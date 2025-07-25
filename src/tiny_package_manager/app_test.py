import unittest

from semver_range import Version

from .app import LocalPackage, RemotePackage

RELATIVE_DATA = '''Hello!
I'm a relative package.'''


class ManagerTestCase(unittest.TestCase):
    @staticmethod
    def test_local_package_1():
        local = LocalPackage("local", "./relative_package")
        assert local.fetch() == RELATIVE_DATA.encode()

    @staticmethod
    def test_local_package_2():
        local = LocalPackage("local", "../tiny-package-manager/relative_package")
        assert local.fetch() == RELATIVE_DATA.encode()

    @staticmethod
    def test_remote_package_1():
        remote = RemotePackage("dayjs", "1.11.13")
        local = LocalPackage("dayjs", "./dayjs-1.11.13.tgz")
        assert remote.fetch() == local.fetch()

    @staticmethod
    def test_remote_package_get_pinned_reference():
        remote = RemotePackage("dayjs", "1.11.0")
        v = Version("1.11.0")
        assert remote._get_pinned_reference() == Version("1.11.0")

        remote = RemotePackage("dayjs", ">=1.11.0")
        assert remote._get_pinned_reference() == Version("1.11.13")

        remote = RemotePackage("dayjs", ">=1.11.0 <1.11.15")
        assert remote._get_pinned_reference() == Version("1.11.13")

        remote = RemotePackage("dayjs", ">=1.11.14")
        assert remote._get_pinned_reference() is None

        remote = RemotePackage("dayjs", ">=1.11.8 <1.11.12")
        assert remote._get_pinned_reference() == Version("1.11.11")


if __name__ == '__main__':
    unittest.main()
