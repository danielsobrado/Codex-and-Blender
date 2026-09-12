from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.model_review import build_model_prompt, collect_image_paths


class ModelReviewTests(unittest.TestCase):
    def test_current_images_precede_reference_images(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current = root / "current.png"
            reference = root / "reference.png"
            current.touch()
            reference.touch()

            paths = collect_image_paths(
                {"views": [{"name": "HeroCamera", "path": str(current)}]},
                {
                    "enabled": True,
                    "views": [
                        {
                            "name": "HeroCamera",
                            "reference": str(reference),
                            "ssim": 0.91,
                            "ssim_min": 0.95,
                        }
                    ],
                },
            )

            self.assertEqual([current, reference], paths)

    def test_prompt_documents_reference_pairing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompt_path = root / "prompt.md"
            current = root / "current.png"
            reference = root / "reference.png"
            state = root / "state.json"
            validation = root / "validation.json"
            prompt_path.write_text("Review contract", encoding="utf-8")
            current.touch()
            reference.touch()

            prompt = build_model_prompt(
                prompt_path,
                {
                    "views": [
                        {
                            "name": "HeroCamera",
                            "role": "hero",
                            "path": str(current),
                        }
                    ]
                },
                state,
                validation,
                {
                    "enabled": True,
                    "views": [
                        {
                            "name": "HeroCamera",
                            "reference": str(reference),
                            "ssim": 0.91,
                            "ssim_min": 0.95,
                        }
                    ],
                },
                root=root,
            )

            self.assertIn("Current render images are attached first", prompt)
            self.assertIn("approved reference for HeroCamera", prompt)
            self.assertIn("SSIM=0.91", prompt)


if __name__ == "__main__":
    unittest.main()
