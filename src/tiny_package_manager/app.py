import json
import os

import requests
import semver
from semver_range import Version, Range


class Package:
    def __init__(self, name: str):
        self.name = name

    def fetch(self) -> bytes:
        raise NotImplementedError()


class RemotePackage(Package):
    def __init__(self, name: str, sem_version_str: str):
        super().__init__(name)
        if Range(sem_version_str):
            self.sem_version = Range(sem_version_str)
        else:
            raise ValueError(f"Invalid semver version: {sem_version_str}")

    def fetch(self) -> bytes:
        return self._http_fetch()

    def _get_pinned_reference(self) -> Version:
        url = f"https://registry.yarnpkg.com/{self.name}"
        response = requests.get(url)
        if response.status_code != 200:
            raise ValueError(f"error fetching package info {url}")
        package_info = json.loads(response.content)
        versions:dict = package_info["versions"]
        max_satisfying_ver = None
        for version in versions:
            max_satisfying_ver = self._max_satisfying_ver(Version(version), max_satisfying_ver)
        return max_satisfying_ver

    def _max_satisfying_ver(self, version:Version, max_satisfying_ver:Version) -> Version:
        if version not in self.sem_version:
            return max_satisfying_ver

        if max_satisfying_ver is None:
            return version

        if version > max_satisfying_ver:
            return version
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
