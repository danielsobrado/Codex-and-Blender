from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.iteration_controller import (
    build_patch_prompt,
    capture_protected,
    restore_protected,
)


class IterationControllerTests(unittest.TestCase):
    def test_patch_prompt_lists_protected_files(self) -> None:
        evaluation = Path("output/visual_evaluation.json")
        protected = [Path("config/acceptance.yaml"), Path("config/evaluator.yaml")]

        prompt = build_patch_prompt(evaluation, protected)

        self.assertIn("config/acceptance.yaml", prompt)
        self.assertIn("config/evaluator.yaml", prompt)
        self.assertIn("Do not commit", prompt)
        self.assertIn("Do not edit generated files under output/", prompt)

    def test_restore_protected_restores_changed_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "quality.yaml"
            path.write_text("passed: false\n", encoding="utf-8")
            snapshot = capture_protected([path])

            path.write_text("passed: true\n", encoding="utf-8")
            changed = restore_protected(snapshot)

            self.assertEqual(1, len(changed))
            self.assertEqual("passed: false\n", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
