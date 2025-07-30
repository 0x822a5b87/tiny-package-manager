import json
import tarfile
from io import BytesIO

from .app import RemotePackage
from .reference import YarnReference


def read_dependencies(name: str, package_data: bytes) -> list[RemotePackage]:
    tar = read_file_from_tar(package_data, "package", "package.json")
    package_spec = json.loads(tar)
    dependencies = package_spec.get("dependencies", {})
    return [RemotePackage(name, version, YarnReference()) for name, version in dependencies.items()]


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
