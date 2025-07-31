import unittest

from semantic_version import Version, NpmSpec

from .reference import JsonReference, PackageVersion, YarnReference


class ReferenceTestCases(unittest.TestCase):
    def test_json_reference(self):
        reference = JsonReference(JSON_REFERENCE)
        versions = reference.package_versions("jest")
        expected_versions = [PackageVersion("jest", Version("0.0.1")),
                             PackageVersion("jest", Version("0.0.2")),
                             PackageVersion("jest", Version("1.0.1")),
                             PackageVersion("jest", Version("1.1.1"))]
        self.assertEqual(sorted(versions), sorted(expected_versions))

    def test_yarn_reference(self):
        direct_dependencies = {
            "express": NpmSpec(""),
            "mongoose": NpmSpec(""),
            "api-easy": NpmSpec(""),
        }
        reference = YarnReference(direct_dependencies)
        self.assertTrue(True)

    def test_update_dependencies(self):
        direct_dependencies = {
            "api-easy": NpmSpec("")
        }
        reference = YarnReference(direct_dependencies)
        reference._update_metadata("api-easy")
        self.assertTrue(reference._compatible(PackageVersion("api-easy", Version("0.2.3")),
                                              PackageVersion("request", Version("1.9.0"))))

        self.assertFalse(reference._compatible(PackageVersion("api-easy", Version("0.2.3")),
                                              PackageVersion("request", Version("1.8.9"))))

        reference._update_metadata("jest")
        reference._update_metadata("express")

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
