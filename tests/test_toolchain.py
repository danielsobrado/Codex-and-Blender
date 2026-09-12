from __future__ import annotations

import unittest
from pathlib import Path

from scripts.toolchain_env import build_environment, load_config

ROOT = Path(__file__).resolve().parents[1]


class ToolchainTests(unittest.TestCase):
    def test_pinned_blender_environment(self) -> None:
        config = load_config(ROOT / "config" / "toolchain.yaml")
        environment = build_environment(config)

        self.assertEqual(config["version"], environment["BLENDER_VERSION"])
        self.assertTrue(environment["BLENDER_URL"].endswith(config["linux_x64_archive"]))
        self.assertTrue(environment["BLENDER_SHA256_URL"].endswith(config["checksum_file"]))
        self.assertTrue(environment["BLENDER_BIN"].endswith("/blender"))


if __name__ == "__main__":
    unittest.main()
