import unittest
from pathlib import Path

from parsing.parse import parse


class parseInstance(unittest.TestCase):
    def test_parse_instance(self):
        instance_path = Path("instances/V100_NBA.json")

        scheduler = parse(instance_path, True)

        self.assertIsNotNone(scheduler)


if __name__ == "__main__":
    unittest.main()
