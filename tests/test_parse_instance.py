import unittest
from pathlib import Path

from src.parse import parse_instance


class parseInstance(unittest.TestCase):
    def test_parse_instance(self):
        instance_path = Path("problem_instances/problem_data_o5_s1.json")
        model = parse_instance(instance_path)
        self.assertIsNotNone(model)

    def test_solve_instance(self):
        instance_path = Path("problem_instances/problem_data_o5_s1.json")
        model = parse_instance(instance_path)
        result = model.solve(solver="ortools", time_limit=10)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
