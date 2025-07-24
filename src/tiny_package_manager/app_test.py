import unittest

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


if __name__ == '__main__':
    unittest.main()
