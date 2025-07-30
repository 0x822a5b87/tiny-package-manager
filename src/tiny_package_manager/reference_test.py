import unittest

from semantic_version import Version, NpmSpec

from .reference import JsonReference, PackageVersion, YarnReference


class ReferenceTestCases(unittest.TestCase):
    @staticmethod
    def test_json_reference():
        reference = JsonReference(JSON_REFERENCE)
        versions = reference.package_versions("jest")
        expected_versions = [PackageVersion("jest", Version("0.0.1")),
                             PackageVersion("jest", Version("0.0.2")),
                             PackageVersion("jest", Version("1.0.1")),
                             PackageVersion("jest", Version("1.1.1"))]
        assert sorted(versions) == sorted(expected_versions)

    @staticmethod
    def test_yarn_reference():
        direct_dependencies = {
            "express": NpmSpec(""),
            "mongoose": NpmSpec(""),
            "api-easy": NpmSpec(""),
        }
        reference = YarnReference(direct_dependencies)
        data = reference.compile()

    @staticmethod
    def test_update_dependencies():
        direct_dependencies = {
            "api-easy": NpmSpec("")
        }
        reference = YarnReference(direct_dependencies)
        reference._update_metadata("api-easy")


JSON_REFERENCE = """
{
	"jest": {
		"0.0.1": {
			"express": ["0.0.1"]
		},
		"0.0.2": {
			"express": ["0.0.1", "0.0.2"]
		},
		"1.0.1": {
			"express": ["0.0.1", "0.0.2"]
		},
		"1.1.1": {
			"express": ["0.0.2"],
			"babel": ["1.0.0", "1.0.1"]
		}
	},
	"express": {
		"0.0.1": {},
		"0.0.2": {}
	}
}
"""

COMPILE_REFERENCE = """
{
  "jest": {
    "0.0.3": {"express": ["0.0.3", "0.0.2"], "babel": ["0.0.2"]},
    "0.0.2": {"express": ["0.0.2"],      "babel": ["0.0.2", "0.0.1"]},
    "0.0.1": {"express": ["0.0.1"]}
  },
  "express": {
    "0.0.3": {"babel": ["0.0.2"]},
    "0.0.2": {"babel": ["0.0.1"]},
    "0.0.1": {"babel": ["0.0.1"]}
  },
  "babel": {
    "0.0.2": [],
    "0.0.1": []
  }
}
"""

if __name__ == '__main__':
    unittest.main()
