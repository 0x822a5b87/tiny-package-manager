import copy
import json
from typing import Optional

import requests
from semantic_version import NpmSpec

from .base import *
from .utils import download_with_cache


def format_npm(npm_version: str) -> str:
    version = npm_version.strip()

    version = version.replace(">= ", ">=").replace("<= ", "<=")
    version = version.replace("> ", ">").replace("< ", "<")
    version = version.replace("= ", "=")
    version = version.replace("^ ", "^")

    return version


class UnresolvedDependency(object):
    def __init__(self, package_name: PackageName, versions: list[Version]):
        self.package_name = package_name
        self.versions = versions

    def merge(self, another: 'UnresolvedDependency'):
        if not isinstance(another, UnresolvedDependency):
            raise TypeError(f"{another} is not of type UnresolvedDependency")
        union_set = set(self.versions) | set(another.versions)
        union_list = list(union_set)
        self.versions = sorted(union_list)

    def __deepcopy__(self, memo):
        new_package_name = copy.deepcopy(self.package_name, memo)
        new_versions = copy.deepcopy(self.versions, memo)
        return UnresolvedDependency(new_package_name, new_versions)


class UnresolvedDependencies(object):
    def __init__(self, direct_dependencies: list[UnresolvedDependency]):
        self.unresolved_dependencies = direct_dependencies

    def deep_copy(self) -> 'UnresolvedDependencies':
        copied_deps = copy.deepcopy(self.unresolved_dependencies)
        return UnresolvedDependencies(copied_deps)

    def index(self, unresolved_dependency: UnresolvedDependency) -> int:
        if not isinstance(unresolved_dependency, UnresolvedDependency):
            return False
        for idx, ud in enumerate(self.unresolved_dependencies):
            if ud.package_name == unresolved_dependency.package_name:
                return idx
        return -1

    def add_unresolved_dependencies(self, indirect_dependencies: list[UnresolvedDependency]):
        new_unresolved_dependencies: list[UnresolvedDependency] = []
        for indirect_dependency in indirect_dependencies:
            idx = self.index(indirect_dependency)
            if idx < 0:
                new_unresolved_dependencies.append(indirect_dependency)
                continue
            self.unresolved_dependencies[idx].merge(indirect_dependency)
        self.unresolved_dependencies.extend(new_unresolved_dependencies)


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

            dependencies = VersionDependencies(package_name, package_version_dependencies)
            self.all_dependencies[package_name] = dependencies

    def package_versions(self, name: PackageName) -> list[PackageVersion]:
        if name in self.all_dependencies:
            return [PackageVersion(name, version)
                    for version in self.all_dependencies[name].all_versions()]
        else:
            raise ValueError(f"no package info for {name}")


