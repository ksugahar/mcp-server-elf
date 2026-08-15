"""Guarded Python/ctypes bridge to a user-local ELF product installation.

The public package contains only orchestration and a small fixed API contract.
It does not contain product DLLs, vendor wrapper source, license material,
product examples, or solver results.  DLL work runs in an isolated Python
worker so a native failure cannot corrupt the long-lived MCP process.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from typing import Any


SCHEMA_VERSION = "elf.product-ctypes-run.v1"
_HOME_ENV_VARS = ("ELF_PRODUCT_HOME", "ELF600_HOME", "ELF_HOME")
_SOLVER_DLLS = {
    "MAGIC": "magh1600.dll",
    "ELFIN": "elfh1300.dll",
}
_CASE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
_INPUT_SUFFIXES = {".mai", ".meg"}
_RESULT_PREFIX = "ELF_MCP_WORKER_RESULT="
_MAX_CAPTURE_CHARS = 60_000
_MAX_HASH_BYTES = 64 * 1024 * 1024
_RUN_LOCK = threading.Lock()


def _sha256(path: Path) -> str | None:
    if path.stat().st_size > _MAX_HASH_BYTES:
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _input_fingerprint(path: Path) -> tuple[int, int, str | None]:
    """Fingerprint an input even when it is too large for the bounded digest."""
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, _sha256(path)


def _file_record(
    path: Path,
    *,
    include_path: bool = False,
    include_digest: bool = True,
) -> dict[str, Any]:
    stat = path.stat()
    record: dict[str, Any] = {
        "name": path.name,
        "suffix": path.suffix.lower(),
        "bytes": stat.st_size,
        "modified_ns": stat.st_mtime_ns,
    }
    if include_digest:
        record["sha256"] = _sha256(path)
    if include_path:
        record["path"] = str(path)
    return record


def _normalize_solver(solver: str) -> str:
    value = str(solver).strip().upper()
    if value not in _SOLVER_DLLS:
        raise ValueError("ctypes execution supports solver MAGIC or ELFIN")
    return value


def _normalize_case_name(case_name: str) -> str:
    value = str(case_name).strip()
    if not _CASE_RE.fullmatch(value):
        raise ValueError(
            "case_name must contain 1-64 ASCII letters, digits, underscores, or hyphens "
            "and must start with a letter or digit"
        )
    return value


def _candidate_homes(product_home: str = "") -> list[tuple[Path, str]]:
    if product_home.strip():
        expanded = os.path.expandvars(os.path.expanduser(product_home.strip()))
        return [(Path(expanded), "explicit")]

    candidates: list[tuple[Path, str]] = []
    for variable in _HOME_ENV_VARS:
        value = os.environ.get(variable, "").strip()
        if value:
            candidates.append((Path(os.path.expandvars(os.path.expanduser(value))), f"env:{variable}"))
    if os.name == "nt":
        drive = os.environ.get("SystemDrive", "").strip()
        if drive:
            candidates.append((Path(drive + os.sep) / "ELF600", "windows-default"))
    return candidates


def _find_home(product_home: str = "") -> tuple[Path | None, str]:
    for candidate, source in _candidate_homes(product_home):
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if resolved.is_dir() and (resolved / "bin").is_dir():
            return resolved, source
    return None, "not-found"


def _allowed_dll(home: Path, name: str) -> Path | None:
    try:
        bin_dir = (home / "bin").resolve(strict=True)
        resolved = (bin_dir / name).resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if not resolved.is_file() or not resolved.is_relative_to(bin_dir):
        return None
    return resolved


def discover_product(product_home: str = "", *, include_paths: bool = False) -> dict[str, Any]:
    """Discover fixed, allow-listed DLLs without loading the product."""
    home, source = _find_home(product_home)
    if home is None:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "not_found",
            "available": False,
            "home_source": source,
            "configuration": {
                "preferred_environment_variable": _HOME_ENV_VARS[0],
                "explicit_product_home_supported": True,
            },
            "execution_mode": "isolated_python_ctypes_worker",
            "product_binaries_bundled": False,
        }

    solvers: dict[str, dict[str, Any]] = {}
    for solver, dll_name in _SOLVER_DLLS.items():
        dll = _allowed_dll(home, dll_name)
        solvers[solver] = {
            "available": dll is not None,
            "dll": (
                _file_record(dll, include_path=include_paths, include_digest=False)
                if dll
                else {"name": dll_name}
            ),
        }
    response: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if any(row["available"] for row in solvers.values()) else "incomplete",
        "available": any(row["available"] for row in solvers.values()),
        "home_source": source,
        "solvers": solvers,
        "execution_mode": "isolated_python_ctypes_worker",
        "product_binaries_bundled": False,
        "supported_workflows": ["mome", "mome_fiel"],
        "safeguards": [
            "fixed DLL and function allow-list",
            "isolated Python worker process",
            "case-name and input-pair validation",
            "no eval, arbitrary Python, shell, or arbitrary native symbol access",
            "explicit execution confirmation",
            "bounded timeout and diagnostics",
            "raw solver files remain in the caller-selected local directory",
        ],
    }
    if include_paths:
        response["product_home"] = str(home)
    return response


def _safe_case_file(directory: Path, case_name: str, suffix: str) -> Path:
    candidate = directory / f"{case_name}{suffix}"
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"required case file is missing: {candidate.name}") from exc
    if not resolved.is_file() or not resolved.is_relative_to(directory):
        raise ValueError(f"case file must be a regular file inside case_directory: {candidate.name}")
    return resolved


def check_product_case(
    case_directory: str,
    case_name: str,
    *,
    solver: str = "MAGIC",
    workflow: str = "mome_fiel",
    product_home: str = "",
    include_paths: bool = False,
) -> dict[str, Any]:
    """Validate a local DLL-backed case without loading or executing the DLL."""
    solver_name = _normalize_solver(solver)
    workflow_name = str(workflow).strip().lower()
    if workflow_name not in {"mome", "mome_fiel"}:
        raise ValueError("workflow must be mome or mome_fiel")
    case = _normalize_case_name(case_name)
    try:
        directory = Path(os.path.expandvars(os.path.expanduser(case_directory))).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("case_directory must be an existing directory") from exc
    if not directory.is_dir():
        raise ValueError("case_directory must be an existing directory")

    inputs = [_safe_case_file(directory, case, suffix) for suffix in (".mai", ".meg")]
    discovery = discover_product(product_home, include_paths=include_paths)
    solver_row = discovery.get("solvers", {}).get(solver_name, {})
    ready = bool(solver_row.get("available"))
    response: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if ready else "not_ready",
        "ready": ready,
        "solver": solver_name,
        "workflow": workflow_name,
        "case_name": case,
        "case_directory_name": directory.name,
        "planned_ctypes_calls": (
            ["START_PRE", "SOL_MOME", "GET_FIEL", "SOL_END", "DE_ALLOCATE", "CLOSE_FILE"]
            if workflow_name == "mome_fiel"
            else ["START_PRE", "SOL_MOME", "SOL_END", "DE_ALLOCATE", "CLOSE_FILE"]
        ),
        "inputs": [_file_record(path, include_path=include_paths) for path in inputs],
        "product": discovery,
        "writes_local_outputs": True,
        "raw_outputs_returned_by_mcp": False,
    }
    if include_paths:
        response["case_directory"] = str(directory)
    return response


def _snapshot_case(directory: Path, case: str) -> dict[str, tuple[int, int]]:
    snapshot: dict[str, tuple[int, int]] = {}
    for path in directory.glob(f"{case}.*"):
        if not path.is_file():
            continue
        stat = path.stat()
        snapshot[path.name] = (stat.st_size, stat.st_mtime_ns)
    return snapshot


def _fresh_outputs(
    directory: Path,
    case: str,
    before: dict[str, tuple[int, int]],
    *,
    include_paths: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(directory.glob(f"{case}.*"), key=lambda item: item.name.lower()):
        if not path.is_file() or path.suffix.lower() in _INPUT_SUFFIXES:
            continue
        stat = path.stat()
        if before.get(path.name) != (stat.st_size, stat.st_mtime_ns):
            rows.append(_file_record(path, include_path=include_paths))
    return rows


def _parse_worker_result(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        if line.startswith(_RESULT_PREFIX):
            try:
                value = json.loads(line[len(_RESULT_PREFIX) :])
            except json.JSONDecodeError:
                return None
            return value if isinstance(value, dict) else None
    return None


def _run_worker(
    request: dict[str, Any],
    directory: Path,
    timeout_seconds: int,
    *,
    include_native_diagnostics: bool,
) -> dict[str, Any]:
    worker = Path(__file__).with_name("_product_worker.py")
    kwargs: dict[str, Any] = {}
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            [sys.executable, str(worker)],
            cwd=str(directory),
            input=json.dumps(request).encode("utf-8"),
            stdout=subprocess.PIPE if include_native_diagnostics else subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
            shell=False,
            **kwargs,
        )
    except subprocess.TimeoutExpired as exc:
        result: dict[str, Any] = {
            "exit_code": None,
            "timed_out": True,
            "elapsed_seconds": round(time.perf_counter() - started, 6),
            "stdout_bytes": len(exc.stdout or b"") if include_native_diagnostics else None,
            "stderr_bytes": len(exc.stderr or b""),
            "worker_result": None,
        }
        if include_native_diagnostics:
            result["stdout_tail"] = (exc.stdout or b"").decode("utf-8", errors="replace")[-_MAX_CAPTURE_CHARS:]
            result["stderr_tail"] = (exc.stderr or b"").decode("utf-8", errors="replace")[-_MAX_CAPTURE_CHARS:]
        return result
    stdout = (completed.stdout or b"").decode("utf-8", errors="replace")
    stderr = completed.stderr.decode("utf-8", errors="replace")
    result = {
        "exit_code": completed.returncode,
        "timed_out": False,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "stdout_bytes": len(completed.stdout) if completed.stdout is not None else None,
        "stderr_bytes": len(completed.stderr),
        "worker_result": _parse_worker_result(stderr),
    }
    if include_native_diagnostics:
        result["stdout_tail"] = stdout[-_MAX_CAPTURE_CHARS:]
        result["stderr_tail"] = stderr[-_MAX_CAPTURE_CHARS:]
    return result


def run_product_case(
    case_directory: str,
    case_name: str,
    *,
    solver: str = "MAGIC",
    workflow: str = "mome_fiel",
    record_width: int = 8,
    timeout_seconds: int = 900,
    confirm_product_execution: bool = False,
    include_native_diagnostics: bool = False,
    product_home: str = "",
    include_paths: bool = False,
) -> dict[str, Any]:
    """Run the fixed DLL workflow through an isolated Python ctypes worker."""
    for value, name, low, high in (
        (record_width, "record_width", 1, 32),
        (timeout_seconds, "timeout_seconds", 1, 86_400),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < low or value > high:
            raise ValueError(f"{name} must be an integer between {low} and {high}")

    check = check_product_case(
        case_directory,
        case_name,
        solver=solver,
        workflow=workflow,
        product_home=product_home,
        include_paths=include_paths,
    )
    if not confirm_product_execution:
        return {
            **check,
            "status": "confirmation_required",
            "ok": False,
            "required_confirmation": "confirm_product_execution=true",
        }
    if not check["ready"]:
        return {**check, "status": "not_ready", "ok": False}

    case = check["case_name"]
    directory = Path(os.path.expandvars(os.path.expanduser(case_directory))).resolve(strict=True)
    home, _ = _find_home(product_home)
    if home is None:
        return {**check, "status": "not_ready", "ok": False}
    dll = _allowed_dll(home, _SOLVER_DLLS[check["solver"]])
    if dll is None:
        return {**check, "status": "not_ready", "ok": False}

    input_before = {
        suffix: _input_fingerprint(_safe_case_file(directory, case, suffix))
        for suffix in (".mai", ".meg")
    }
    before = _snapshot_case(directory, case)
    request = {
        "schema_version": SCHEMA_VERSION,
        "dll_path": str(dll),
        "case_name": case,
        "workflow": check["workflow"],
        "record_width": record_width,
    }
    with _RUN_LOCK:
        stage = _run_worker(
            request,
            directory,
            timeout_seconds,
            include_native_diagnostics=include_native_diagnostics,
        )

    if not include_native_diagnostics and isinstance(stage.get("worker_result"), dict):
        worker_public = stage["worker_result"]
        stage["worker_result"] = {
            key: worker_public[key]
            for key in ("ok", "calls", "error_type")
            if key in worker_public
        }

    input_after = {
        suffix: _input_fingerprint(_safe_case_file(directory, case, suffix))
        for suffix in (".mai", ".meg")
    }
    inputs_unchanged = input_before == input_after
    fresh = _fresh_outputs(directory, case, before, include_paths=include_paths)
    worker_result = stage.get("worker_result") or {}
    ok = bool(
        not stage["timed_out"]
        and stage["exit_code"] == 0
        and worker_result.get("ok") is True
        and inputs_unchanged
        and fresh
    )
    return {
        **check,
        "status": "completed" if ok else "failed",
        "ok": ok,
        "execution_mode": "isolated_python_ctypes_worker",
        "stage": stage,
        "inputs_unchanged": inputs_unchanged,
        "fresh_outputs": fresh,
        "raw_outputs_returned_by_mcp": False,
        "next_call": (
            "elf_python_run_result_parse_path(run_path=<same local directory>)"
            if ok
            else "inspect the bounded worker diagnostics and correct the local case"
        ),
    }
