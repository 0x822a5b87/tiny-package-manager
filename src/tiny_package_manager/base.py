from semantic_version import Version

PackageName = str
VersionName = str


class PackageVersion(object):
    def __init__(self, name: PackageName, version: Version):
        self.name = name
        self.version = version

    def __str__(self):
        return f"({self.name}:{self.version})"

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

    def compatible(self, dep_package_version: PackageVersion) -> bool:
        if PackageName(dep_package_version.name) not in self.versions:
            return True
        version_list = self.versions[PackageName(dep_package_version.name)]
        for version in version_list:
            if version == dep_package_version.version:
                return True
        return False

    def all_packages(self) -> list[PackageName]:
        return [version for version in self.versions]


class VersionDependencies(object):
    def __init__(self, version_name: VersionName, version_dependencies: dict[VersionName, VersionDependency]):
        self.version_name = version_name
        self.version_dependencies = version_dependencies

    def contain_version(self, version_name: VersionName) -> bool:
        return version_name in self.version_dependencies

    def all_versions(self) -> list[Version]:
        return [Version(version_name) for version_name in self.version_dependencies]

    def update(self, version_name: VersionName, version_dep: VersionDependency):
        self.version_dependencies[version_name] = version_dep

    # def update(self, version_name: VersionName, package_name: PackageName, versions: list[Version]):
    #     if version_name not in self.version_dependencies:
    #         self.version_dependencies[version_name] = VersionDependency({})
    #     self.version_dependencies[version_name].update(package_name, versions)

    def compatible(self, package_version: PackageVersion, dep_package_version: PackageVersion) -> bool:
        if str(package_version.version) not in self.version_dependencies:
            # It means the package doesn't have any dependency
            return True
        v = self.version_dependencies[VersionName(package_version.version)]
        return v.compatible(dep_package_version)


class Dependencies(object):
    def __init__(self, dependencies: dict[PackageName, VersionDependencies]):
        self.dependencies = dependencies
        self.count = 0

    def update(self,
               package_name: PackageName,
               version_name: VersionName,
               version_dependency: VersionDependency):
        """
        update dependencies
        :param package_name: the name of the package
        :param version_name: the version of the package
        :param version_dependency: dependency of the version
        :return:
        """
        if package_name not in self.dependencies:
            self.dependencies[package_name] = VersionDependencies(package_name, {})
        self.dependencies[package_name].update(version_name, version_dependency)

    def inc_count(self) -> int:
        self.count += 1
        return self.count

    def all_versions(self) -> list[Version]:
        return [Version(version_name) for version_name in self.dependencies]

    def contain_package(self, package_name: PackageName) -> bool:
        return package_name in self.dependencies

    def contain_package_version(self, package_version: PackageVersion) -> bool:
        name = package_version.name
        version = VersionName(package_version.version)
        return self.contain_package(name) and self.package_dependencies(name).contain_version(version)

    def package_version_dependencies(self, package_version: PackageVersion) -> VersionDependency:
        dependencies = self.package_dependencies(package_version.name)
        return dependencies.version_dependencies.get(str(package_version.version))

    def package_dependencies(self, package_name: PackageName) -> VersionDependencies:
        assert package_name in self.dependencies
        return self.dependencies[package_name]

    def compatible(self, package_version: PackageVersion, dep_package_version: PackageVersion) -> bool:
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


class Package:
    def __init__(self, name: str):
        self.name = name

    def fetch(self) -> bytes:
        raise NotImplementedError()
