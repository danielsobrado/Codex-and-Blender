from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys

LOGGER = logging.getLogger("environment_check")
MIN_CODEX_VERSION = (0, 153, 0)


def resolve_blender() -> str | None:
    configured = os.getenv("BLENDER_BIN")
    return configured or shutil.which("blender")


def command_output(command: str, args: list[str]) -> str | None:
    executable = shutil.which(command)
    if not executable:
        LOGGER.warning("Optional command not found: %s", command)
        return None

    try:
        result = subprocess.run(
            [executable, *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        LOGGER.warning("Could not execute %s: %s", command, exc)
        return None

    output = result.stdout or result.stderr
    first_line = output.splitlines()[0] if output else "detected"
    LOGGER.info("%s: %s", command, first_line)
    return output


def parse_version(value: str) -> tuple[int, int, int] | None:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def check_codex() -> bool:
    output = command_output("codex", ["--version"])
    if output is None:
        return False

    version = parse_version(output)
    if version is None:
        LOGGER.warning("Could not parse Codex CLI version.")
        return False
    if version < MIN_CODEX_VERSION:
        LOGGER.error(
            "Codex CLI %s is too old for the Astra workflow; require >= %s.",
            ".".join(map(str, version)),
            ".".join(map(str, MIN_CODEX_VERSION)),
        )
        return False
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

    codex_ready = check_codex()
    command_output("blender-mcp", ["--help"])
    return 0 if codex_ready else 1


if __name__ == "__main__":
    sys.exit(main())
