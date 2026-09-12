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

    def test_workflow_has_autonomous_artifact_paths(self) -> None:
        paths = self.load("config/workflow.yaml")["paths"]
        for key in (
            "render_index_file",
            "evaluation_file",
            "run_report_file",
            "iteration_dir",
            "best_dir",
            "evaluator_file",
            "autonomy_file",
        ):
            self.assertIn(key, paths)

    def test_exactly_one_primary_camera(self) -> None:
        config = self.load("config/workflow.yaml")
        primary = [camera for camera in config["cameras"] if camera.get("primary", False)]
        self.assertEqual(1, len(primary))

    def test_cameras_define_visual_contract(self) -> None:
        config = self.load("config/workflow.yaml")
        for camera in config["cameras"]:
            self.assertTrue(camera.get("role"))
            self.assertIn("required", camera)

    def test_acceptance_has_structural_rules(self) -> None:
        config = self.load("config/acceptance.yaml")
        self.assertIn("structural", config)
        self.assertIn("required_objects", config["structural"])
        self.assertGreaterEqual(config["iteration"]["max_iterations"], 1)

    def test_evaluator_contract_exists(self) -> None:
        config = self.load("config/evaluator.yaml")
        model = config["model_review"]
        self.assertIn(model["provider"], {"codex", "grok"})
        self.assertTrue(model.get("model"))
        self.assertTrue((ROOT / model["prompt_file"]).exists())
        self.assertTrue((ROOT / model["output_schema_file"]).exists())

    def test_autonomy_protects_quality_gates(self) -> None:
        config = self.load("config/autonomy.yaml")
        protected = set(config["protected_files"])
        self.assertIn("config/acceptance.yaml", protected)
        self.assertIn("config/evaluator.yaml", protected)
        self.assertIn("config/autonomy.yaml", protected)
        self.assertIn("schemas/visual_evaluation.schema.json", protected)
        self.assertIn("prompts/visual_review.md", protected)


if __name__ == "__main__":
    unittest.main()
