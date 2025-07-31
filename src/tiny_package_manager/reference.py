import json

import requests
from semantic_version import NpmSpec

from .base import *
from .utils import download


def format_npm(npm_version: str) -> str:
    version = npm_version.strip()

    version = version.replace(">= ", ">=").replace("<= ", "<=")
    version = version.replace("> ", ">").replace("< ", "<")
    version = version.replace("= ", "=")
    version = version.replace("^ ", "^")

    return version

class JsonReference(Reference):
    """
    THIS IS ONLY USED FOR SIMPLIFYING TESTS
    """

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

    def package_versions(self, name: PackageName) -> list[PackageVersion]:
        if name in self.all_dependencies:
            return [PackageVersion(name, version)
                    for version in self.all_dependencies[name].all_versions()]
        else:
            raise ValueError(f"no package info for {name}")


class YarnReference(Reference):
    def __init__(self, direct_dependencies: dict[PackageName, NpmSpec] = None):
        self.package_version_cache: dict[PackageName, dict] = {}
        if direct_dependencies is None:
            direct_dependencies = {}
        self.direct_dependencies = direct_dependencies
        self.manifest = Dependencies({})

    def package_versions(self, name: str) -> list[PackageVersion]:
        package_info = self.get_metadata(name)
        versions: dict = package_info["versions"]
        return [PackageVersion(name, Version(version)) for version in versions]

    def compile(self):
        # for package_name, npm_spec in self.direct_dependencies.items():
        #     package_versions = self.package_versions(package_name)
        #     for package_version in package_versions:
        #         if package_version.version in npm_spec:
        #             pass
        #
        #     package_versions = [package_version.version
        #                         for package_version
        #                         in self.package_versions(package_name)
        #                         if package_version.version in npm_spec]
        #
        # return package_versions
        for package_name, npm_spec in self.direct_dependencies.items():
            metadata = self.get_metadata(package_name)
            versions: dict = metadata["versions"]
            for version_name, version_metadata in versions.items():
                dependencies: dict = version_metadata["dependencies"]
                for dependency_name, dependency_npm_version in dependencies.items():
                    pass

    def _compile(self,
                 solution: list[list[PackageVersion]],
                 selected: list[PackageVersion],
                 unresolved: list[PackageVersion]):
        if solution:
            return solution

        if not unresolved:
            # we find a solution.
            solution.append(selected)
        else:
            head, tail = unresolved[0], unresolved[1:]
            # Check if the head satisfies the constraint
            # TODO check error
            if self._compatible(head):
                candidate = selected + [head]
                self._compile(solution, candidate, unresolved)

    def _compatible(self, current: PackageVersion, dep: PackageVersion) -> bool:
        if not self.manifest.contains(current):
            try:
                self._update_metadata(current.name)
            except Exception:
                print(f"failed to update metadata for {current}")
        return self.manifest.compatible(current, dep)

    def _update_metadata(self, package_name: PackageName):
        metadata = self.get_metadata(package_name)
        self._init_new_dependencies(metadata)
        versions: dict = metadata["versions"]
        for version_name, version_metadata in versions.items():
            if "dependencies" not in version_metadata:
                continue
            dependencies: dict = version_metadata["dependencies"]
            for dependency_name, npm_version_str in dependencies.items():
                npm_version = NpmSpec(format_npm(npm_version_str))
                dependency_versions = self.package_versions(dependency_name)
                compatible_versions = [dependency_version.version
                                       for dependency_version in dependency_versions
                                       if dependency_version.version in npm_version]
                self.manifest.update(package_name, version_name, dependency_name, compatible_versions)

    def _init_new_dependencies(self, metadata: dict):
        from .utils import parse_all_dependency_name
        all_dependency_name = parse_all_dependency_name(metadata)
        new_dependencies = [dependency_name
                            for dependency_name in all_dependency_name
                            if dependency_name not in self.package_version_cache]
        dataset = download(set(new_dependencies))
        for package_name, package_data in dataset.items():
            self.package_version_cache[package_name] = json.loads(package_data)

    def _parse_versions(self):
        pass

    def _parse_dependencies(self):
        pass

    def get_metadata(self, name: PackageName) -> dict:
        if name not in self.package_version_cache:
            url = f"https://registry.yarnpkg.com/{name}"
            response = requests.get(url)
            if response.status_code != 200:
                raise ValueError(f"error fetching package info {url}")
            package_info = json.loads(response.content)
            self.package_version_cache[name] = package_info
        else:
            package_info = self.package_version_cache[name]
        return package_info
