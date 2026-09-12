from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts.reference_regression import (
    ReferenceRegressionError,
    evaluate_reference_regression,
    ssim_score,
)


class ReferenceRegressionTests(unittest.TestCase):
    def image(self, path: Path, split: int | None = None) -> None:
        image = Image.new("RGB", (32, 32), (32, 64, 96))
        if split is not None:
            image.paste((220, 220, 220), (split, 0, 32, 32))
        image.save(path)

    def test_identical_images_have_perfect_ssim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            left = root / "left.png"
            right = root / "right.png"
            self.image(left)
            self.image(right)

            self.assertAlmostEqual(1.0, ssim_score(left, right), places=6)

    def test_gate_fails_below_per_view_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / "current.png"
            reference = root / "reference.png"
            self.image(reference)
            self.image(current, split=16)

            result = evaluate_reference_regression(
                {
                    "views": [
                        {"name": "HeroCamera", "path": str(current)}
                    ]
                },
                {
                    "enabled": True,
                    "mode": "gate",
                    "views": [
                        {
                            "name": "HeroCamera",
                            "reference": str(reference),
                            "ssim_min": 0.99,
                        }
                    ],
                },
                root=root,
            )

            self.assertFalse(result["passed"])
            self.assertFalse(result["views"][0]["meets_threshold"])
            self.assertLess(result["views"][0]["ssim"], 0.99)

    def test_report_only_does_not_gate_without_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / "current.png"
            reference = root / "reference.png"
            self.image(reference)
            self.image(current, split=16)

            result = evaluate_reference_regression(
                {"views": [{"name": "HeroCamera", "path": str(current)}]},
                {
                    "enabled": True,
                    "mode": "report_only",
                    "views": [
                        {"name": "HeroCamera", "reference": str(reference)}
                    ],
                },
                root=root,
            )

            self.assertTrue(result["passed"])
            self.assertIsNone(result["views"][0]["meets_threshold"])

    def test_dimension_mismatch_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / "current.png"
            reference = root / "reference.png"
            self.image(current)
            Image.new("RGB", (16, 16), (32, 64, 96)).save(reference)

            with self.assertRaises(ReferenceRegressionError):
                ssim_score(current, reference)


if __name__ == "__main__":
    unittest.main()
