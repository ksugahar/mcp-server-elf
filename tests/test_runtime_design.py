from __future__ import annotations

import asyncio
import zipfile

import pytest
from pydantic import TypeAdapter, ValidationError

from elf_mcp_server.handlers import (
    elf_catalog_page,
    elf_overview,
    elf_sample_decks_index,
    elf_search,
    mcp,
    new_elf_analysis,
)
from elf_mcp_server.help_access import get_help_file, search_help
from elf_mcp_server.guards import NonNegativeFloat, PositiveFloat
from elf_mcp_server.ngsolve_multiphysics import (
    build_ngsolve_validation_script,
    build_ngsolve_validation_spec,
)
from elf_mcp_server.policy_lint import _content_digest, audit_wheel
from elf_mcp_server.project_feature_inventory_contract import FEATURE_ROUTES
from elf_mcp_server.python_facade import build_motor_demag_margin_plan
from elf_mcp_server.sample_decks import build_mcp_readiness, search_sample_decks
from elf_mcp_server.tool_definitions import TOOL_CONTRACTS


def test_runtime_surface_is_explicit_and_safely_annotated() -> None:
    tools = asyncio.run(mcp.list_tools())
    assert {tool.name for tool in tools} == set(TOOL_CONTRACTS)
    assert len(tools) == 115
    for tool in tools:
        contract = TOOL_CONTRACTS[tool.name]
        assert tool.title == contract.title
        assert tool.annotations is not None
        assert tool.annotations.readOnlyHint is contract.read_only
        assert tool.annotations.destructiveHint is contract.destructive
        assert tool.annotations.idempotentHint is contract.idempotent
        assert tool.annotations.openWorldHint is contract.open_world
        assert tool.meta["elf.contract"] == "elf.mcp-server-contract.v3"
        expected_classification = (
            "read-only-external"
            if contract.read_only and contract.open_world
            else "read-only-local"
            if contract.read_only
            else "local-product-execution"
        )
        assert tool.meta["elf.classification"] == expected_classification


def test_canonical_tools_publish_bounds_and_semantic_output_schemas() -> None:
    tools = {tool.name: tool for tool in asyncio.run(mcp.list_tools())}
    search_schema = tools["elf_search"].outputSchema
    page_schema = tools["elf_catalog_page"].outputSchema
    assert search_schema["properties"]["schema_version"]["const"] == "elf.search.v1"
    assert "hits" in search_schema["properties"]
    assert tools["elf_search"].inputSchema["properties"]["top_k"]["maximum"] == 100
    assert page_schema["properties"]["limit"]["maximum"] == 200
    product_schema = tools["elf_product_run"].inputSchema["properties"]
    assert product_schema["timeout_seconds"]["maximum"] == 86_400
    assert product_schema["record_width"]["maximum"] == 32
    assert product_schema["case_name"]["pattern"].startswith("^")

    result = elf_search("electrostatic", source="help", top_k=3)
    assert result.schema_version == "elf.search.v1"
    assert result.total <= 3
    page = elf_catalog_page(source="samples", offset=5, limit=3)
    assert page.returned == 3
    assert page.offset == 5
    assert page.has_more is True


def test_resources_templates_and_prompt_are_first_class() -> None:
    resources = asyncio.run(mcp.list_resources())
    templates = asyncio.run(mcp.list_resource_templates())
    prompts = asyncio.run(mcp.list_prompts())
    assert {str(resource.uri) for resource in resources} == {
        "elf://guides/overview",
        "elf://guides/public-boundary",
        "elf://corpus/help",
        "elf://corpus/python",
    }
    assert [template.uriTemplate for template in templates] == ["elf://topics/{topic}"]
    assert [(prompt.name, prompt.title) for prompt in prompts] == [
        ("new_elf_analysis", "New ELF Analysis")
    ]
    content = asyncio.run(mcp.read_resource("elf://guides/overview"))
    assert "Python/ctypes bridge" in content[0].content
    prompt = asyncio.run(
        mcp.get_prompt(
            "new_elf_analysis", {"geometry": "parallel-plate capacitor", "solver": "ELFIN"}
        )
    )
    text = prompt.messages[0].content.text
    assert "electrostatic" in text
    assert "dielectric" in text


