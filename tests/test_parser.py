import unittest

from canitf_project.parser import extract_candidates_from_release, merge_candidates


BODY = """
## New Features

* Added support for provider iteration with `for_each`. (#123)
* New backend configuration using locals and variables.

## Bug Fixes

* Fixed a panic when doing something unrelated.
"""


class ParserTests(unittest.TestCase):
    def test_extracts_feature_bullets_but_not_bugfixes(self):
        rows = extract_candidates_from_release("opentofu", "v1.9.0", "https://example.test/release", BODY)
        titles = [r.title for r in rows]
        self.assertEqual(len(rows), 2)
        self.assertIn("Added support for provider iteration with for_each", titles)
        self.assertNotIn("Fixed a panic when doing something unrelated", titles)

    def test_merge_combines_tools_on_same_key(self):
        a = extract_candidates_from_release("opentofu", "v1.9.0", "https://example.test/tofu", "## Features\n* Provider iteration with for_each")
        b = extract_candidates_from_release("terraform", "v1.15.0", "https://example.test/tf", "## Features\n* Provider iteration with for_each")
        rows = merge_candidates(a + b)
        self.assertEqual(len(rows), 1)
        self.assertIn("opentofu", rows[0].tools)
        self.assertIn("terraform", rows[0].tools)


if __name__ == "__main__":
    unittest.main()
