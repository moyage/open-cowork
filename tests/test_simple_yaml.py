from __future__ import annotations

import unittest

import test_support  # noqa: F401

from governance.simple_yaml import dump_yaml, loads_yaml


class SimpleYamlTests(unittest.TestCase):
    def test_multiline_strings_round_trip_inside_list_mappings(self):
        payload = {
            "commands": [
                {
                    "command": "python3 -m unittest",
                    "stderr": ".....\n----------------------------------------------------------------------\nRan 213 tests\n\nOK",
                }
            ]
        }

        dumped = dump_yaml(payload)
        loaded = loads_yaml(dumped)

        self.assertIn("stderr: |-", dumped)
        self.assertEqual(loaded, payload)


if __name__ == "__main__":
    unittest.main()
