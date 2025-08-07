import json
import tarfile
from concurrent import futures
from io import BytesIO

import requests

from .app import RemotePackage, LocalPackage
from .reference import PackageName


def read_dependencies(name: str, package_data: bytes) -> list[RemotePackage]:
    tar = read_file_from_tar(package_data, "package", "package.json")
    package_spec = json.loads(tar)
    dependencies = package_spec.get("dependencies", {})
    return [RemotePackage(name, version, None) for name, version in dependencies.items()]


def read_file_from_tar(package_data: bytes, virtual_path: str, file_name: str) -> bytes:
    """
    read data from tarball file with specific name
    """
    # build the full path
    full_path = f"{virtual_path}/{file_name}" if virtual_path else file_name

    with BytesIO(package_data) as file_obj:
        with tarfile.open(fileobj=file_obj, mode="r:*") as tar:
            try:
                tar_info = tar.getmember(full_path)
                with tar.extractfile(tar_info) as f:
                    return f.read()
            except KeyError:
                raise FileNotFoundError(f"File '{file_name}' not found in archive")


def fetch_url(url: str) -> bytes:
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"error fetching package info {url}")
    return response.content


def download(dependency_names: set[PackageName]) -> dict[str, bytes]:
    def remote_url(name: str) -> str:
        return f"https://registry.yarnpkg.com/{name}"

    with futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {
            executor.submit(fetch_url, remote_url(dependency_name)): dependency_name
            for dependency_name in dependency_names
        }

        dataset: dict[str, bytes] = {}
        for future in futures.as_completed(future_to_url):
            package_name = future_to_url[future]
            data = future.result()
            dataset[package_name] = data
        return dataset


def format_name(name: str) -> str:
    name = name.replace("@", "at_")
    name = name.replace("/", "_")
    return name


def download_with_cache(dependency_names: set[PackageName]) -> dict[str, bytes]:
    dataset: dict[str, bytes] = {}
    uncached_dep: set[PackageName] = set()
    for dependency_name in dependency_names:
        local = LocalPackage(dependency_name, f"../resources/{format_name(dependency_name)}")
        if local.exist():
            dataset[dependency_name] = local.fetch()
        else:
            uncached_dep.add(dependency_name)
    uncached_dataset = download(uncached_dep)
    dataset.update(uncached_dataset)
    for dependency_name in uncached_dataset:
        data = dataset[dependency_name]
        local = LocalPackage(dependency_name, f"../resources/{format_name(dependency_name)}")
        local.store(data)

    return dataset


def parse_all_dependency_name(metadata: dict) -> set[PackageName]:
    """
    parse all dependency names for a package in order to request in parallel
    :return:
    """
    package_names: set[PackageName] = set()
    versions: dict = metadata["versions"]
    for version_name, version_metadata in versions.items():
        if "dependencies" not in version_metadata:
            continue
        dependencies: dict = version_metadata["dependencies"]
        for dependency_name in dependencies:
            package_names.add(PackageName(dependency_name))
    return package_names
