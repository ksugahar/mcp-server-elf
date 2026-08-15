from __future__ import annotations

from pathlib import Path

import pytest

from elf_mcp_server import product_runner


def _product_home(tmp_path: Path) -> Path:
    home = tmp_path / "product"
    binary_dir = home / "bin"
    binary_dir.mkdir(parents=True)
    (binary_dir / "magh1600.dll").write_bytes(b"MZ-fake-magic")
    (binary_dir / "elfh1300.dll").write_bytes(b"MZ-fake-elfin")
    return home


def _case(tmp_path: Path, name: str = "CASE1") -> Path:
    directory = tmp_path / "case"
    directory.mkdir()
    (directory / f"{name}.mai").write_text("USE MAGIC\nPRE\nSOL MOME\nEND\n", encoding="ascii")
    (directory / f"{name}.meg").write_text("BOOK MEP 3.50\nEND\n", encoding="ascii")
    return directory


def test_detect_is_noninvasive_and_reports_fixed_ctypes_backends(tmp_path: Path) -> None:
    home = _product_home(tmp_path)
    result = product_runner.discover_product(str(home))
    assert result["status"] == "ready"
    assert result["execution_mode"] == "isolated_python_ctypes_worker"
    assert result["solvers"]["MAGIC"]["available"] is True
    assert result["solvers"]["ELFIN"]["available"] is True
    assert result["product_binaries_bundled"] is False
    assert "product_home" not in result


def test_case_check_rejects_path_like_case_name_and_missing_pair(tmp_path: Path) -> None:
    home = _product_home(tmp_path)
    directory = _case(tmp_path)
    with pytest.raises(ValueError, match="case_name"):
        product_runner.check_product_case(str(directory), "../CASE1", product_home=str(home))
    (directory / "CASE1.meg").unlink()
    with pytest.raises(ValueError, match="CASE1.meg"):
        product_runner.check_product_case(str(directory), "CASE1", product_home=str(home))


def test_case_check_rejects_non_ctypes_solver(tmp_path: Path) -> None:
    home = _product_home(tmp_path)
    directory = _case(tmp_path)
    with pytest.raises(ValueError, match="MAGIC or ELFIN"):
        product_runner.check_product_case(
            str(directory), "CASE1", solver="BEAM", product_home=str(home)
        )


def test_run_requires_explicit_confirmation_without_loading_dll(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = _product_home(tmp_path)
    directory = _case(tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("worker must not start without confirmation")

    monkeypatch.setattr(product_runner, "_run_worker", forbidden)
    result = product_runner.run_product_case(
        str(directory), "CASE1", product_home=str(home)
    )
    assert result["status"] == "confirmation_required"
    assert result["ok"] is False


def test_run_uses_isolated_worker_and_returns_only_fresh_file_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = _product_home(tmp_path)
    directory = _case(tmp_path)

    def fake_worker(request, run_directory, timeout_seconds, *, include_native_diagnostics):
        assert request["dll_path"].endswith("magh1600.dll")
        assert request["workflow"] == "mome_fiel"
        assert request["record_width"] == 8
        assert timeout_seconds == 15
        assert include_native_diagnostics is False
        (run_directory / "CASE1.mao").write_text("completed", encoding="ascii")
        (run_directory / "CASE1.mag").write_text("field", encoding="ascii")
        return {
            "exit_code": 0,
            "timed_out": False,
            "elapsed_seconds": 0.01,
            "stdout_bytes": 10,
            "stderr_bytes": 0,
            "worker_result": {"ok": True, "calls": ["START_PRE", "SOL_MOME", "GET_FIEL"]},
        }

    monkeypatch.setattr(product_runner, "_run_worker", fake_worker)
    result = product_runner.run_product_case(
        str(directory),
        "CASE1",
        product_home=str(home),
        timeout_seconds=15,
        confirm_product_execution=True,
    )
    assert result["status"] == "completed"
    assert result["ok"] is True
    assert result["inputs_unchanged"] is True
    assert {row["name"] for row in result["fresh_outputs"]} == {"CASE1.mao", "CASE1.mag"}
    assert "stdout_tail" not in result["stage"]
    assert result["raw_outputs_returned_by_mcp"] is False


@pytest.mark.parametrize(
    ("name", "value"),
    [("record_width", 0), ("record_width", 33), ("timeout_seconds", 0), ("timeout_seconds", 86_401)],
)
def test_run_rejects_unbounded_integer_inputs(tmp_path: Path, name: str, value: int) -> None:
    home = _product_home(tmp_path)
    directory = _case(tmp_path)
    kwargs = {name: value}
    with pytest.raises(ValueError, match=name):
        product_runner.run_product_case(
            str(directory), "CASE1", product_home=str(home), **kwargs
        )
