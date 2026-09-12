from __future__ import annotations

from pathlib import Path

import bpy


def missing_external_files() -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []

    for image in bpy.data.images:
        if image.source != "FILE" or not image.filepath:
            continue
        path = Path(bpy.path.abspath(image.filepath))
        if not path.exists():
            missing.append({"kind": "image", "name": image.name, "path": str(path)})

    for library in bpy.data.libraries:
        if not library.filepath:
            continue
        path = Path(bpy.path.abspath(library.filepath))
        if not path.exists():
            missing.append({"kind": "library", "name": library.name, "path": str(path)})

    return sorted(missing, key=lambda item: (item["kind"], item["name"]))
