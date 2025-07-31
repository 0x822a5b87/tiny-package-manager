import os

import requests
from semantic_version import Version, NpmSpec

from .base import Package, Reference, PackageVersion


class RemotePackage(Package):
    def __init__(self, name: str, sem_version_str: str, reference: Reference):
        super().__init__(name)
        self.sem_version = NpmSpec(sem_version_str)
        self.references = reference

    def __eq__(self, __value):
        return (str(self.sem_version) == str(__value.sem_version)
                and self.name == __value.name)

    def __hash__(self):
        return hash(self.name + str(self.sem_version))

    def __lt__(self, other):
        if self.name != other.name:
            return self.name < other.name
        return self.sem_version < other.sem_version

    def fetch(self) -> bytes:
        return self._http_fetch()

    def _get_pinned_reference(self) -> Version:
        versions  = self.references.package_versions(self.name)
        max_satisfying_ver = None
        for version in versions:
            max_satisfying_ver = self._max_satisfying_ver(version, max_satisfying_ver)
        return max_satisfying_ver

    def _max_satisfying_ver(self, package_version: PackageVersion, max_satisfying_ver: Version) -> Version:
        if package_version.version not in self.sem_version:
            return max_satisfying_ver

        if max_satisfying_ver is None:
            return package_version.version

        if package_version.version > max_satisfying_ver:
            return package_version.version
        else:
            return max_satisfying_ver

    def _http_fetch(self):
        url = f"https://registry.yarnpkg.com/{self.name}/-/{self.name}-{str(self.sem_version)}.tgz"
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            raise ValueError(f"error fetching {url}")


class LocalPackage(Package):
    def __init__(self, name: str, path: str):
        super().__init__(name)
        self.path = path

    def fetch(self) -> bytes:
        with open(self._get_abs_path(), "rb") as reader:
            return reader.read()

    def _get_abs_path(self):
        return os.path.abspath(self.path)


# async download file
async def fetch_package(package: Package) -> bytes:
    if isinstance(package, LocalPackage):
        return package.fetch()
    elif isinstance(package, RemotePackage):
        return package.fetch()
    else:
        raise TypeError(f"Unsupported package type: {type(package)}")


if __name__ == '__main__':
    print("Hello from tiny-package-manager!")
