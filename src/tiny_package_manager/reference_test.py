import unittest

from semantic_version import Version

from .reference import JsonReference


class ReferenceTestCases(unittest.TestCase):
    @staticmethod
    def test_json_reference():
        reference = JsonReference("""
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
        """)

        versions = reference.versions("jest")
        expected_versions = [Version("0.0.1"), Version("0.0.2"), Version("1.0.1"), Version("1.1.1")]
        assert sorted(versions) == sorted(expected_versions)


if __name__ == '__main__':
    unittest.main()
