from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def load(self, relative: str) -> dict:
        with (ROOT / relative).open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        self.assertIsInstance(data, dict)
        return data

    def test_workflow_has_required_sections(self) -> None:
        config = self.load("config/workflow.yaml")
        for section in ("blender", "paths", "scene", "cameras", "lights", "render"):
            self.assertIn(section, config)

    def test_exactly_one_primary_camera(self) -> None:
        config = self.load("config/workflow.yaml")
        primary = [camera for camera in config["cameras"] if camera.get("primary", False)]
        self.assertEqual(1, len(primary))

    def test_acceptance_has_structural_rules(self) -> None:
        config = self.load("config/acceptance.yaml")
        self.assertIn("structural", config)
        self.assertIn("required_objects", config["structural"])


if __name__ == "__main__":
    unittest.main()
