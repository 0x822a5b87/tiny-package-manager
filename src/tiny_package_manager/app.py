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

    def package_versions(self) -> list[PackageVersion]:
        return self.references.package_versions(self.name)

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
        self.abs_path = self._get_abs_path()

    def exist(self) -> bool:
        return os.path.exists(self.abs_path)

    def fetch(self) -> bytes:
        with open(self.abs_path, "rb") as reader:
            return reader.read()

    def store(self, data: bytes):
        with open(self.abs_path, "wb") as writer:
            writer.write(data)

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
