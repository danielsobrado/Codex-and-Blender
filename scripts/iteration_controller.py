from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

LOGGER = logging.getLogger("iteration_controller")
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW = ROOT / "config" / "workflow.yaml"
CODEX_EXECUTABLE = "codex"
CODEX_SANDBOX = "workspace-write"


class ControllerError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        raise ControllerError(f"Cannot read YAML: {path}") from exc
    if not isinstance(value, dict):
        raise ControllerError(f"YAML root must be a mapping: {path}")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ControllerError(f"Cannot read JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ControllerError(f"JSON root must be an object: {path}")
    return value


def resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (ROOT / path).resolve()


def run(command: list[str], timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    LOGGER.info("Running: %s", " ".join(command[:4]))
    try:
        return subprocess.run(
            command,
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=False,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise ControllerError(f"Executable was not found: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ControllerError(f"Command timed out: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise ControllerError(
            f"Command failed with exit code {exc.returncode}: {command[0]}"
        ) from exc


def git_output(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise ControllerError("Git command failed.") from exc
    return result.stdout


def worktree_status() -> str:
    return git_output("status", "--porcelain", "--untracked-files=all")


def file_digest(path: Path) -> str:
    if not path.exists():
        return "<missing>"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture_protected(paths: list[Path]) -> dict[Path, tuple[str, bytes | None]]:
    result: dict[Path, tuple[str, bytes | None]] = {}
    for path in paths:
        data = path.read_bytes() if path.exists() else None
        result[path] = (file_digest(path), data)
    return result


def restore_protected(snapshot: dict[Path, tuple[str, bytes | None]]) -> list[str]:
    changed: list[str] = []
    for path, (digest, data) in snapshot.items():
        if file_digest(path) == digest:
            continue
        changed.append(str(path.relative_to(ROOT)))
        if data is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    return changed


def copy_if_exists(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def snapshot_iteration(
    workflow: dict[str, Any], iteration: int, retain_blend: bool
) -> Path:
    paths = workflow["paths"]
    target = resolve(paths["iteration_dir"]) / f"{iteration:03d}"
    target.mkdir(parents=True, exist_ok=True)

    artifact_keys = (
        "render_file",
        "render_dir",
        "render_index_file",
        "state_file",
        "validation_file",
        "evaluation_file",
    )
    for key in artifact_keys:
        source = resolve(paths[key])
        copy_if_exists(source, target / source.name)

    if retain_blend:
        source = resolve(paths["blend_file"])
        copy_if_exists(source, target / source.name)

    (target / "source.diff").write_text(
        git_output("diff", "--binary"), encoding="utf-8"
    )
    (target / "source.status").write_text(worktree_status(), encoding="utf-8")
    return target


def promote_best(workflow: dict[str, Any], snapshot: Path, score: int) -> None:
    best_dir = resolve(workflow["paths"]["best_dir"])
    if best_dir.exists():
        shutil.rmtree(best_dir)
    shutil.copytree(snapshot, best_dir)
    (best_dir / "best.json").write_text(
        json.dumps({"score": score, "snapshot": snapshot.name}, indent=2),
        encoding="utf-8",
    )


def build_patch_prompt(evaluation_path: Path) -> str:
    return f"""You are the correction worker inside a bounded Blender visual-quality loop.

Read AGENTS.md, the durable scene source, and {evaluation_path.relative_to(ROOT)}.
Implement the smallest source-controlled correction that addresses the highest-severity supported visual issues.

Rules:
- Edit durable source only: config/workflow.yaml and code/assets intentionally owned by this repository.
- Do not edit generated files under output/.
- Do not weaken or edit acceptance/evaluator/autonomy policy, the visual evaluation schema, or its review prompt.
- Do not commit, push, or invoke scripts/iteration_controller.py.
- Do not make unrelated cleanup changes.
- Prefer exact Blender state over guessing dimensions from pixels.
- The parent controller will rebuild, render, and evaluate after you return.

If the evidence does not justify a safe source change, make no changes and explain why.
"""


def run_correction_worker(
    workflow: dict[str, Any],
    autonomy: dict[str, Any],
    evaluation_path: Path,
    summary_path: Path,
) -> None:
    if shutil.which(CODEX_EXECUTABLE) is None:
        raise ControllerError("Codex CLI was not found on PATH.")

    evaluator = load_yaml(resolve(workflow["paths"]["evaluator_file"]))
    model = evaluator.get("model_review", {})
    prompt = build_patch_prompt(evaluation_path)
    command = [
        CODEX_EXECUTABLE,
        "exec",
        "--ephemeral",
        "--sandbox",
        CODEX_SANDBOX,
        "--model",
        str(model.get("model", "gpt-6-astra")),
        "--config",
        f'model_reasoning_effort="{model.get("reasoning_effort", "high")}"',
        "--output-last-message",
        str(summary_path),
        "-",
    ]
    timeout = int(autonomy.get("patch_timeout_seconds", 900))
    try:
        subprocess.run(
            command,
            cwd=ROOT,
            input=prompt,
            text=True,
            check=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise ControllerError("Codex CLI was not found on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise ControllerError("Correction worker timed out.") from exc
    except subprocess.CalledProcessError as exc:
        raise ControllerError(
            f"Correction worker failed with exit code {exc.returncode}."
        ) from exc


def write_report(workflow: dict[str, Any], report: dict[str, Any]) -> None:
    output = resolve(workflow["paths"]["run_report_file"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")


def execute_loop(
    workflow_path: Path,
    max_iterations_override: int | None,
    allow_dirty: bool,
) -> dict[str, Any]:
    workflow = load_yaml(workflow_path)
    paths = workflow["paths"]
    acceptance = load_yaml(resolve(paths["acceptance_file"]))
    autonomy = load_yaml(resolve(paths["autonomy_file"]))
    configured_max = int(acceptance.get("iteration", {}).get("max_iterations", 1))
    max_iterations = max_iterations_override or configured_max
    if max_iterations < 1:
        raise ControllerError("Iteration budget must be at least one.")

    if autonomy.get("require_clean_worktree_on_start", True) and not allow_dirty:
        dirty = worktree_status()
        if dirty:
            raise ControllerError(
                "Autonomous correction requires a clean worktree. Use --allow-dirty only when intentional."
            )

    protected = [resolve(value) for value in autonomy.get("protected_files", [])]
    report: dict[str, Any] = {
        "version": 1,
        "started_at": datetime.now(UTC).isoformat(),
        "start_head": git_output("rev-parse", "HEAD").strip(),
        "max_iterations": max_iterations,
        "iterations": [],
        "passed": False,
        "stop_reason": None,
    }
    best_score = -1

    for iteration in range(1, max_iterations + 1):
        LOGGER.info("Iteration %d/%d", iteration, max_iterations)
        try:
            run([sys.executable, str(ROOT / "scripts" / "blender_runner.py"), "all", "--config", str(workflow_path)])
        except ControllerError as exc:
            report["stop_reason"] = "build_or_structural_validation_failed"
            report["iterations"].append({"iteration": iteration, "error": str(exc)})
            break

        try:
            run([sys.executable, str(ROOT / "scripts" / "visual_evaluator.py"), "--config", str(workflow_path)])
            evaluation_path = resolve(paths["evaluation_file"])
            evaluation = load_json(evaluation_path)
        except ControllerError as exc:
            report["stop_reason"] = "visual_evaluator_failed"
            report["iterations"].append({"iteration": iteration, "error": str(exc)})
            break

        snapshot = snapshot_iteration(
            workflow,
            iteration,
            bool(autonomy.get("retain_blend_in_snapshots", False)),
        )
        score_value = evaluation.get("score")
        score = int(score_value) if isinstance(score_value, int) else -1
        if score > best_score:
            promote_best(workflow, snapshot, score)
            best_score = score

        iteration_result = {
            "iteration": iteration,
            "passed": bool(evaluation.get("passed", False)),
            "score": score_value,
            "snapshot": str(snapshot.relative_to(ROOT)),
        }
        report["iterations"].append(iteration_result)

        if evaluation.get("passed", False):
            report["passed"] = True
            report["stop_reason"] = "accepted"
            break

        if iteration == max_iterations:
            report["stop_reason"] = "iteration_budget_exhausted"
            break

        protected_before = capture_protected(protected)
        status_before = worktree_status()
        summary_path = snapshot / "codex_correction.txt"
        try:
            run_correction_worker(
                workflow, autonomy, evaluation_path, summary_path
            )
        except ControllerError as exc:
            report["stop_reason"] = "correction_worker_failed"
            iteration_result["correction_error"] = str(exc)
            break

        changed_protected = restore_protected(protected_before)
        if changed_protected:
            report["stop_reason"] = "protected_quality_gate_modified"
            iteration_result["protected_files_restored"] = changed_protected
            break

        status_after = worktree_status()
        if status_after == status_before:
            report["stop_reason"] = "no_source_change"
            break

    report["finished_at"] = datetime.now(UTC).isoformat()
    report["best_score"] = None if best_score < 0 else best_score
    write_report(workflow, report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run bounded Blender visual self-correction.")
    parser.add_argument("--config", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--max-iterations", type=int)
    parser.add_argument("--allow-dirty", action="store_true")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    try:
        report = execute_loop(
            args.config.resolve(), args.max_iterations, args.allow_dirty
        )
    except (ControllerError, KeyError, TypeError, ValueError) as exc:
        LOGGER.error("%s", exc)
        return 2

    LOGGER.info("Autonomous loop passed=%s stop=%s", report["passed"], report["stop_reason"])
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