def test_numeric_and_output_bounds_reject_bypass_values() -> None:
    with pytest.raises(ValueError, match="top_k"):
        search_sample_decks("SOL", top_k=-1)
    with pytest.raises(ValueError, match="top_k"):
        search_help("field", top_k=101)
    with pytest.raises(ValueError, match="max_chars"):
        get_help_file("guides/magic", max_chars=-1)
    with pytest.raises(ValueError, match="iron_mu_r"):
        build_motor_demag_margin_plan(iron_mu_r=0)
    with pytest.raises(ValueError, match="mu_rec"):
        build_motor_demag_margin_plan(mu_rec=0)
    with pytest.raises(ValidationError):
        TypeAdapter(PositiveFloat).validate_python(float("inf"))
    with pytest.raises(ValidationError):
        TypeAdapter(NonNegativeFloat).validate_python(float("nan"))


def test_script_generation_enforces_the_same_validation_gate_as_plan() -> None:
    spec = build_ngsolve_validation_spec(
        goal="invalid thermal input", total_loss_w=0, cooling_h_w_m2k=0
    )
    with pytest.raises(ValueError, match="failed"):
        build_ngsolve_validation_script(spec, lane="thermal")


def test_legacy_deck_index_is_paginated_and_readiness_is_cached() -> None:
    text = elf_sample_decks_index(limit=7)
    assert text.startswith("# 7 of ")
    assert len(text.splitlines()) == 8
    assert build_mcp_readiness.cache_parameters() == {"maxsize": 1, "typed": False}
    overview = elf_overview()
    assert overview["n_resources"] == 4
    assert overview["n_resource_templates"] == 1


def test_solver_routing_keeps_electrostatics_distinct() -> None:
    assert FEATURE_ROUTES["stationary_eddy_current_and_shielding"] == ("magic",)
    assert FEATURE_ROUTES["moving_conductor_and_rotation"] == ("magic",)
    assert FEATURE_ROUTES["electrostatic_and_dielectric_fields"] == ("elfin",)
    assert "electrostatic" in new_elf_analysis("capacitor", "ELFIN")


def test_wheel_audit_rejects_product_dump_even_when_named_json(tmp_path) -> None:
    wheel = tmp_path / "unsafe.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("elf_mcp_server/help_dump.json", "{}")
    issues = audit_wheel(wheel)
    assert any("product-derived dump" in issue for issue in issues)


def test_wheel_audit_rejects_bundled_product_dll(tmp_path) -> None:
    wheel = tmp_path / "unsafe-binary.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("elf_mcp_server/magh1600.dll", b"MZ")
    issues = audit_wheel(wheel)
    assert any("product/runtime binary" in issue for issue in issues)


def test_wheel_audit_does_not_flag_its_own_marker_dictionary(tmp_path) -> None:
    wheel = tmp_path / "safe.whl"
    required = (
        "runtime.py",
        "handlers.py",
        "tool_definitions.py",
        "mcp_resources.py",
        "models.py",
        "product_runner.py",
        "_product_worker.py",
    )
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("elf_mcp_server/THIRD_PARTY_NOTICES.md", "public notice")
        marker = "S:" + "/"
        archive.writestr("elf_mcp_server/policy_lint.py", f'MARKERS = ("{marker}",)')
        for name in required:
            archive.writestr(f"elf_mcp_server/{name}", "# public module")
    assert audit_wheel(wheel) == []


def test_deck_content_digest_is_cross_platform_line_ending_stable(tmp_path) -> None:
    lf_root = tmp_path / "lf"
    crlf_root = tmp_path / "crlf"
    lf_root.mkdir()
    crlf_root.mkdir()
    lf_file = lf_root / "case.mai"
    crlf_file = crlf_root / "case.mai"
    lf_file.write_bytes(b"USE MAGIC\nSOL MOME\nEND\n")
    crlf_file.write_bytes(b"USE MAGIC\r\nSOL MOME\r\nEND\r\n")
    assert _content_digest([lf_file], lf_root) == _content_digest([crlf_file], crlf_root)
