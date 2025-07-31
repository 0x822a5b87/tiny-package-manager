from semantic_version import Version

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

class Package:
    def __init__(self, name: str):
        self.name = name

    def fetch(self) -> bytes:
        raise NotImplementedError()