class YarnReference(Reference):
    def __init__(self, debug: bool = False):
        self.package_version_cache: dict[PackageName, dict] = {}
        self.direct_dependencies: dict[str, str] = {}
        self.manifest = Dependencies({})
        self.debug = debug

    def package_versions(self, name: str) -> list[PackageVersion]:
        package_info = self.get_metadata(name)
        if "versions" not in package_info:
            return []
        versions: dict = package_info["versions"]
        return [PackageVersion(name, Version(version)) for version in versions]

    def compile(self) -> Optional[list[PackageVersion]]:
        """
        """
        solution: list[list[PackageVersion]] = []
        selected: list[PackageVersion] = []
        ud: list[UnresolvedDependency] = []
        for package_name, spec in self.direct_dependencies.items():
            npm_spec = NpmSpec(format_npm(spec))
            self._update_metadata(package_name, npm_spec)
            package_versions = self.package_versions(package_name)
            versions = [pv.version for pv in package_versions if pv.version in npm_spec]
            dependency = UnresolvedDependency(package_name, versions)
            ud.append(dependency)
        unresolved_dependencies: UnresolvedDependencies = UnresolvedDependencies(ud)
        self._do_compile(solution, selected, unresolved_dependencies)
        if solution:
            return solution[0]
        else:
            return None
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
        # for package_name, npm_spec in self.direct_dependencies.items():
        #     metadata = self.get_metadata(package_name)
        #     versions: dict = metadata["versions"]
        #     for version_name, version_metadata in versions.items():
        #         dependencies: dict = version_metadata["dependencies"]
        #         for dependency_name, dependency_npm_version in dependencies.items():
        #             pass

    def _do_compile(self,
                    solution: list[list[PackageVersion]],
                    selected: list[PackageVersion],
                    unresolved_package: UnresolvedDependencies) -> list[list[PackageVersion]]:
        if solution:
            return solution

        if not unresolved_package.unresolved_dependencies:
            # we find a solution.
            solution.append(selected)
        else:
            # head is current candidate, tail is the next unresolved collection.
            head, tail = unresolved_package.unresolved_dependencies[0], unresolved_package.unresolved_dependencies[1:]
            head_package = head.package_name
            if not self.manifest.contain_package(head_package):
                self._update_metadata(head_package)
            for head_version in head.versions:
                # package_version_dependencies = self.manifest.package_dependencies(head_package)
                # for version_name, version_dependency in package_version_dependencies.version_dependencies.items():
                chosen_one = PackageVersion(head_package, head_version)
                if self._compatible(selected, chosen_one):
                    selected_new = selected + [chosen_one]
                    indirect_dep = self._choose_new(chosen_one)
                    unresolved_new = self._copy_and_update_unresolved(indirect_dep, UnresolvedDependencies(tail))
                    self._do_compile(solution, selected_new, unresolved_new)
        return []

    def _choose_new(self, chosen_one: PackageVersion) -> VersionDependency:
        if not self.manifest.contain_package_version(chosen_one):
            version_name = format_npm(str(chosen_one.version))
            self._update_metadata(chosen_one.name, NpmSpec(version_name))
        return self.manifest.package_version_dependencies(chosen_one)

    def _copy_and_update_unresolved(self,
                                    indirect_dep: VersionDependency,
                                    unresolved: UnresolvedDependencies) -> UnresolvedDependencies:
        unresolved_new = unresolved.deep_copy()
        if indirect_dep is None:
            # it means the package doesn't have any indirect dependency.
            return unresolved_new
        unresolved_indirect_deps: list[UnresolvedDependency] = []
        for version, deps in indirect_dep.versions.items():
            unresolved_indirect_deps.append(UnresolvedDependency(version, deps))
        unresolved_new.add_unresolved_dependencies(unresolved_indirect_deps)
        return unresolved_new

    def _compatible(self, selected: list[PackageVersion], dep: PackageVersion) -> bool:
        for current in selected:
            if not self._single_compatible(current, dep):
                return False
        return True

    def _single_compatible(self, current: PackageVersion, dep: PackageVersion) -> bool:
        if not self.manifest.contain_package(current.name):
            try:
                self._update_metadata(current.name)
            except Exception:
                print(f"failed to update metadata for {current}")
        return self.manifest.compatible(current, dep)

    def _update_metadata(self, package_name: PackageName,
                         npm_spec: NpmSpec = NpmSpec("")) -> None:
        metadata = self.get_metadata(package_name)
        self._init_new_dependencies(metadata)
        versions: dict = metadata["versions"]
        for version_name, version_metadata in versions.items():
            if self.manifest.contain_package_version(PackageVersion(package_name, version_name)):
                print(f"skipping {version_name}")
                continue
            if Version(version_name) not in npm_spec:
                continue

            if self._is_empty_dependency(version_metadata):
                self.manifest.update(package_name, version_name, VersionDependency({}))
            else:
                dependencies: dict = version_metadata["dependencies"]
                version_dependency: VersionDependency = VersionDependency({})
                for dependency_name, npm_version_str in dependencies.items():
                    if self.debug:
                        print(f"updated metadata for ({dependency_name}-{npm_version_str}) for ({package_name}), count = {self.manifest.inc_count()}")
                    npm_version = NpmSpec(format_npm(npm_version_str))
                    dependency_versions = self.package_versions(dependency_name)
                    compatible_versions = [dependency_version.version
                                           for dependency_version in dependency_versions
                                           if dependency_version.version in npm_version]
                    if not self.manifest.contain_package(dependency_name):
                        version_dependency.update(dependency_name, compatible_versions)
                self.manifest.update(package_name, version_name, version_dependency)

    def _is_empty_dependency(self, version_metadata) -> bool:
        assert isinstance(version_metadata, dict)
        if "dependencies" not in version_metadata:
            return True
        dependencies: dict = version_metadata["dependencies"]
        return not dependencies

    def _init_new_dependencies(self, metadata: dict):
        from .utils import parse_all_dependency_name
        all_dependency_name = parse_all_dependency_name(metadata)
        new_dependencies = [dependency_name
                            for dependency_name in all_dependency_name
                            if dependency_name not in self.package_version_cache]
        dataset = download_with_cache(set(new_dependencies))
        for package_name, package_data in dataset.items():
            self.package_version_cache[package_name] = json.loads(package_data)

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
