from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "toolchain.yaml"
CACHE_DIR = ROOT / ".cache" / "blender"
REQUIRED_KEYS = (
    "version",
    "release_channel",
    "linux_x64_archive",
    "checksum_file",
    "download_base_url",
    "extracted_dir",
)


class ToolchainError(RuntimeError):
    pass


def load_config(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        raise ToolchainError(f"Cannot read toolchain config: {path}") from exc

    if not isinstance(value, dict) or not isinstance(value.get("blender"), dict):
        raise ToolchainError("Toolchain config must contain a blender mapping.")

    blender = value["blender"]
    missing = [key for key in REQUIRED_KEYS if not blender.get(key)]
    if missing:
        raise ToolchainError(f"Missing Blender toolchain keys: {', '.join(missing)}")
    return blender


def build_environment(config: dict[str, Any]) -> dict[str, str]:
    base_url = str(config["download_base_url"]).rstrip("/")
    extracted_dir = CACHE_DIR / str(config["extracted_dir"])
    archive = str(config["linux_x64_archive"])

    return {
        "BLENDER_VERSION": str(config["version"]),
        "BLENDER_ARCHIVE": archive,
        "BLENDER_URL": f"{base_url}/{archive}",
        "BLENDER_SHA256_URL": f"{base_url}/{config['checksum_file']}",
        "BLENDER_CACHE_DIR": str(CACHE_DIR),
        "BLENDER_BIN": str(extracted_dir / "blender"),
    }


def write_environment(environment: dict[str, str], destination: Path | None) -> None:
    lines = [f"{key}={value}" for key, value in environment.items()]
    payload = "\n".join(lines) + "\n"

    if destination is None:
        sys.stdout.write(payload)
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve the pinned Blender toolchain.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--github-env", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config.resolve())
        write_environment(build_environment(config), args.github_env)
    except ToolchainError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
