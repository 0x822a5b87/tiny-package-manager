import json

import requests
from semantic_version import Version, NpmSpec

PackageName = str
VersionName = str


class PackageVersion(object):
    def __init__(self, name: PackageName, version: Version):
        self.name = name
        self.version = version

    def __eq__(self, __value):
        if not isinstance(__value, PackageVersion):
            return False

        return self.name.__eq__(__value.name)

    def __lt__(self, other):
        if not isinstance(other, PackageVersion):
            return NotImplemented(f"Cannot compare {type(self)} to {type(other)}")

        return self.name.__lt__(other.name)


class VersionDependency(object):
    def __init__(self, versions: dict[PackageName, list[Version]]):
        self.versions = versions

    def update(self, package_name: PackageName, versions: list[Version]):
        if package_name not in self.versions:
            self.versions[package_name] = []
        self.versions[package_name] = versions

    def compatible(self, dep_package_version:PackageVersion) -> bool:
        if PackageName(dep_package_version.name) not in self.versions:
            raise ValueError(f"Dependency constraint {dep_package_version} is not found")
        version_list = self.versions[PackageName(dep_package_version.name)]
        for version in version_list:
            if version == dep_package_version.version:
                return True
        return False


class VersionDependencies(object):
    def __init__(self, version_dependencies: dict[VersionName, VersionDependency]):
        self.version_dependencies = version_dependencies

    def all_versions(self) -> list[Version]:
        return [Version(version_name) for version_name in self.version_dependencies]

    def update(self, version_name: VersionName, package_name:PackageName, versions: list[Version]):
        if version_name not in self.version_dependencies:
            self.version_dependencies[version_name] = VersionDependency({})
        self.version_dependencies[version_name].update(package_name, versions)

    def compatible(self, package_version: PackageVersion, dep_package_version:PackageVersion) -> bool:
        if str(package_version.version) not in self.version_dependencies:
            raise ValueError(f"Dependency version {package_version} is not found")
        v = self.version_dependencies[VersionName(package_version.version)]
        return v.compatible(dep_package_version)


class Dependencies(object):
    def __init__(self, dependencies: dict[PackageName, VersionDependencies]):
        self.dependencies = dependencies

    def update(self,
               package_name: PackageName,
               version_name: VersionName,
               dep_package_name: PackageName,
               versions: list[Version]):
        """
        update dependencies
        :param package_name: the name of the package
        :param version_name: the version of the package
        :param dep_package_name: the name of the dependency package
        :param versions: all versions of the dependency package
        :return:
        """
        if package_name not in self.dependencies:
            self.dependencies[package_name] = VersionDependencies({})
        self.dependencies[package_name].update(version_name, dep_package_name, versions)

    def all_versions(self) -> list[Version]:
        return [Version(version_name) for version_name in self.dependencies]

    def contains(self, package_version: PackageVersion) -> bool:
        return package_version.name in self.dependencies

    def compatible(self, package_version: PackageVersion, dep_package_version:PackageVersion) -> bool:
        if package_version.name not in self.dependencies:
            raise ValueError(f"Dependency package {package_version} is not found")
        version_dependencies = self.dependencies[package_version.name]
        return version_dependencies.compatible(package_version, dep_package_version)


class Reference(object):
    def package_versions(self, name: str) -> list[PackageVersion]:
        """
        retrieve versions of packages named `name`
        """
        raise NotImplementedError()

    def dependencies(self, name: str, version: Version) -> Dependencies:
        raise NotImplementedError()


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
        versions: dict = metadata["versions"]
        for version_name, version_metadata in versions.items():
            if "dependencies" not in version_metadata:
                continue
            dependencies: dict = version_metadata["dependencies"]
            for dependency_name, npm_version_str in dependencies.items():
                npm_version = NpmSpec(self.format_npm(npm_version_str))
                dependency_versions = self.package_versions(dependency_name)
                compatible_versions = [dependency_version.version
                                       for dependency_version in dependency_versions
                                       if dependency_version.version in npm_version]
                self.manifest.update(package_name, version_name, dependency_name, compatible_versions)

    def format_npm(self, npm_version: str) -> str:
        version = npm_version.strip()

        version = version.replace(">= ", ">=").replace("<= ", "<=")
        version = version.replace("> ", ">").replace("< ", "<")
        version = version.replace("= ", "=")
        version = version.replace("^ ", "^")

        return version

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
