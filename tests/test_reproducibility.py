from __future__ import annotations

import unittest

from scripts.reproducibility_check import compare_manifests


class ReproducibilityTests(unittest.TestCase):
    def test_numeric_values_within_tolerance_match(self) -> None:
        differences, truncated = compare_manifests(
            {"location": [1.0, 2.0, 3.0]},
            {"location": [1.0 + 1.0e-7, 2.0, 3.0]},
            tolerance=1.0e-6,
            max_differences=10,
        )

        self.assertEqual([], differences)
        self.assertFalse(truncated)

    def test_numeric_difference_reports_exact_path(self) -> None:
        differences, truncated = compare_manifests(
            {"objects": [{"scale": [1.0, 1.0, 1.0]}]},
            {"objects": [{"scale": [1.0, 1.01, 1.0]}]},
            tolerance=1.0e-6,
            max_differences=10,
        )

        self.assertEqual(1, len(differences))
        self.assertEqual("$.objects[0].scale[1]", differences[0]["path"])
        self.assertFalse(truncated)

    def test_boolean_values_are_not_treated_as_numbers(self) -> None:
        differences, _ = compare_manifests(
            {"visible": True},
            {"visible": False},
            tolerance=1.0,
            max_differences=10,
        )

        self.assertEqual("value differs", differences[0]["reason"])


if __name__ == "__main__":
    unittest.main()
