from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts.visual_evaluator import (
    EvaluationError,
    build_render_index,
    deterministic_review,
)


class VisualEvaluatorTests(unittest.TestCase):
    def workflow(self, root: Path, cameras: list[dict], include_reviews: bool = True) -> dict:
        return {
            "paths": {
                "render_file": str(root / "hero.png"),
                "render_dir": str(root / "reviews"),
                "render_index_file": str(root / "render_index.json"),
            },
            "cameras": cameras,
            "render": {"render_review_cameras": include_reviews},
        }

    def test_render_index_preserves_camera_roles(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflow = self.workflow(
                root,
                [
                    {
                        "name": "HeroCamera",
                        "role": "hero",
                        "primary": True,
                        "required": True,
                    },
                    {
                        "name": "SideCamera",
                        "role": "side",
                        "primary": False,
                        "required": True,
                    },
                ],
            )

            index = build_render_index(workflow)

            self.assertEqual(["hero", "side"], [view["role"] for view in index["views"]])
            self.assertTrue((root / "render_index.json").exists())

    def test_required_review_camera_cannot_be_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflow = self.workflow(
                root,
                [
                    {"name": "HeroCamera", "primary": True, "required": True},
                    {"name": "SideCamera", "primary": False, "required": True},
                ],
                include_reviews=False,
            )

            with self.assertRaises(EvaluationError):
                build_render_index(workflow)

    def test_protected_required_view_cannot_be_downgraded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflow = self.workflow(
                root,
                [
                    {
                        "name": "HeroCamera",
                        "role": "hero",
                        "primary": True,
                        "required": True,
                    },
                    {
                        "name": "SideCamera",
                        "role": "side",
                        "primary": False,
                        "required": False,
                    },
                ],
                include_reviews=False,
            )
            acceptance = {
                "visual": {
                    "required_views": [
                        {"name": "SideCamera", "role": "side", "primary": False}
                    ]
                }
            }

            with self.assertRaises(EvaluationError):
                build_render_index(workflow, acceptance)

    def test_protected_required_view_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflow = self.workflow(
                root,
                [
                    {
                        "name": "HeroCamera",
                        "role": "hero",
                        "primary": True,
                        "required": True,
                    }
                ],
            )
            acceptance = {
                "visual": {
                    "required_views": [
                        {"name": "SideCamera", "role": "side", "primary": False}
                    ]
                }
            }

            with self.assertRaises(EvaluationError):
                build_render_index(workflow, acceptance)

    def test_protected_required_view_role_cannot_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflow = self.workflow(
                root,
                [
                    {
                        "name": "HeroCamera",
                        "role": "hero",
                        "primary": True,
                        "required": True,
                    },
                    {
                        "name": "SideCamera",
                        "role": "detail",
                        "primary": False,
                        "required": True,
                    },
                ],
            )
            acceptance = {
                "visual": {
                    "required_views": [
                        {"name": "SideCamera", "role": "side", "primary": False}
                    ]
                }
            }

            with self.assertRaises(EvaluationError):
                build_render_index(workflow, acceptance)

    def test_deterministic_review_accepts_non_flat_render(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "render.png"
            image = Image.new("L", (400, 400), 0)
            image.paste(255, (200, 0, 400, 400))
            image.save(path)

            result = deterministic_review(
                {
                    "views": [
                        {
                            "name": "HeroCamera",
                            "role": "hero",
                            "primary": True,
                            "required": True,
                            "path": str(path),
                        }
                    ]
                },
                {
                    "min_width": 320,
                    "min_height": 320,
                    "min_luminance_stddev": 1.0,
                    "max_dark_fraction": 0.995,
                    "max_bright_fraction": 0.995,
                    "dark_threshold": 4,
                    "bright_threshold": 251,
                },
            )

            self.assertTrue(result["passed"])
            self.assertGreater(result["views"][0]["metrics"]["luminance_stddev"], 1.0)

    def test_missing_required_render_fails(self) -> None:
        result = deterministic_review(
            {
                "views": [
                    {
                        "name": "RequiredCamera",
                        "role": "hero",
                        "primary": True,
                        "required": True,
                        "path": "/path/that/does/not/exist.png",
                    }
                ]
            },
            {},
        )

        self.assertFalse(result["passed"])
        self.assertEqual("RequiredCamera", result["errors"][0]["view"])


if __name__ == "__main__":
    unittest.main()
