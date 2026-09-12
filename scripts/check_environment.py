from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys

LOGGER = logging.getLogger("environment_check")


def resolve_blender() -> str | None:
    configured = os.getenv("BLENDER_BIN")
    return configured or shutil.which("blender")


def check_command(command: str, args: list[str]) -> bool:
    executable = shutil.which(command)
    if not executable:
        LOGGER.warning("Optional command not found: %s", command)
        return False

    try:
        result = subprocess.run(
            [executable, *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        LOGGER.warning("Could not execute %s: %s", command, exc)
        return False

    output = (result.stdout or result.stderr).splitlines()
    LOGGER.info("%s: %s", command, output[0] if output else "detected")
    return True


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    blender = resolve_blender()
    if not blender:
        LOGGER.error("Blender not found. Set BLENDER_BIN or add Blender to PATH.")
        return 1

    try:
        result = subprocess.run(
            [blender, "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        LOGGER.error("Failed to execute Blender: %s", exc)
        return 1

    first_line = result.stdout.splitlines()[0] if result.stdout else "Blender detected"
    LOGGER.info("%s", first_line)

    check_command("codex", ["--version"])
    check_command("blender-mcp", ["--help"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
