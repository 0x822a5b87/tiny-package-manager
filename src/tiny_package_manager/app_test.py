import unittest

from semantic_version import Version

from .utils import get_pinned_reference
from .reference import YarnReference
from .app import LocalPackage, RemotePackage

RELATIVE_DATA = '''Hello!
I'm a relative package.'''


class ManagerTestCase(unittest.TestCase):
    @staticmethod
    def test_local_package_1():
        local = LocalPackage("local", "./resources/relative_package")
        assert local.fetch() == RELATIVE_DATA.encode()

    @staticmethod
    def test_local_package_2():
        local = LocalPackage("local", "../tiny-package-manager/resources/relative_package")
        assert local.fetch() == RELATIVE_DATA.encode()

    @staticmethod
    def test_remote_package_1():
        remote = RemotePackage("dayjs", "1.11.13", YarnReference())
        local = LocalPackage("dayjs", "./resources/dayjs-1.11.13.tgz")
        assert remote.fetch() == local.fetch()

    @staticmethod
    def test_remote_package_get_pinned_reference():
        remote = RemotePackage("dayjs", "1.11.0", YarnReference())
        versions = remote.package_versions()
        assert get_pinned_reference(versions, remote.sem_version) == Version("1.11.0")

        remote = RemotePackage("dayjs", ">=1.11.0", YarnReference())
        versions = remote.package_versions()
        assert get_pinned_reference(versions, remote.sem_version) == Version("1.11.13")

        remote = RemotePackage("dayjs", ">=1.11.0 <1.11.15", YarnReference())
        versions = remote.package_versions()
        assert get_pinned_reference(versions, remote.sem_version) == Version("1.11.13")

        remote = RemotePackage("dayjs", ">=1.11.14", YarnReference())
        versions = remote.package_versions()
        assert get_pinned_reference(versions, remote.sem_version) is None

        remote = RemotePackage("dayjs", ">=1.11.8 <1.11.12", YarnReference())
        versions = remote.package_versions()
        assert get_pinned_reference(versions, remote.sem_version) == Version("1.11.11")


if __name__ == '__main__':
    unittest.main()
