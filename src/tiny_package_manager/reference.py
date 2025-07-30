import json

import requests
from semantic_version import Version

PackageName = str
VersionName = str


class VersionDependency(object):
    def __init__(self, versions: dict[PackageName, list[Version]]):
        self.versions = versions


class VersionDependencies(object):
    def __init__(self, version_dependencies: dict[VersionName, VersionDependency]):
        self.version_dependencies = version_dependencies

    def all_versions(self) -> list[Version]:
        return [Version(version_name) for version_name in self.version_dependencies]


class Dependencies(object):
    def __init__(self, dependencies: dict[PackageName, VersionDependencies]):
        self.dependencies = dependencies

    def all_versions(self) -> list[Version]:
        return [Version(version_name) for version_name in self.dependencies]


class Reference(object):
    def versions(self, name: str) -> list[Version]:
        """
        retrieve versions of packages named `name`
        """
        raise NotImplementedError()

    def dependencies(self, name: str, version: Version) -> Dependencies:
        raise NotImplementedError()


class JsonReference(Reference):
    def __init__(self, conf: str):
        self.all_dependencies: dict[PackageName, VersionDependencies] = {}
        package_dependencies = json.loads(conf)
        for package_name in package_dependencies:
            package_version_dependencies: dict[VersionName, VersionDependency] = {}
            # jest
            package_info = package_dependencies[package_name]
            for package_version in package_info:
                sub_version_dependencies: dict[VersionName, list[Version]] = {}
                # 0.0.1
                version_dependencies = package_info[package_version]
                if version_dependencies:
                    for version_dependency_name in version_dependencies:
                        # express
                        version_single_dependency = version_dependencies[version_dependency_name]
                        version_single_dependencies: list[Version] = []
                        for v in version_single_dependency:
                            # ["0.0.1", "0.0.2"]
                            version_single_dependencies.append(Version(v))
                        sub_version_dependencies[version_dependency_name] = version_single_dependencies
                    package_version_dependencies[package_version] = VersionDependency(sub_version_dependencies)
                else:
                    sub_version_dependencies[package_version] = None
                    package_version_dependencies[package_version] = VersionDependency(sub_version_dependencies)

            dependencies = VersionDependencies(package_version_dependencies)
            self.all_dependencies[package_name] = dependencies

    """
    THIS IS ONLY USED FOR SIMPLIFYING TESTS
    """

    def versions(self, name: PackageName) -> list[Version]:
        if name in self.all_dependencies:
            return self.all_dependencies[name].all_versions()
        else:
            raise ValueError(f"no package info for {name}")


class YarnReference(Reference):
    def versions(self, name: str) -> list[Version]:
        url = f"https://registry.yarnpkg.com/{name}"
        response = requests.get(url)
        if response.status_code != 200:
            raise ValueError(f"error fetching package info {url}")
        package_info = json.loads(response.content)
        versions: dict = package_info["versions"]
        return [Version(version) for version in versions]
