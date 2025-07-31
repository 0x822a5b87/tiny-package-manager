import unittest

from .app import LocalPackage
from .reference import YarnReference
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

    def test_parse_all_dependency_name(self):
        reference = YarnReference()
        metadata = reference.get_metadata("jest")
        dependency_names = parse_all_dependency_name(metadata)
        self.assertEqual(dependency_names,
                         {'sji', 'api-easy', 'mongoose', 'jest-cli', 'express', 'import-local', '@jest/types',
                          '@jest/core', 'underscore', 'express-resource'})

    def test_download(self):
        reference = YarnReference()
        metadata = reference.get_metadata("jest")
        dependency_names = parse_all_dependency_name(metadata)
        dataset = download(dependency_names)
        self.assertEqual(len(dataset), len(dependency_names))

    def test_read_file_from_tar(self):
        tar = read_file_from_tar(self.dayjs.fetch(), "package", "package.json")
        self.assertEqual(tar, self.dayjs_spec.fetch())

        tar = read_file_from_tar(self.jest.fetch(), "package", "package.json")
        self.assertEqual(tar, self.jest_spec.fetch())

    def test_read_dependencies(self):
        dependencies = read_dependencies("dayjs", self.dayjs.fetch())
        self.assertEqual(len(dependencies), 0)

        dependencies = read_dependencies("jest", self.jest.fetch())
        self.assertEqual(len(dependencies), 3)
        dependencies = sorted(dependencies)
        expected_dependencies = sorted([RemotePackage("express-resource", "", YarnReference()),
                                        RemotePackage("underscore", "", YarnReference()),
                                        RemotePackage("sji", "", YarnReference())])
        self.assertEqual(dependencies, expected_dependencies)

    if __name__ == '__main__':
        unittest.main()
