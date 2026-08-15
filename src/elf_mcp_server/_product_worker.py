"""Isolated implementation detail for the fixed ELF ctypes workflow."""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import sys
import traceback
from typing import Any


_RESULT_PREFIX = "ELF_MCP_WORKER_RESULT="
_CASE_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")
_CASE_FIRST_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
_ALLOWED_DLLS = {"magh1600.dll", "elfh1300.dll"}
_SET_WIDTH_FUNCTIONS = ("SET_NMAD", "SET_NMAF", "SET_NMAG", "SET_NMAH", "SET_NMAO")
_NO_ARG_FUNCTIONS = ("SOL_MOME", "GET_FIEL", "SOL_END", "DE_ALLOCATE", "CLOSE_FILE")


def _emit(payload: dict[str, Any]) -> None:
    print(
        _RESULT_PREFIX + json.dumps(payload, ensure_ascii=True, separators=(",", ":")),
        file=sys.stderr,
        flush=True,
    )


def _validate_request(payload: dict[str, Any]) -> tuple[Path, str, str, int]:
    dll = Path(str(payload.get("dll_path", ""))).resolve(strict=True)
    if dll.name.lower() not in _ALLOWED_DLLS or not dll.is_file():
        raise ValueError("DLL is not in the fixed product allow-list")
    case = str(payload.get("case_name", ""))
    if not case or len(case) > 64 or case[0] not in _CASE_FIRST_CHARS or any(ch not in _CASE_CHARS for ch in case):
        raise ValueError("invalid case_name")
    workflow = str(payload.get("workflow", "")).lower()
    if workflow not in {"mome", "mome_fiel"}:
        raise ValueError("invalid workflow")
    width = payload.get("record_width")
    if isinstance(width, bool) or not isinstance(width, int) or width < 1 or width > 32:
        raise ValueError("invalid record_width")
    return dll, case, workflow, width


def _configure(dll: ctypes.CDLL) -> None:
    dll.START_PRE.restype = None
    dll.START_PRE.argtypes = [ctypes.c_char_p]
    for name in _SET_WIDTH_FUNCTIONS:
        function = getattr(dll, name)
        function.restype = None
        function.argtypes = [ctypes.POINTER(ctypes.c_int)]
    for name in _NO_ARG_FUNCTIONS:
        function = getattr(dll, name)
        function.restype = None
        function.argtypes = []


def _best_effort_cleanup(dll: ctypes.CDLL, calls: list[str]) -> None:
    for name in ("SOL_END", "DE_ALLOCATE", "CLOSE_FILE"):
        if name in calls:
            continue
        try:
            getattr(dll, name)()
            calls.append(name)
        except Exception:
            pass


def main() -> int:
    calls: list[str] = []
    loaded: ctypes.CDLL | None = None
    dll_directory_handle: Any = None
    try:
        raw = sys.stdin.buffer.read()
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("request must be a JSON object")
        dll_path, case, workflow, width = _validate_request(payload)
        if os.name == "nt" and hasattr(os, "add_dll_directory"):
            dll_directory_handle = os.add_dll_directory(str(dll_path.parent))
        loaded = ctypes.CDLL(str(dll_path))
        _configure(loaded)

        loaded.START_PRE((case + "/").encode("ascii"))
        calls.append("START_PRE")
        width_value = ctypes.c_int(width)
        for name in _SET_WIDTH_FUNCTIONS:
            getattr(loaded, name)(ctypes.byref(width_value))
            calls.append(name)
        loaded.SOL_MOME()
        calls.append("SOL_MOME")
        if workflow == "mome_fiel":
            loaded.GET_FIEL()
            calls.append("GET_FIEL")
        loaded.SOL_END()
        calls.append("SOL_END")
        loaded.DE_ALLOCATE()
        calls.append("DE_ALLOCATE")
        loaded.CLOSE_FILE()
        calls.append("CLOSE_FILE")
        _emit({"ok": True, "calls": calls})
        return 0
    except BaseException as exc:
        if loaded is not None:
            _best_effort_cleanup(loaded, calls)
        _emit(
            {
                "ok": False,
                "calls": calls,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback_tail": traceback.format_exc().splitlines()[-8:],
            }
        )
        return 1
    finally:
        if dll_directory_handle is not None:
            dll_directory_handle.close()


if __name__ == "__main__":
    raise SystemExit(main())
