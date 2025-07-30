import unittest

from .app import LocalPackage
from .utils import *


class UtilsTestCase(unittest.TestCase):
    dayjs: LocalPackage = None
    dayjs_spec: LocalPackage = None

    jest: LocalPackage = None
    jest_spec: LocalPackage = None

    @classmethod
    def setUpClass(cls):
        """init stream data"""
        cls.dayjs = LocalPackage("dayjs", "./resources/dayjs-1.11.13.tgz")
        cls.dayjs_spec = LocalPackage("dayjs", "./resources/dayjs-1.11.13.json")

        cls.jest = LocalPackage("jest", "./resources/jest-0.0.71.tgz")
        cls.jest_spec = LocalPackage("jest", "./resources/jest-0.0.71.json")

    def test_read_file_from_tar(self):
        tar = read_file_from_tar(self.dayjs.fetch(), "package", "package.json")
        assert tar == self.dayjs_spec.fetch()

        tar = read_file_from_tar(self.jest.fetch(), "package", "package.json")
        assert tar == self.jest_spec.fetch()

    def test_read_dependencies(self):
        dependencies = read_dependencies("dayjs", self.dayjs.fetch())
        assert len(dependencies) == 0

        dependencies = read_dependencies("jest", self.jest.fetch())
        assert len(dependencies) == 3
        dependencies = sorted(dependencies)
        expected_dependencies = sorted([RemotePackage("express-resource", "", YarnReference()),
                                        RemotePackage("underscore", "", YarnReference()),
                                        RemotePackage("sji", "", YarnReference())])
        assert dependencies == expected_dependencies


    if __name__ == '__main__':
        unittest.main()
