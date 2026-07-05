# -*- coding: utf-8 -*-
"""Smoke tests for the public ELF doc-server (ELF-mcp-server).

Minimal guards for a public package: the server imports, the four bundled
vendor-doc dumps load, the tool surface is the expected size, and the removed
work-examples family stays OUT (publish-boundary regression guard).
"""
import os
import sys
import asyncio
import json
import math
import tomllib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_server_imports():
    import elf_mcp_server
    from elf_mcp_server import server

    assert server.mcp is not None
    pyproject = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    with open(pyproject, "rb") as f:
        project = tomllib.load(f)["project"]
    assert elf_mcp_server.__version__ == project["version"]


def test_doc_dumps_load():
    from elf_mcp_server.help_access import list_help_files
    from elf_mcp_server.examples_access import list_examples
    from elf_mcp_server.wiki_access import list_wiki_pages
    from elf_mcp_server.python_access import list_python_files
    assert len(list_help_files()) > 1000
    assert len(list_examples()) > 300
    assert len(list_wiki_pages()) > 50
    assert len(list_python_files()) > 5


def test_100_example_playbook_cards_public_safe():
    from elf_mcp_server.example_playbook import build_example_cards, format_example_cards
    cards = build_example_cards(limit=100)
    assert len(cards) == 100
    assert sum(1 for c in cards if c["solver"] == "MAGIC") == 97
    text = format_example_cards(cards)
    assert "magic/IPM/Motor1.mai" in text
    assert "flux-linkage" in text
    assert "maxwell-force" in text
    assert "C:\\" not in text
    assert "_cross" + "val" not in text


def test_tool_surface_and_no_work_family():
    from elf_mcp_server.server import mcp, elf_overview
    tools = asyncio.run(mcp.list_tools())
    names = [t.name for t in tools]
    assert len(names) >= 25
    assert "elf_examples_playbook" in names
    assert "elf_recipe_search" in names
    assert "elf_recipe_get" in names
    assert "elf_plan_workflow" in names
    assert "elf_mcp_readiness" in names
    assert "elf_motor_readiness" in names
    assert "elf_motor_hybrid_router" in names
    assert "elf_motor_mmm_quick_check" in names
    assert "elf_sample_decks_index" in names
    assert "elf_sample_decks_get" in names
    assert "elf_sample_decks_route" in names
    assert "elf_sample_decks_playbook" in names
    assert "elf_sample_decks_validation" in names
    assert "elf_sample_decks_representatives" in names
    assert "elf_sample_decks_quality" in names
    assert "elf_sample_decks_physics" in names
    assert "elf_sample_decks_validation_matrix" in names
    assert "elf_sample_decks_observable_contracts" in names
    assert "elf_sample_decks_cross_validation" in names
    assert "elf_sample_decks_duplicates" in names
    assert "elf_local_simulation_handoff" in names
    assert "elf_public_promotion" in names
    assert "elf_python_team28" in names
    assert "elf_python_interface_design" in names
    assert "elf_python_api_manual" in names
    assert "elf_python_api_schema" in names
    assert "elf_python_motor_spec_lint" in names
    assert "elf_python_deck_lint" in names
    assert "elf_python_pm_demag_step_lint" in names
    assert "elf_python_run_contract" in names
    assert "elf_python_motor_design_plan" in names
    assert "elf_python_motor_sweep_matrix" in names
    assert "elf_python_motor_dq_axis_map_plan" in names
    assert "elf_python_motor_mtpa_search_plan" in names
    assert "elf_python_reluctance_motor_design_plan" in names
    assert "elf_python_motor_winding_layout_plan" in names
    assert "elf_python_motor_topology_parameter_plan" in names
    assert "elf_python_motor_demag_margin_plan" in names
    assert "elf_python_motor_drive_cycle_plan" in names
    assert "elf_python_motor_optimization_study_plan" in names
    assert "elf_python_motor_voltage_field_weakening_plan" in names
    assert "elf_python_motor_cogging_ripple_plan" in names
    assert "elf_python_motor_airgap_harmonics_nvh_plan" in names
    assert "elf_python_motor_thermal_network_plan" in names
    assert "elf_python_motor_manufacturing_tolerance_plan" in names
    assert "elf_python_motor_material_variation_plan" in names
    assert "elf_python_motor_feasibility_study" in names
    assert "elf_python_run_result_parse" in names
    assert "elf_python_run_result_parse_path" in names
    assert "elf_python_motor_optimization_loop" in names
    assert "elf_python_motor_ngsolve_result_crosscheck" in names
    assert "elf_python_motor_drawing_bom_handoff" in names
    assert "elf_python_motor_operating_point_run_queue" in names
    assert "elf_python_motor_inverter_pwm_harmonic_plan" in names
    assert "elf_python_motor_saturation_inductance_map_plan" in names
    assert "elf_python_motor_rotor_stress_retention_plan" in names
    assert "elf_python_motor_validation_scorecard" in names
    assert "elf_python_motor_efficiency_map_plan" in names
    assert "elf_python_motor_efficiency_map_from_results" in names
    assert "elf_python_motor_loss_model_contract" in names
    assert "elf_python_motor_torque_speed_envelope" in names
    assert "elf_python_induction_slip_sweep_plan" in names
    assert "elf_python_motor_observable_contract" in names
    assert "elf_python_motor_market_brief" in names
    assert "elf_python_motor_design_agent_handoff" in names
    assert "elf_python_ngsolve_validation_plan" in names
    assert "elf_python_ngsolve_validation_script" in names
    assert "elf_python_meg_generation_plan" in names
    assert "elf_python_2d_motor_template" in names
    overview = elf_overview()
    overview_text = str(overview)
    assert overview["n_tools"] == 85
    assert "public_boundary" in overview
    assert "recommended_calls" in overview
    assert "elf_python_interface_design" in overview_text
    assert "COMSOL" not in overview_text
    assert "internal" + ":" not in overview_text
    assert "S:" + "\\" not in overview_text
    # publish boundary: the private work-examples corpus tools were removed and
    # must never come back into the public package. Public workflow planning is
    # allowed; private work-example corpus tools are not.
    forbidden = ("elf_work", "work_examples", "work_examples_", "elf_examples_work")
    assert not any(any(token in n for token in forbidden) for n in names), names


def test_python_interface_design_public_policy():
    from elf_mcp_server.python_interface_design import (
        build_python_interface_design,
        format_python_interface_design,
    )

    design = build_python_interface_design()
    text = format_python_interface_design(design)
    assert design["schema_version"] == "elf-python-interface-design/v1"
    assert "product_python_is_reference_not_required" in text
    assert "vendor_dll_is_immutable_boundary" in text
    assert "public_api_may_expand_above_product_python" in text
    assert "MotorSpec" in text
    assert "RunRequest / RunResult" in text
    assert "S:" + "\\" not in text
    assert "_cross" + "val" not in text


def test_python_facade_schema_lint_and_generation_plan(tmp_path):
    from elf_mcp_server.python_api_manual import build_python_api_manual, format_python_api_manual
    from elf_mcp_server.python_facade import (
        build_meg_generation_plan,
        build_induction_motor_slip_sweep_plan,
        build_motor_design_agent_handoff,
        build_motor_design_plan,
        build_motor_demag_margin_plan,
        build_motor_drive_cycle_plan,
        build_motor_dq_axis_map_plan,
            build_motor_efficiency_map_plan,
            build_motor_efficiency_map_from_results,
        build_motor_airgap_harmonics_nvh_plan,
        build_motor_cogging_ripple_plan,
        build_motor_feasibility_study,
        build_motor_loss_model_contract,
        build_motor_manufacturing_tolerance_plan,
        build_motor_market_brief,
        build_motor_material_variation_plan,
        build_motor_mtpa_search_plan,
        build_motor_ngsolve_result_crosscheck,
        build_motor_observable_contract,
        build_motor_operating_point_run_queue,
        build_motor_optimization_study_plan,
        build_motor_optimization_loop,
        build_motor_inverter_pwm_harmonic_plan,
        build_motor_saturation_inductance_map_plan,
        build_motor_rotor_stress_retention_plan,
        build_motor_spec_template,
        build_2d_motor_template,
        build_motor_sweep_matrix,
        build_motor_topology_parameter_plan,
        build_motor_torque_speed_envelope,
        build_motor_thermal_network_plan,
        build_motor_validation_scorecard,
        build_motor_voltage_field_weakening_plan,
        build_motor_winding_layout_plan,
        build_motor_drawing_bom_handoff,
        build_reluctance_motor_design_plan,
        build_run_request_contract,
            parse_run_result_payload,
            parse_run_result_path,
        format_motor_drawing_bom_handoff,
        format_pm_demag_step_lint,
        format_motor_demag_margin_plan,
        format_motor_drive_cycle_plan,
        format_induction_motor_slip_sweep_plan,
            format_motor_efficiency_map_plan,
            format_motor_efficiency_map_result,
        format_motor_airgap_harmonics_nvh_plan,
        format_motor_cogging_ripple_plan,
        format_motor_feasibility_study,
        format_motor_loss_model_contract,
        format_motor_manufacturing_tolerance_plan,
        format_motor_torque_speed_envelope,
        format_motor_dq_axis_map_plan,
        format_motor_mtpa_search_plan,
        format_motor_material_variation_plan,
        format_motor_observable_contract,
        format_motor_optimization_study_plan,
        format_motor_optimization_loop,
        format_motor_ngsolve_result_crosscheck,
        format_motor_topology_parameter_plan,
        format_motor_thermal_network_plan,
        format_motor_operating_point_run_queue,
        format_motor_inverter_pwm_harmonic_plan,
        format_motor_saturation_inductance_map_plan,
        format_motor_rotor_stress_retention_plan,
        format_motor_validation_scorecard,
        format_motor_voltage_field_weakening_plan,
        format_motor_winding_layout_plan,
            format_run_result_parse,
            format_run_result_path_parse,
        format_reluctance_motor_design_plan,
        lint_mai_text,
        lint_pm_demag_step_contract,
        MOTOR_TYPES,
        python_api_schema,
        validate_motor_spec_dict,
    )
    from elf_mcp_server.ngsolve_multiphysics import (
        build_ngsolve_validation_plan,
        build_ngsolve_validation_script,
        build_ngsolve_validation_spec,
        format_ngsolve_validation_plan,
        format_ngsolve_validation_script,
        validate_ngsolve_validation_spec,
    )
    from elf_mcp_server.sample_decks import get_sample_deck

    schema = python_api_schema()
    assert schema["policy"]["product_python_required"] is False
    assert schema["policy"]["product_python_role"] == "reference"
    assert schema["policy"]["vendor_dll_mutable_by_public_package"] is False
    assert schema["policy"]["public_facade_can_extend_api"] is True
    advanced_motor_types = [
        "pm_assisted_synrm",
        "bldc",
        "line_start_pm",
        "deep_bar_induction",
        "flux_switching_pm",
        "vernier_pm",
        "transverse_flux_pm",
        "slotless_pm",
        "claw_pole",
        "commutator_dc",
    ]
    for motor_type in advanced_motor_types:
        assert motor_type in MOTOR_TYPES
        assert motor_type in schema["enums"]["motor_types"]
        advanced_template = build_motor_spec_template(motor_type)
        assert advanced_template["motor_type"] == motor_type
        assert validate_motor_spec_dict(advanced_template)["status"] == "PASS"
        assert advanced_template["design_variables"]
        advanced_topology = build_motor_topology_parameter_plan(motor_type)
        assert advanced_topology["motor_type"] == motor_type
        assert len(advanced_topology["parameters"]) >= 7
        advanced_2d = build_2d_motor_template(motor_type, pole_pairs=4, stator_slots=48)
        assert advanced_2d["motor_type"] == motor_type
        assert advanced_2d["angular_features"]
        advanced_optimization = build_motor_optimization_study_plan(motor_type, budget=6)
        assert advanced_optimization["motor_type"] == motor_type
        assert advanced_optimization["design_variables"]
    assert build_motor_design_plan("six-step BLDC torque ripple")["motor_type"] == "bldc"
    assert build_motor_design_plan("line-start PM pull-in torque")["motor_type"] == "line_start_pm"
    assert build_motor_design_plan("deep-bar induction starting torque")["motor_type"] == "deep_bar_induction"

    template = build_motor_spec_template("ipm")
    lint = validate_motor_spec_dict(template)
    assert lint["status"] == "PASS"
    assert "ld_lq" in lint["recommended_observables"]

    deck = get_sample_deck("application/motor/pm_cosine_pickup_72/pm001/pm001.mai")
    deck_lint = lint_mai_text(deck["text"], ["flux_linkage", "back_emf_constant"])
    assert deck_lint["status"] == "PASS"
    assert deck_lint["detected"]["has_flum"] is True
    assert deck_lint["detected"]["has_hbrm"] is True
    assert deck_lint["detected"]["has_hbcn"] is True

    demag_lint = lint_pm_demag_step_contract(
        "\n".join(
            [
                "USE MAGIC 3.50",
                "PRE 3 2",
                "HBRM 1 1.05 1.20",
                "HBRM 2 1.05 1.00",
                "HBRM 3 1.05 0.90",
                "HBCN 7 0 1",
                "HBCN 7 1 2",
                "HBCN 7 2 3",
                "END",
                "SOL MOME",
                "END",
            ]
        )
    )
    assert demag_lint["status"] == "PASS"
    assert len(demag_lint["detected"]["hbrm_rows"]) == 3
    assert len(demag_lint["detected"]["hbcn_rows"]) == 3
    assert demag_lint["detected"]["complete_three_step_mids"] == [7]
    assert demag_lint["detected"]["missing_recoil_curves"] == []
    demag_lint_text = format_pm_demag_step_lint(demag_lint)
    assert "PM Demag Step Lint" in demag_lint_text
    assert "complete material ids: `7`" in demag_lint_text

    contract = build_run_request_contract(
        goal="SPM motor back EMF sweep",
        motor_type="spm",
        source_public_deck_path=deck["path"],
    )
    assert contract["run_request"]["privacy_policy"] == "keep_raw_outputs_user_local"
    assert contract["run_request"]["source_public_deck_paths"] == [deck["path"]]

    parsed_result = parse_run_result_payload(
        "torque_nm=0.82\nloss_w=12.5\nefficiency=0.91\nLd_h=0.001\nLq_h=0.0018",
        case_id="cand_a",
        motor_type="spm",
        requested_observables=["torque", "loss_proxy"],
    )
    assert parsed_result["schema_version"] == "elf-python-run-result-parse/v1"
    assert parsed_result["parsed_observables"]["torque_value"] == 0.82
    assert parsed_result["parsed_observables"]["loss_proxy_value"] == 12.5
    assert abs(parsed_result["parsed_observables"]["ld_lq_value"]["saliency_ratio"] - 1.8) < 1e-12
    parsed_text = format_run_result_parse(parsed_result)
    assert "RunResult Parser" in parsed_text
    assert "torque_value" in parsed_text

    force_result = parse_run_result_payload(
        {
            "case_id": "force_ref",
            "parsed_observables": {
                "force_x_n_per_m": -4.0e-4,
                "force_y_n_per_m": 0.0,
                "force_unit": "N/m",
                "quantity_dimension": "2d_per_length",
            },
        },
        motor_type="linear_pm",
        requested_observables=["force"],
    )
    assert force_result["parsed_observables"]["force_x_n_per_m"] == -4.0e-4
    assert force_result["parsed_observables"]["force_unit"] == "N/m"
    assert force_result["parsed_observables"]["quantity_dimension"] == "2d_per_length"
    assert force_result["status"] == "PASS"
    assert force_result["missing_requested_observables"] == []
    assert force_result["force_metadata_checks"]["unit_dimension_consistent"] is True

    bad_force_result = parse_run_result_payload(
        {
            "case_id": "force_bad_unit",
            "parsed_observables": {
                "force_x_n_per_m": -4.0e-4,
                "force_unit": "N",
                "quantity_dimension": "2d_per_length",
            },
        },
        motor_type="linear_pm",
        requested_observables=["force"],
    )
    assert bad_force_result["status"] == "WARN"
    assert bad_force_result["force_metadata_checks"]["unit_dimension_consistent"] is False
    assert any("does not match quantity_dimension" in item for item in bad_force_result["warnings"])

    run_dir = tmp_path / "completed_run"
    run_dir.mkdir()
    result_csv = run_dir / "map_results.csv"
    result_csv.write_text(
        "\n".join(
            [
                "point_id,speed_rpm,requested_torque_nm,torque_nm,loss_w,voltage_margin_v,current_margin_a",
                "s00_t00,1000,0.1,0.1,1.0,12.0,5.0",
                "s00_t01,1000,0.2,0.2,2.0,10.0,4.0",
                "s01_t00,2000,0.1,0.1,1.5,9.0,3.5",
                "s01_t01,2000,0.2,0.2,4.0,8.0,2.5",
            ]
        ),
        encoding="utf-8",
    )
    result_mah = run_dir / "case_summary.mah"
    result_mah.write_text(
        "\n".join(
            [
                "case_id mah_summary",
                "point_id s01_t00",
                "speed_rpm 2000",
                "requested_torque_nm 0.1",
                "torque_nm 0.1",
                "copper_loss_w 1.0",
                "iron_loss_w 0.5",
            ]
        ),
        encoding="utf-8",
    )
    result_maf = run_dir / "force_table.maf"
    result_maf.write_text(
        "\n".join(
            [
                "case_id point_id speed_rpm requested_torque_nm torque_z_nm loss_total_w force_x_n",
                "maf_summary s00_t01 1000 0.2 0.2 2.0 0.0",
            ]
        ),
        encoding="utf-8",
    )
    parsed_path = parse_run_result_path(
        str(run_dir),
        motor_type="spm",
        requested_observables=["torque", "loss_proxy"],
    )
    assert parsed_path["schema_version"] == "elf-python-run-result-path-parse/v1"
    assert parsed_path["status"] == "PASS"
    assert set(parsed_path["files_scanned"]) == {"case_summary.mah", "force_table.maf", "map_results.csv"}
    assert len(parsed_path["parsed_results"]) == 6
    assert "torque_value" in parsed_path["combined_observables"]
    assert any(result["case_id"] == "mah_summary" for result in parsed_path["parsed_results"])
    assert any(result["case_id"] == "maf_summary" for result in parsed_path["parsed_results"])
    parsed_path_text = format_run_result_path_parse(parsed_path)
    assert "RunResult Path Parser" in parsed_path_text
    assert "map_results.csv" in parsed_path_text
    assert "case_summary.mah" in parsed_path_text
    assert "force_table.maf" in parsed_path_text
    assert str(run_dir) not in parsed_path_text

    secret_json = tmp_path / "not_a_run_result.json"
    secret_json.write_text(
        json.dumps({"api_token": "SHOULD_NOT_LEAK", "torque_nm": 1.23}),
        encoding="utf-8",
    )
    secret_path = parse_run_result_path(str(secret_json), motor_type="spm")
    secret_text = format_run_result_path_parse(secret_path)
    assert secret_path["combined_observables"] == {}
    assert secret_path["parsed_results"] == []
    assert secret_path["status"] == "WARN"
    assert "api_token" not in str(secret_path)
    assert "SHOULD_NOT_LEAK" not in str(secret_path)
    assert "api_token" not in secret_text
    assert "SHOULD_NOT_LEAK" not in secret_text
    assert "ignored JSON file without RunResult schema" in secret_text

    numeric_map = build_motor_efficiency_map_from_results(
        "spm",
        result_payloads=parsed_path,
        torque_min_nm=0.1,
        torque_max_nm=0.2,
        torque_points=2,
        speed_min_rpm=1000,
        speed_max_rpm=2000,
        speed_points=2,
        base_speed_rpm=2000,
    )
    assert numeric_map["schema_version"] == "elf-python-motor-efficiency-map-result/v1"
    assert numeric_map["status"] == "PASS"
    assert numeric_map["coverage"]["filled_points"] == 4
    assert numeric_map["eta_grid"][0][0] is not None
    assert numeric_map["total_loss_w_grid"][1][1] == 4.0
    assert numeric_map["best_efficiency_point"]["efficiency"] is not None
    assert all(gate["status"] == "PASS" for gate in numeric_map["quality_gate_results"])
    assert {gate["gate"] for gate in numeric_map["quality_gate_results"]} >= {
        "coverage_fraction",
        "feasible_region_coverage",
        "efficiency_range_0_to_1",
        "loss_nonnegative",
        "torque_error_within_limit",
        "voltage_margin_nonnegative_when_present",
    }
    assert any(point["voltage_margin_v"] == 12.0 for point in numeric_map["result_points"])
    assert any(point["current_margin_a"] == 5.0 for point in numeric_map["result_points"])
    numeric_map_text = format_motor_efficiency_map_result(numeric_map)
    assert "Motor Efficiency Map Result" in numeric_map_text
    assert "Eta Grid" in numeric_map_text
    assert "voltage margin" in numeric_map_text
    assert "Quality Gate Results" in numeric_map_text

    omega_1000 = 2.0 * math.pi * 1000.0 / 60.0
    p_out = 0.2 * omega_1000
    loss_bucket_map = build_motor_efficiency_map_from_results(
        "spm",
        result_payloads=[
            {
                "schema_version": "elf-python-run-result-parse/v1",
                "case_id": "loss_bucket",
                "status": "PASS",
                "parsed_observables": {
                    "point_id": "s00_t00",
                    "speed_rpm": 1000,
                    "requested_torque_nm": 0.2,
                    "torque_value": 0.2,
                    "input_power_w": p_out + 4.0,
                    "copper_loss_w": 2.0,
                    "iron_loss_w": 1.0,
                    "magnet_loss_w": 0.4,
                    "mechanical_loss_w": 0.6,
                },
                "missing_requested_observables": [],
            }
        ],
        torque_min_nm=0.2,
        torque_max_nm=0.2,
        torque_points=1,
        speed_min_rpm=1000,
        speed_max_rpm=1000,
        speed_points=1,
        base_speed_rpm=1000,
    )
    loss_cell = loss_bucket_map["result_points"][0]
    assert loss_bucket_map["status"] == "PASS"
    assert loss_cell["total_loss_w"] == 4.0
    assert loss_cell["loss_source"] == "summed_loss_terms"
    assert loss_cell["loss_terms_w"]["copper_loss_w"] == 2.0
    assert loss_cell["dominant_loss_term"] == "copper_loss_w"
    assert loss_cell["loss_bucket_balance_rel_error"] == 0.0
    assert loss_cell["input_power_balance_rel_error"] == 0.0

    negative_voltage_margin_map = build_motor_efficiency_map_from_results(
        "spm",
        result_payloads=[
            {
                "case_id": "negative_voltage_margin",
                "status": "PASS",
                "parsed_observables": {
                    "point_id": "s00_t00",
                    "speed_rpm": 1000,
                    "requested_torque_nm": 0.2,
                    "torque_nm": 0.2,
                    "loss_w": 2.0,
                    "voltage_margin_v": -0.25,
                },
            }
        ],
        torque_min_nm=0.2,
        torque_max_nm=0.2,
        torque_points=1,
        speed_min_rpm=1000,
        speed_max_rpm=1000,
        speed_points=1,
        base_speed_rpm=1000,
    )
    negative_voltage_gates = {
        gate["gate"]: gate["status"] for gate in negative_voltage_margin_map["quality_gate_results"]
    }
    assert negative_voltage_margin_map["status"] == "WARN"
    assert negative_voltage_gates["voltage_margin_nonnegative_when_present"] == "WARN"
    assert negative_voltage_margin_map["result_points"][0]["voltage_margin_v"] == -0.25

    bad_map = build_motor_efficiency_map_from_results(
        "spm",
        result_payloads=[
            {
                "case_id": "bad_torque",
                "status": "PASS",
                "parsed_observables": {
                    "point_id": "s00_t00",
                    "speed_rpm": 1000,
                    "requested_torque_nm": 0.1,
                    "torque_nm": 0.4,
                    "efficiency": 0.9,
                },
            }
        ],
        torque_min_nm=0.1,
        torque_max_nm=0.2,
        torque_points=2,
        speed_min_rpm=1000,
        speed_max_rpm=2000,
        speed_points=2,
        base_speed_rpm=2000,
        max_abs_torque_error_nm=0.01,
    )
    assert bad_map["status"] == "FAIL"
    gate_status = {gate["gate"]: gate["status"] for gate in bad_map["quality_gate_results"]}
    assert gate_status["coverage_fraction"] == "FAIL"
    assert gate_status["loss_nonnegative"] == "FAIL"
    assert gate_status["torque_error_within_limit"] == "FAIL"

    design_plan = build_motor_design_plan("IPM torque density and Ld Lq", motor_type="ipm")
    assert design_plan["motor_type"] == "ipm"
    assert design_plan["objective"] == "torque_density"
    assert any(var["name"] == "magnet_v_angle_deg" for var in design_plan["design_variables"])
    assert "dq_inductance" in design_plan["recommended_studies"]

    sweep = build_motor_sweep_matrix("spm", objective="back_emf_target", budget=7)
    assert sweep["motor_type"] == "spm"
    assert sweep["objective"] == "back_emf_target"
    assert len(sweep["rows"]) == 7
    assert any(var["name"] == "magnet_arc_fraction" for var in sweep["active_variables"])
    assert "back_emf_constant" in sweep["observables"]

    dq_map = build_motor_dq_axis_map_plan("ipm", pole_pairs=4, current_limit_a_peak=40, id_points=3, iq_points=3)
    assert dq_map["schema_version"] == "elf-python-motor-dq-axis-map-plan/v1"
    assert dq_map["dq_parameters"]["torque_formula"] == "T = 1.5*p*(psi_pm*Iq + (Ld-Lq)*Id*Iq)"
    assert len(dq_map["operating_points"]) == 9
    assert any(point["reluctance_torque_nm_proxy"] > 0 for point in dq_map["operating_points"])
    dq_text = format_motor_dq_axis_map_plan(dq_map)
    assert "PM and reluctance torque" in dq_text
    assert "flux_d_wb" in dq_text

    mtpa = build_motor_mtpa_search_plan("ipm", pole_pairs=4, current_limit_a_peak=40, angle_points=9)
    assert mtpa["schema_version"] == "elf-python-motor-mtpa-search-plan/v1"
    assert "best_proxy_point" in mtpa
    assert "reluctance_torque_nm_proxy" in mtpa["rows"][0]
    mtpa_text = format_motor_mtpa_search_plan(mtpa)
    assert "MTPA" in mtpa_text
    assert "torque-per-amp" in mtpa_text

    reluctance = build_reluctance_motor_design_plan("synrm", pole_pairs=2, stator_slots=36)
    assert reluctance["schema_version"] == "elf-python-reluctance-motor-design-plan/v1"
    assert reluctance["motor_type"] == "synrm"
    assert "dq_inductance" in reluctance["recommended_studies"]
    assert reluctance["dq_axis_map_plan"]["dq_parameters"]["pm_flux_wb"] == 0.0
    assert "aligned_unaligned_inductance_checks" in reluctance
    rel_text = format_reluctance_motor_design_plan(reluctance)
    assert "Reluctance Motor Design Plan" in rel_text
    assert "Ld/Lq" in rel_text
    assert "Aligned / Unaligned" in rel_text

    winding = build_motor_winding_layout_plan(stator_slots=48, pole_pairs=4)
    assert winding["schema_version"] == "elf-python-motor-winding-layout-plan/v1"
    assert winding["slots_per_pole_per_phase"] == 2.0
    assert "fundamental_winding_factor_proxy" in winding["winding_factors"]
    assert len(winding["slot_table"]) == 48
    winding_text = format_motor_winding_layout_plan(winding)
    assert "Motor Winding Layout Plan" in winding_text
    assert "winding factor proxy" in winding_text

    topology = build_motor_topology_parameter_plan("ipm", rotor_topology="inner_rotor")
    assert topology["schema_version"] == "elf-python-motor-topology-parameter-plan/v1"
    assert topology["motor_type"] == "ipm"
    assert any(var["name"] == "bridge_thickness_mm" for var in topology["parameters"])
    assert any(var["name"] == "magnet_v_angle_deg" for var in topology["parameters"])
    topology_text = format_motor_topology_parameter_plan(topology)
    assert "Topology Parameter Plan" in topology_text
    assert "Geometry Regions" in topology_text

    demag = build_motor_demag_margin_plan("spm", temperature_c=120)
    assert demag["schema_version"] == "elf-python-motor-demag-margin-plan/v1"
    assert demag["risk_label"] in {"green", "amber", "red"}
    assert "br_hot_t_proxy" in demag
    assert demag["hcj_hot_ka_m"] == 495.00000000000006
    assert demag["loadline_summary"]["first_unsafe_gap_m"] == 0.008
    assert demag["loadline_summary"]["safe_prefix_count"] == 4
    assert demag["loadline_summary"]["largest_safe_gap_m"] == 0.004
    assert demag["loadline_summary"]["risk_label"] == "red"
    assert demag["loadline_summary"]["risk_summary"]["schema_version"] == "elf-python-pm-loadline-risk-summary/v1"
    assert demag["loadline_summary"]["minimum_demag_margin_A_per_m"] < 0.0
    assert all(demag["loadline_summary"]["checks"].values())
    assert [row["safe_against_knee"] for row in demag["loadline_sweep"]] == [True, True, True, True, False]
    assert demag["elf_step_contract"]["schema_version"] == "elf-python-pm-demag-hbrm-hbcn-contract/v1"
    assert demag["elf_step_contract"]["lint_tool"] == "elf_python_pm_demag_step_lint"
    assert demag["elf_step_contract"]["required_hbcn_steps"] == [0, 1, 2]
    assert demag["elf_step_contract"]["metadata_gate"] == "pm_loadline_metadata_gate"
    assert demag["elf_step_contract"]["radia_ngsolve_gate"] == "pm_recoil_demag_step_summary"
    assert demag["elf_step_contract"]["loadline_gate"] == "pm_temperature_demag_sweep_summary"
    assert "step1_H_A_per_m" in demag["elf_step_contract"]["recommended_observable_keys"]
    assert "recoil_remanence_ratio_proxy" in demag["elf_step_contract"]["recommended_observable_keys"]
    assert demag["elf_step_contract"]["slot46_reference"]["first_unsafe_gap_m"] == 0.008
    assert demag["elf_step_contract"]["slot46_reference"]["safe_prefix_count"] == 4
    assert demag["elf_step_contract"]["slot102_reference"]["irreversible_demag"] is True
    assert demag["elf_step_contract"]["slot102_reference"]["recoil_remanence_ratio_proxy"] == 0.8
    assert demag["fault_current_screening"]["schema_version"] == "elf-python-motor-fault-current-demag-screening/v1"
    assert demag["fault_current_screening"]["negative_id_is_demag_direction"] is True
    assert "short_circuit_operating_point" in demag["fault_current_screening"]["recommended_radia_ngsolve_gates"]
    assert "field_weakening_speed_capability" in demag["fault_current_screening"]["recommended_radia_ngsolve_gates"]
    assert "pm_recoil_demag_step_summary" in demag["fault_current_screening"]["recommended_radia_ngsolve_gates"]
    assert "d_axis_demag_fraction" in demag["fault_current_screening"]["recommended_observable_keys"]
    assert "field_probe" in demag["fault_current_screening"]["recommended_observable_keys"]
    assert "recoil_remanence_ratio_proxy" in demag["fault_current_screening"]["recommended_observable_keys"]
    assert demag["bem_source_balance_contract"]["schema_version"] == "elf-python-pm-bem-source-balance-contract/v1"
    assert demag["bem_source_balance_contract"]["metadata_gate"] == "pm_bem_surface_normal_metadata_gate"
    assert demag["bem_source_balance_contract"]["balance_gate"] == "pm_bem_surface_source_balance_gate"
    assert demag["bem_source_balance_contract"]["signed_charge_proxy"] == "sum_i area_i * dot(M_i, n_i)"
    assert demag["bem_source_balance_contract"]["expected_normal_convention"] == "outward_from_magnet"
    assert demag["bem_source_balance_contract"]["source_convention"] == "sigma_m_equals_m_dot_n"
    assert demag["bem_source_balance_contract"]["source_balance_unit"] == "area_weighted_m_dot_n"
    assert demag["bem_source_balance_contract"]["signed_charge_balance_rel_tol"] == 1.0e-9
    assert "normal_unit_vector" in demag["bem_source_balance_contract"]["required_row_keys"]
    assert "surface_source_artifact_id" in demag["bem_source_balance_contract"]["required_row_keys"]
    assert "magnetization_source_id" in demag["bem_source_balance_contract"]["required_row_keys"]
    assert "material_id" in demag["bem_source_balance_contract"]["required_row_keys"]
    assert "material_name" in demag["bem_source_balance_contract"]["required_row_keys"]
    assert "surface_mesh_id" in demag["bem_source_balance_contract"]["required_summary_keys"]
    assert "surface_mesh_digest" in demag["bem_source_balance_contract"]["required_summary_keys"]
    assert "surface_row_count" in demag["bem_source_balance_contract"]["required_summary_keys"]
    assert "source_balance_artifact_id" in demag["bem_source_balance_contract"]["required_summary_keys"]
    assert "source_balance_digest" in demag["bem_source_balance_contract"]["required_summary_keys"]
    assert "source_convention" in demag["bem_source_balance_contract"]["required_summary_keys"]
    assert "expected_surface_source_artifact_id" in demag["bem_source_balance_contract"]["required_summary_keys"]
    assert "expected_magnetization_source_id" in demag["bem_source_balance_contract"]["required_summary_keys"]
    assert "expected_material_id" in demag["bem_source_balance_contract"]["required_summary_keys"]
    assert "expected_material_name" in demag["bem_source_balance_contract"]["required_summary_keys"]
    assert "total_area_m2" in demag["bem_source_balance_contract"]["required_summary_keys"]
    assert "source_balance_unit" in demag["bem_source_balance_contract"]["required_summary_keys"]
    assert "open surface" in demag["bem_source_balance_contract"]["negative_controls"]
    assert "normal_convention not outward_from_magnet" in demag["bem_source_balance_contract"]["negative_controls"]
    assert "stale surface_mesh_digest" in demag["bem_source_balance_contract"]["negative_controls"]
    assert "wrong surface_row_count" in demag["bem_source_balance_contract"]["negative_controls"]
    assert "stale source_balance_digest" in demag["bem_source_balance_contract"]["negative_controls"]
    assert "wrong source_convention" in demag["bem_source_balance_contract"]["negative_controls"]
    assert "stale surface_source_artifact_id" in demag["bem_source_balance_contract"]["negative_controls"]
    assert "missing magnetization_source_id" in demag["bem_source_balance_contract"]["negative_controls"]
    assert "stale material_name" in demag["bem_source_balance_contract"]["negative_controls"]
    assert "missing total_area_m2" in demag["bem_source_balance_contract"]["negative_controls"]
    assert demag["run_result_loadline_handoff"]["schema_version"] == "elf-python-run-result-loadline-handoff/v1"
    assert demag["run_result_loadline_handoff"]["row_identity"] == "case_id"
    assert "elf_python_run_result_parse_path" in demag["run_result_loadline_handoff"]["parser_tools"]
    assert "H_pm_A_per_m" in demag["run_result_loadline_handoff"]["required_normalized_columns"]
    assert demag["run_result_loadline_handoff"]["metadata_gate"] == "pm_loadline_metadata_gate"
    assert demag["run_result_loadline_handoff"]["loadline_gate"] == "pm_temperature_demag_sweep_summary"
    assert demag["run_result_loadline_handoff"]["recoil_step_gate"] == "pm_recoil_demag_step_summary"
    assert "missing case_id" in demag["run_result_loadline_handoff"]["negative_controls"]
    assert "wrong h_field_unit" in demag["run_result_loadline_handoff"]["negative_controls"]
    assert demag["demag_package_handoff"]["schema_version"] == "elf-python-demag-package-handoff/v1"
    assert demag["demag_package_handoff"]["package_gate"] == "pm_demag_package_identity_gate"
    assert demag["demag_package_handoff"]["row_identity"] == ["case_id", "magnet_id"]
    assert demag["demag_package_handoff"]["required_artifacts"] == [
        "run_result",
        "loadline_metadata",
        "bem_surface",
        "recoil_steps",
    ]
    assert "H_knee_A_per_m" in demag["demag_package_handoff"]["required_run_result_columns"]
    assert demag["demag_package_handoff"]["source_gates"]["run_result"] == "elf_python_run_result_parse_path"
    assert demag["demag_package_handoff"]["source_gates"]["recoil_steps"] == "pm_recoil_demag_three_step_gate"
    assert "stale magnet_id" in demag["demag_package_handoff"]["negative_controls"]
    assert "recoil steps missing step 2" in demag["demag_package_handoff"]["negative_controls"]
    assert demag["demag_margin_screening_package"]["schema_version"] == "elf-python-demag-margin-screening-package/v1"
    assert demag["demag_margin_screening_package"]["package_gate"] == "pm_demag_margin_screening_package_gate"
    assert demag["demag_margin_screening_package"]["manifest_gate"] == "pm_demag_margin_screening_package_gate"
    assert demag["demag_margin_screening_package"]["row_identity"] == ["case_id", "magnet_id", "temperature_C"]
    assert demag["demag_margin_screening_package"]["step_identity_keys"] == [
        "load_step_id",
        "fault_step_id",
        "demag_step_id",
    ]
    assert "HBRM/HBCN demag evaluation" in demag["demag_margin_screening_package"]["step_identity_contract"]
    assert "stale solver step" in demag["demag_margin_screening_package"]["step_identity_contract"]
    assert demag["demag_margin_screening_package"]["required_artifacts"] == [
        "loadline_sweep",
        "fault_current_screening",
        "bem_source_balance",
        "demag_package",
    ]
    assert demag["demag_margin_screening_package"]["source_gates"]["demag_package"] == "pm_demag_package_identity_gate"
    assert demag["demag_margin_screening_package"]["bem_source_balance_identity_keys"] == [
        "source_balance_artifact_id",
        "source_balance_digest",
        "source_convention",
    ]
    assert "source-balance artifact id" in demag["demag_margin_screening_package"]["bem_source_balance_identity_contract"]
    assert "field_probe" in demag["demag_margin_screening_package"]["required_fault_observables"]
    assert demag["demag_margin_screening_package"]["field_probe_identity_keys"] == [
        "field_probe_id",
        "field_probe_family",
        "observation_region_id",
        "field_probe_geometry_digest",
        "field_probe_point_xyz_m",
        "observation_component",
        "field_axis_convention",
        "field_sign_convention",
        "field_probe_method",
        "averaging_rule",
    ]
    assert "demag-axis field component" in demag["demag_margin_screening_package"]["field_probe_identity_contract"]
    assert "probe geometry digest" in demag["demag_margin_screening_package"]["field_probe_identity_contract"]
    assert "representative probe point" in demag["demag_margin_screening_package"]["field_probe_identity_contract"]
    assert "field-axis convention" in demag["demag_margin_screening_package"]["field_probe_identity_contract"]
    assert "sign convention" in demag["demag_margin_screening_package"]["field_probe_identity_contract"]
    assert "probe/export method" in demag["demag_margin_screening_package"]["field_probe_identity_contract"]
    assert demag["demag_margin_screening_package"]["field_probe_output_identity_keys"] == [
        "field_probe_output_artifact_id",
        "field_probe_output_digest",
        "field_probe_output_path",
    ]
    assert (
        "exported probe table/result artifact id"
        in demag["demag_margin_screening_package"]["field_probe_output_identity_contract"]
    )
    assert "total_area_m2" in demag["demag_margin_screening_package"]["required_bem_source_balance_summary_keys"]
    assert "surface_mesh_id" in demag["demag_margin_screening_package"]["required_bem_source_balance_summary_keys"]
    assert "surface_mesh_digest" in demag["demag_margin_screening_package"]["required_bem_source_balance_summary_keys"]
    assert "surface_row_count" in demag["demag_margin_screening_package"]["required_bem_source_balance_summary_keys"]
    assert "source_balance_artifact_id" in demag["demag_margin_screening_package"]["required_bem_source_balance_summary_keys"]
    assert "source_balance_digest" in demag["demag_margin_screening_package"]["required_bem_source_balance_summary_keys"]
    assert "source_convention" in demag["demag_margin_screening_package"]["required_bem_source_balance_summary_keys"]
    assert "expected_bem_normal_convention" in demag["demag_margin_screening_package"]["required_bem_source_balance_summary_keys"]
    assert "signed_charge_balance_abs" in demag["demag_margin_screening_package"]["required_bem_source_balance_summary_keys"]
    assert "stale temperature_C" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "stale field_probe_id" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "wrong field_probe_family" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "stale field_probe_geometry_digest" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "missing field_probe_point_xyz_m" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "wrong observation_component" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "wrong field_axis_convention" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "wrong field_probe_method" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "missing field_probe_method" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "wrong field_sign_convention" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "missing averaging_rule" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "stale field_probe_output_artifact_id" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "stale field_probe_output_digest" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "missing field_probe_output_path" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "stale fault_step_id" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "missing demag_step_id" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "stale magnet_id" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "missing BEM source unit" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "missing BEM surface mesh id" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "stale BEM surface mesh digest" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "wrong BEM surface row count" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "missing BEM source-balance artifact id" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "stale BEM source-balance digest" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "wrong BEM source convention" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "wrong BEM normal convention" in demag["demag_margin_screening_package"]["negative_controls"]
    assert demag["demag_margin_screening_package"]["slot166_reference"]["case_id"] == "demag_case_166"
    assert demag["demag_margin_screening_package"]["slot166_reference"]["magnet_id"] == "pm_spm_A"
    assert demag["demag_margin_screening_package"]["slot166_reference"]["radia_ngsolve_gate"] == "pm_demag_margin_screening_package_gate"
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["field_probe_id"]
        == "elf_slot286_field_probe_pm_spm_A_demag_axis_v1"
    )
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["source_balance_digest"]
        == "sha256:bem_source_balance_pm_spm_A_v1"
    )
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["surface_mesh_digest"]
        == "sha256:bem_surface_mesh_pm_spm_A_v1"
    )
    assert demag["demag_margin_screening_package"]["slot166_reference"]["surface_row_count"] == 6
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["source_convention"]
        == "sigma_m_equals_m_dot_n"
    )
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["field_probe_family"]
        == "elf_demag_margin_field_probe"
    )
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["field_probe_geometry_digest"]
        == "sha256:elf_slot326_field_probe_volume_pm_spm_A"
    )
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["field_probe_point_xyz_m"]
        == [0.028, 0.0, 0.0]
    )
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["observation_component"]
        == "H_parallel_demag_axis"
    )
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["field_axis_convention"]
        == "magnetization_axis_positive"
    )
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["field_sign_convention"]
        == "negative_h_parallel_is_demag"
    )
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"][
            "field_probe_output_artifact_id"
        ]
        == "elf_slot294_field_probe_table_pm_spm_A_v1"
    )
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"][
            "field_probe_output_digest"
        ]
        == "sha256:elf_slot294_field_probe_table_pm_spm_A"
    )
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["load_step_id"]
        == "elf_slot342_loadline_hot_120c_v1"
    )
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["fault_step_id"]
        == "elf_slot342_negative_id_fault_step_v1"
    )
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["demag_step_id"]
        == "elf_slot342_hbcn_demag_step2_v1"
    )
    assert demag["demag_margin_screening_package"]["material_state_keys"] == [
        "Br_T",
        "H_knee_A_per_m",
        "recoil_mu_r",
    ]
    assert demag["demag_margin_screening_package"]["material_state_identity_keys"] == [
        "material_state_artifact_id",
        "material_state_digest",
    ]
    assert "material-state tuple" in demag["demag_margin_screening_package"]["notebook_policy"]
    assert "material-state artifact id/digest" in demag["demag_margin_screening_package"]["notebook_policy"]
    assert "field-probe observation identity" in demag["demag_margin_screening_package"]["notebook_policy"]
    assert "field-probe geometry identity" in demag["demag_margin_screening_package"]["notebook_policy"]
    assert "field-probe output artifact identity" in demag["demag_margin_screening_package"]["notebook_policy"]
    assert "load/fault/demag step ids" in demag["demag_margin_screening_package"]["notebook_policy"]
    assert any("stale Br_T" in item for item in demag["demag_margin_screening_package"]["negative_controls"])
    assert "stale material_state_artifact_id" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "stale material_state_digest" in demag["demag_margin_screening_package"]["negative_controls"]
    assert "missing material_state_artifact_id" in demag["demag_margin_screening_package"]["negative_controls"]
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["material_state_artifact_id"]
        == "elf_slot334_pm_spm_A_hbrm_hbcn_state_v1.json"
    )
    assert (
        demag["demag_margin_screening_package"]["slot166_reference"]["material_state_digest"]
        == "sha256:elf_slot334_pm_spm_A_hbrm_hbcn_state_v1"
    )
    assert "loadline_checks" in demag
    assert any("pm_loadline_metadata_gate" in item for item in demag["loadline_checks"])
    assert any("pm_bem_surface_normal_metadata_gate" in item for item in demag["loadline_checks"])
    assert any("pm_bem_surface_source_balance_gate" in item for item in demag["loadline_checks"])
    assert any(
        "surface_mesh_id" in item
        and "surface_mesh_digest" in item
        and "source_balance_artifact_id" in item
        for item in demag["loadline_checks"]
    )
    assert any("surface_source_artifact_id" in item and "material_name" in item for item in demag["loadline_checks"])
    assert any("total_area_m2" in item and "source_balance_unit" in item for item in demag["loadline_checks"])
    assert any("permeance coefficient" in item for item in demag["loadline_checks"])
    assert any("HBRM/HBCN" in item for item in demag["loadline_checks"])
    assert any("Br_T" in item and "recoil_mu_r" in item for item in demag["loadline_checks"])
    assert any("field_probe_output_artifact_id" in item for item in demag["loadline_checks"])
    assert any("pm_recoil_demag_step_summary" in item for item in demag["loadline_checks"])
    assert any("negative-Id" in item for item in demag["loadline_checks"])
    assert any("surface source balance" in item for item in demag["quality_gates"])
    demag_text = format_motor_demag_margin_plan(demag)
    assert "Demag Margin Plan" in demag_text
    assert "field_probe" in demag_text
    assert "Load-Line Sweep" in demag_text
    assert "safe prefix count" in demag_text
    assert "load-line risk label" in demag_text
    assert "first unsafe gap" in demag_text
    assert "Load-Line Checks" in demag_text
    assert "ELF/MAGIC Step Contract" in demag_text
    assert "pm_loadline_metadata_gate" in demag_text
    assert "pm_bem_surface_normal_metadata_gate" in demag_text
    assert "HBRM role" in demag_text
    assert "HBCN role" in demag_text
    assert "pm_recoil_demag_step_summary" in demag_text
    assert "pm_temperature_demag_sweep_summary" in demag_text
    assert "recoil_remanence_ratio_proxy" in demag_text
    assert "Fault-Current Demag Screening" in demag_text
    assert "short_circuit_operating_point" in demag_text
    assert "PM BEM Source Balance Contract" in demag_text
    assert "pm_bem_surface_source_balance_gate" in demag_text
    assert "sum_i area_i * dot(M_i, n_i)" in demag_text
    assert "source balance unit" in demag_text
    assert "required summary keys" in demag_text
    assert "surface_source_artifact_id" in demag_text
    assert "magnetization_source_id" in demag_text
    assert "expected_material_name" in demag_text
    assert "total_area_m2" in demag_text
    assert "H_m=(B_gap-Br)/(mu0*mu_rec)" in demag_text
    assert "RunResult Load-Line Handoff" in demag_text
    assert "elf_python_run_result_parse_path" in demag_text
    assert "H_pm_A_per_m" in demag_text
    assert "missing case_id" in demag_text
    assert "Demag Package Handoff" in demag_text
    assert "pm_demag_package_identity_gate" in demag_text
    assert "magnet_id" in demag_text
    assert "recoil steps missing step 2" in demag_text
    assert "Demag Margin Screening Package" in demag_text
    assert "pm_demag_margin_screening_package_gate" in demag_text
    assert "fault_current_screening" in demag_text
    assert "field-probe identity keys" in demag_text
    assert "field_probe_id" in demag_text
    assert "observation_component" in demag_text
    assert "averaging_rule" in demag_text
    assert "demag-axis field component" in demag_text
    assert "field-probe output identity keys" in demag_text
    assert "field_probe_output_artifact_id" in demag_text
    assert "field_probe_output_digest" in demag_text
    assert "field_probe_output_path" in demag_text
    assert "step identity keys" in demag_text
    assert "load_step_id" in demag_text
    assert "fault_step_id" in demag_text
    assert "demag_step_id" in demag_text
    assert "stale solver step" in demag_text
    assert "required BEM source-balance summary keys" in demag_text
    assert "stale temperature_C" in demag_text
    assert "stale field_probe_id" in demag_text
    assert "missing averaging_rule" in demag_text
    assert "stale field_probe_output_artifact_id" in demag_text

    cycle = build_motor_drive_cycle_plan("robot_drone")
    assert cycle["schema_version"] == "elf-python-motor-drive-cycle-plan/v1"
    assert len(cycle["operating_points"]) == 4
    assert abs(sum(point["weight"] for point in cycle["operating_points"]) - 1.0) < 1.0e-12
    assert "cycle_efficiency" in cycle["weighted_outputs"]
    assert any("drive_cycle_weighted_efficiency_gate" in gate for gate in cycle["quality_gates"])
    cycle_text = format_motor_drive_cycle_plan(cycle)
    assert "Drive Cycle" in cycle_text
    assert "weighted_total_loss_w" in cycle_text

    optimization = build_motor_optimization_study_plan("spm", budget=24)
    assert optimization["schema_version"] == "elf-python-motor-optimization-study-plan/v1"
    assert optimization["budget"] == 24
    assert optimization["constraints"]
    assert "constraint_violation_count" in optimization["ranking_outputs"]
    optimization_text = format_motor_optimization_study_plan(optimization)
    assert "Optimization Study Plan" in optimization_text
    assert "build winding layout plan" in optimization_text

    loop = build_motor_optimization_loop(
        "spm",
        objective="cycle_efficiency",
        result_payloads=[
            {"case_id": "baseline", "status": "PASS", "parsed_observables": {"torque_nm": 0.7, "loss_w": 15, "efficiency": 0.88}},
            {"case_id": "candidate_hi", "status": "PASS", "parsed_observables": {"torque_nm": 0.82, "loss_w": 12, "efficiency": 0.92}},
        ],
        budget=4,
    )
    assert loop["schema_version"] == "elf-python-motor-optimization-loop/v1"
    assert loop["best_candidate"]["case_id"] == "candidate_hi"
    assert loop["loop_status"] in {"needs_more_runs", "ready_for_validation"}
    loop_text = format_motor_optimization_loop(loop)
    assert "Motor Optimization Loop" in loop_text
    assert "candidate_hi" in loop_text

    voltage_fw = build_motor_voltage_field_weakening_plan("ipm", dc_bus_v=48, speed_points=4)
    assert voltage_fw["schema_version"] == "elf-python-motor-voltage-field-weakening-plan/v1"
    assert len(voltage_fw["rows"]) == 4
    assert "required_negative_id_a_peak_proxy" in voltage_fw["rows"][-1]
    voltage_text = format_motor_voltage_field_weakening_plan(voltage_fw)
    assert "Voltage / Field-Weakening Plan" in voltage_text
    assert "voltage_margin" in str(voltage_fw)

    cogging = build_motor_cogging_ripple_plan("spm", stator_slots=48, pole_pairs=4)
    assert cogging["schema_version"] == "elf-python-motor-cogging-ripple-plan/v1"
    assert cogging["cogging_order_mechanical"] == 48
    assert "torque_ripple_percent" in cogging["parser_keys"]
    cogging_text = format_motor_cogging_ripple_plan(cogging)
    assert "Cogging / Ripple Plan" in cogging_text
    assert "harmonic orders" in cogging_text

    harmonics = build_motor_airgap_harmonics_nvh_plan("spm", stator_slots=48, pole_pairs=4)
    assert harmonics["schema_version"] == "elf-python-motor-airgap-harmonics-nvh-plan/v1"
    assert 48 in harmonics["mechanical_force_orders"]
    assert harmonics["speed_rows"][0]["slot_pass_frequency_hz"] > 0
    harmonics_text = format_motor_airgap_harmonics_nvh_plan(harmonics)
    assert "Airgap Harmonics / NVH Plan" in harmonics_text
    assert "NGSolve Follow-Up" in harmonics_text

    thermal = build_motor_thermal_network_plan(total_loss_w=25)
    assert thermal["schema_version"] == "elf-python-motor-thermal-network-plan/v1"
    assert sum(node["loss_w"] for node in thermal["nodes"]) == 25.0
    thermal_text = format_motor_thermal_network_plan(thermal)
    assert "Thermal Network Plan" in thermal_text
    assert "temperature" in thermal_text

    tolerance = build_motor_manufacturing_tolerance_plan("spm", airgap_mm=0.8)
    assert tolerance["schema_version"] == "elf-python-motor-manufacturing-tolerance-plan/v1"
    assert any(var["name"] == "eccentricity_mm" for var in tolerance["tolerance_variables"])
    assert len(tolerance["doe_rows"]) == 11
    tolerance_text = format_motor_manufacturing_tolerance_plan(tolerance)
    assert "Manufacturing Tolerance Plan" in tolerance_text
    assert "eccentricity_mm" in tolerance_text

    material = build_motor_material_variation_plan("spm", focus="magnet")
    assert material["schema_version"] == "elf-python-motor-material-variation/v1"
    assert material["focus"] == "magnet"
    assert any(var["name"] == "br_t" for var in material["variables"])
    material_text = format_motor_material_variation_plan(material)
    assert "Material Variation Plan" in material_text
    assert "magnet.br_t" in material_text

    feasibility = build_motor_feasibility_study("outer-rotor drone motor")
    assert feasibility["schema_version"] == "elf-python-motor-feasibility-study/v1"
    assert any(lane["lane"] == "thermal_feasibility" for lane in feasibility["lanes"])
    feasibility_text = format_motor_feasibility_study(feasibility)
    assert "Motor Feasibility Study" in feasibility_text
    assert "MCP Cannot Claim Alone" in feasibility_text

    ngsolve_runtime = {
        "schema_version": "elf-ngsolve-runtime-result/v1",
        "results": [
            {"lane": "thermal", "peak_temperature_c": 92.0, "temperature_rise_c": 67.0},
            {"lane": "nvh", "relative_order_separation": 0.25, "order_frequency_hz": 800.0},
            {"lane": "stress", "yield_margin_proxy": 2.1},
        ],
    }
    crosscheck = build_motor_ngsolve_result_crosscheck(parsed_result, ngsolve_runtime)
    assert crosscheck["schema_version"] == "elf-python-motor-ngsolve-crosscheck/v1"
    assert crosscheck["overall_status"] == "PASS"
    assert [lane["lane"] for lane in crosscheck["lane_checks"]] == ["thermal", "nvh", "stress"]
    crosscheck_text = format_motor_ngsolve_result_crosscheck(crosscheck)
    assert "NGSolve Result Crosscheck" in crosscheck_text
    assert "thermal" in crosscheck_text

    drawing_bom = build_motor_drawing_bom_handoff(
        "spm",
        rotor_topology="outer_rotor",
        stator_slots=48,
        pole_pairs=4,
        run_result_payload=parsed_result,
        validation_label="crosscheck_pass",
    )
    assert drawing_bom["schema_version"] == "elf-python-motor-drawing-bom-handoff/v1"
    assert any(item["item"] == "permanent_magnets" for item in drawing_bom["bom"])
    assert drawing_bom["attached_result_summary"]["status"] == "PASS"
    drawing_text = format_motor_drawing_bom_handoff(drawing_bom)
    assert "Drawing / BOM Handoff" in drawing_text
    assert "permanent_magnets" in drawing_text

    rotor_stress = build_motor_rotor_stress_retention_plan("spm", max_speed_rpm=12000)
    assert rotor_stress["schema_version"] == "elf-python-motor-rotor-stress-retention-plan/v1"
    assert rotor_stress["tip_speed_m_s"] > 0.0
    assert rotor_stress["risk_label"] in {"green", "amber", "red"}
    rotor_text = format_motor_rotor_stress_retention_plan(rotor_stress)
    assert "Rotor Stress / Retention Plan" in rotor_text
    assert "retention margin proxy" in rotor_text

    loss_contract = build_motor_loss_model_contract("induction")
    assert loss_contract["motor_type"] == "induction"
    assert any(term["name"] == "rotor_loss_w" for term in loss_contract["loss_terms"])
    assert "efficiency formula" in format_motor_loss_model_contract(loss_contract)

    envelope = build_motor_torque_speed_envelope(
        "spm",
        peak_torque_nm=1.2,
        base_speed_rpm=3000,
        max_speed_rpm=9000,
        speed_points=4,
    )
    assert envelope["rows"][0]["region"] == "constant_torque"
    assert envelope["rows"][-1]["region"] == "field_weakening_constant_power"
    assert "field_weakening" in format_motor_torque_speed_envelope(envelope)

    eff_map = build_motor_efficiency_map_plan(
        "spm",
        torque_min_nm=0.1,
        torque_max_nm=1.0,
        torque_points=3,
        speed_min_rpm=1000,
        speed_max_rpm=9000,
        speed_points=4,
        base_speed_rpm=3000,
    )
    assert eff_map["schema_version"] == "elf-python-motor-efficiency-map-plan/v1"
    assert len(eff_map["operating_points"]) == 12
    assert "eta_grid" in eff_map["postprocess_outputs"]
    assert any(not point["feasible_by_envelope"] for point in eff_map["operating_points"])
    eff_text = format_motor_efficiency_map_plan(eff_map)
    assert "ELF Python Motor Efficiency Map Plan" in eff_text
    assert "feasible points by envelope" in eff_text

    run_queue = build_motor_operating_point_run_queue(
        "spm",
        torque_points=2,
        speed_points=3,
        max_rows=6,
    )
    assert run_queue["schema_version"] == "elf-python-motor-operating-point-run-queue/v1"
    assert len(run_queue["run_rows"]) == 6
    assert run_queue["run_rows"][0]["case_id"] == "op_001"
    assert "torque_value" in run_queue["parser_keys"]
    run_queue_text = format_motor_operating_point_run_queue(run_queue)
    assert "Operating-Point Run Queue" in run_queue_text
    assert "op_001" in run_queue_text

    pwm_plan = build_motor_inverter_pwm_harmonic_plan(
        "spm",
        switching_frequency_hz=20000,
        fundamental_frequency_hz=400,
        max_sideband_order=2,
    )
    assert pwm_plan["schema_version"] == "elf-python-motor-inverter-pwm-harmonic-plan/v1"
    assert any(row["kind"] == "switching_sideband" for row in pwm_plan["harmonic_rows"])
    assert "magnet_loss_w" in pwm_plan["parser_keys"]
    pwm_text = format_motor_inverter_pwm_harmonic_plan(pwm_plan)
    assert "PWM Harmonic Plan" in pwm_text
    assert "magnet_loss_w" in pwm_text

    saturation_map = build_motor_saturation_inductance_map_plan(
        "ipm",
        current_points=2,
        angle_points=3,
    )
    assert saturation_map["schema_version"] == "elf-python-motor-saturation-inductance-map-plan/v1"
    assert len(saturation_map["map_rows"]) == 6
    assert saturation_map["map_rows"][0]["case_id"] == "sat_001"
    saturation_text = format_motor_saturation_inductance_map_plan(saturation_map)
    assert "Saturation Inductance Map Plan" in saturation_text
    assert "saliency" in saturation_text

    slip_plan = build_induction_motor_slip_sweep_plan(
        pole_pairs=2,
        supply_frequency_hz=50,
        slip_min=0.01,
        slip_max=0.05,
        slip_points=3,
    )
    assert slip_plan["motor_type"] == "induction"
    assert slip_plan["synchronous_speed_rpm"] == 1500.0
    assert slip_plan["operating_points"][0]["slip_frequency_hz"] == 0.5
    slip_text = format_induction_motor_slip_sweep_plan(slip_plan)
    assert "Induction Motor Slip Sweep" in slip_text
    assert "rotor_copper_loss_w = slip * airgap_power_w" in slip_text

    scorecard = build_motor_validation_scorecard(
        {
            "case_id": "cand_a",
            "status": "PASS",
            "parsed_observables": {
                "torque_nm": 0.82,
                "loss_w": 12.5,
                "efficiency": 0.91,
                "copper_loss_w": 7.0,
                "iron_loss_w": 3.0,
            },
        },
        ngsolve_runtime,
        drawing_bom_payload={"validation_label": "crosscheck_pass"},
    )
    assert scorecard["schema_version"] == "elf-python-motor-validation-scorecard/v1"
    assert scorecard["overall_status"] == "PASS"
    assert scorecard["promotion_decision"] == "promote_to_release_candidate"
    scorecard_text = format_motor_validation_scorecard(scorecard)
    assert "Validation Scorecard" in scorecard_text
    assert "loss_separation" in scorecard_text

    observable_contract = build_motor_observable_contract("ipm", "dq_inductance")
    assert observable_contract["study"] == "dq_inductance"
    assert "ld_lq" in observable_contract["observables"]
    assert "ld_lq_value" in observable_contract["parser_observable_keys"]
    assert "mtpa" in observable_contract["age_targets"]
    force_contract = build_motor_observable_contract("linear_pm", "force_gap_sweep")
    assert force_contract["study"] == "force_gap_sweep"
    assert "force" in force_contract["observables"]
    assert "force_value" in force_contract["parser_observable_keys"]
    assert "SOL FORC|SOL FORT|SOL FIXB" in force_contract["elf_markers"]["force"]
    assert force_contract["force_result_contract"]["schema_version"] == "elf-python-force-observable-package-contract/v1"
    assert "quantity_dimension" in force_contract["force_result_contract"]["required_metadata"]
    assert "result_set_id" in force_contract["force_result_contract"]["required_metadata"]
    assert "run_artifact_id" in force_contract["force_result_contract"]["required_metadata"]
    assert "result_revision_id" in force_contract["force_result_contract"]["required_metadata"]
    assert "observable_id" in force_contract["force_result_contract"]["required_metadata"]
    assert "N/m" in force_contract["force_result_contract"]["allowed_force_units"]
    assert "parallel_wire_force_result_package_gate" in force_contract["force_result_contract"]["public_gate_candidates"]
    assert "maxwell_stress_surface_package_gate" in force_contract["force_result_contract"]["public_gate_candidates"]
    assert "stale run_artifact_id or result_revision_id" in force_contract["force_result_contract"]["negative_controls"]
    assert "dipole-limit F*s^4 scaling when applicable" in force_contract["validation_checks"]
    assert "force quantity dimension declared before comparison" in force_contract["validation_checks"]
    assert "coaxial_pm_force_gap_sweep" in force_contract["age_targets"]
    force_contract_text = format_motor_observable_contract(force_contract)
    assert "Force Result Package" in force_contract_text
    assert "2d_per_length" in force_contract_text
    assert "parallel_wire_force_result_package_gate" in force_contract_text
    assert "maxwell_stress_surface_package_gate" in force_contract_text
    flux_contract = build_motor_observable_contract("spm", "static_flux_linkage")
    assert "mutual-flux sign and current-scaling gate" in flux_contract["validation_checks"]
    back_emf_contract = build_motor_observable_contract("spm", "back_emf_speed_sweep")
    assert "flux_linkage_back_emf_derivative_gate before Ke export" in back_emf_contract["validation_checks"]
    assert "flux_linkage_back_emf_derivative_gate" in back_emf_contract["age_targets"]
    assert "flux_linkage_back_emf_derivative_gate" in format_motor_observable_contract(back_emf_contract)

    market = build_motor_market_brief("robot_drone", "spm", "outer_rotor")
    assert market["target_market"] == "robot_drone"
    assert market["motor_type"] == "spm"
    assert market["rotor_topology"] == "outer_rotor"
    assert "continuous_torque_nm" in market["spec_intake_fields"]
    assert any("End users provide specifications" in item for item in market["user_experience_policy"])

    handoff = build_motor_design_agent_handoff(
        "outer-rotor drone SPM motor",
        target_market="robot_drone",
        motor_type="spm",
        rotor_topology="outer_rotor",
        continuous_torque_nm=0.8,
        base_speed_rpm=3500,
        dc_bus_v=48,
        outer_diameter_mm=80,
        stack_length_mm=20,
    )
    assert handoff["schema_version"] == "elf-python-motor-design-agent-handoff/v1"
    assert handoff["brief"]["target_market"] == "robot_drone"
    assert handoff["missing_spec_fields"] == []
    assert "ngsolve_multiphysics" in handoff["analysis_routing"]
    multiphysics = handoff["analysis_routing"]["ngsolve_multiphysics"]
    assert "required NGSolve" in multiphysics["nvh"]
    assert "required NGSolve" in multiphysics["thermal"]
    assert "required NGSolve" in multiphysics["stress"]
    assert "drawing_intent" in handoff["manufacturing_handoff"]

    ngsolve_spec = build_ngsolve_validation_spec(
        "outer-rotor drone SPM motor",
        lanes="all",
        motor_type="spm",
    )
    ngsolve_lint = validate_ngsolve_validation_spec(ngsolve_spec)
    assert ngsolve_lint["status"] == "PASS"
    assert ngsolve_lint["lanes"] == ["thermal", "nvh", "stress"]
    ngsolve_plan = build_ngsolve_validation_plan(ngsolve_spec)
    assert ngsolve_plan["status"] == "PASS"
    assert [job["lane"] for job in ngsolve_plan["jobs"]] == ["thermal", "nvh", "stress"]
    plan_text = format_ngsolve_validation_plan(ngsolve_plan)
    assert "H1 scalar heat equation" in plan_text
    assert "VectorH1 linear elasticity" in plan_text
    script_bundle = build_ngsolve_validation_script(ngsolve_spec, lane="all")
    assert script_bundle["lanes"] == ["thermal", "nvh", "stress"]
    assert "from ngsolve import *" in script_bundle["script"]
    assert "def run_thermal" in script_bundle["script"]
    assert "def run_nvh" in script_bundle["script"]
    assert "def run_stress" in script_bundle["script"]
    script_text = format_ngsolve_validation_script(script_bundle)
    assert "elf-ngsolve-runtime-result/v1" in script_text
    assert "S:" + "\\" not in script_text

    plan_2d = build_meg_generation_plan("2D SPM motor cross-section", dimension="2d")
    assert plan_2d["primary_strategy"] == "netgen_2d"
    assert "llm_2d_template" in plan_2d["alternative_strategies"]
    plan_3d = build_meg_generation_plan("3D WPT shielded coils", dimension="3d")
    assert plan_3d["primary_strategy"] == "cubit_mesh_export"

    template_2d = build_2d_motor_template("spm", pole_pairs=4, stator_slots=48)
    assert template_2d["schema_version"] == "elf-python-2d-motor-template/v1"
    assert template_2d["meg_generation_path"] == "llm_2d_template_then_netgen_2d_remesh"
    assert any(feature["name"] == "surface_pm_pole" for feature in template_2d["angular_features"])
    assert any("template is a draft" in rule for rule in template_2d["hard_validation_rules"])

    manual = format_python_api_manual(build_python_api_manual("quickstart"))
    assert "ELF/MAGIC Python Facade API Manual" in manual
    assert "LLM Call Order" in manual
    assert "elf_python_deck_lint" in manual
    assert "Cubit mesh export" in manual
    assert "Netgen 2D" in manual
    assert "Product-side Python is reference material" in manual
    assert "S:" + "\\" not in manual


def test_public_sample_decks_are_runnable_inputs_only():
    from elf_mcp_server.sample_decks import (
        build_sample_deck_cards,
        build_publication_batch_summary,
        build_cross_validation_summary,
        build_duplicate_audit,
        build_local_simulation_handoff,
        build_mcp_readiness,
        build_motor_hybrid_router,
        build_motor_mmm_quick_check,
        build_motor_readiness,
        build_quality_summary,
        build_observable_contract_summary,
        build_physical_quantity_summary,
        build_validation_matrix,
        build_representative_cards,
        build_team28_cards,
        build_validation_summary,
        format_public_promotion,
        format_cross_validation_summary,
        format_duplicate_audit,
        format_local_simulation_handoff,
        format_mcp_readiness,
        format_motor_hybrid_router,
        format_motor_mmm_quick_check,
        format_motor_readiness,
        format_observable_contract_summary,
        format_physical_quantity_summary,
        format_quality_summary,
        format_validation_matrix,
        format_representative_cards,
        format_validation_summary,
        format_team28_cards,
        list_sample_decks,
        route_sample_decks,
        format_sample_deck_routes,
        search_sample_decks,
        get_sample_deck,
    )
    decks = list_sample_decks()
    assert len(decks) == 3200
    assert sum(1 for d in decks if d["ext"] == "mai") == 1600
    assert sum(1 for d in decks if d["ext"] == "meg") == 1600
    assert any(d["path"] == "application/motor/pm_cosine_pickup_72/pm001/pm001.mai" for d in decks)
    assert any(d["path"] == "application/motor/spm_surface_pm_10/spm001/spm001.mai" for d in decks)
    assert any(d["path"] == "application/motor/srm_switched_reluctance_10/srm001/srm001.mai" for d in decks)
    assert any(d["path"] == "application/motor/induction_cage_10/im001/im001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_bldc_spm_10/ebl001/ebl001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_ipm_hairpin_10/eip001/eip001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_induction_bar_10/eim001/eim001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_synrm_flux_barrier_10/esr001/esr001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_srm_pole_variants_10/esm001/esm001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_afpm_linearized_10/eaf001/eaf001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_bldc_outer_rotor_10/ebo001/ebo001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_induction_fraction_10/eif001/eif001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_spmsm_static_torque_10/eptq001/eptq001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_srm1216_outer_rotor_10/ero001/ero001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_synrm_fraction_static_torque_10/eyf001/eyf001.mai" for d in decks)
    assert any(
        d["path"] == "application/emdlab_1ph_transformer_static_10/ept001/ept001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/emdlab_benchmark_ccore_10/ecc001/ecc001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_validation_anchors_10/nva001/nva001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_flum_law_64/nfl001/nfl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_inductance_energy_100/nie001/nie001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_force_torque_100/nft001/nft001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_ac_loss_100/nal001/nal001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_magnetic_circuit_100/nmc001/nmc001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_permanent_magnet_100/npm001/npm001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_transformer_coupling_100/ntc001/ntc001.mai"
        for d in decks
    )
    assert any(d["path"] == "application/motor/ipm_interior_pm_10/ipm001/ipm001.mai" for d in decks)
    assert any(d["path"] == "application/motor/wound_field_sync_10/wfs001/wfs001.mai" for d in decks)
    assert any(d["path"] == "application/motor/axial_flux_pm_10/afm001/afm001.mai" for d in decks)
    assert any(d["path"] == "application/motor/linear_pm_motor_10/lpm001/lpm001.mai" for d in decks)
    assert any(d["path"] == "application/motor/stepper_motor_10/stm001/stm001.mai" for d in decks)
    assert any(d["path"] == "application/wpt_loop_10/wpl001/wpl001.mai" for d in decks)
    assert any(d["path"] == "application/mri_loop_10/mrl001/mrl001.mai" for d in decks)
    assert any(d["path"] == "application/motor/sr_motor_loop_10/srl001/srl001.mai" for d in decks)
    assert any(d["path"] == "application/motor/spm_loop_10/spl001/spl001.mai" for d in decks)
    assert any(
        d["path"] == "application/ih_induction_heating_10/ihl001/ihl001.mai"
        for d in decks
    )
    assert any(d["path"] == "application/motor/reluctance_motor_10/ryl001/ryl001.mai" for d in decks)
    assert any(d["path"] == "application/motor/hysteresis_motor_10/hyl001/hyl001.mai" for d in decks)
    assert any(
        d["path"] == "application/transformer_loop_10/tfl001/tfl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/accelerator_magnet_10/acl001/acl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/actuator_plunger_10/atl001/atl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/maglev_bearing_10/mvl001/mvl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/magnetic_separator_10/msl001/msl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/eddy_current_brake_10/ebl001/ebl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/ndt_eddy_probe_10/ndl001/ndl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/transformer_core_pickup_12/tf001/tf001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/mri_gradient_shield_12/mri001/mri001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/wpt_coupled_coils_10/wpt001/wpt001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/magnetic_gear_10/mgl001/mgl001.mai"
        for d in decks
    )
    assert any(d["path"] == "application/voice_coil_10/vcl001/vcl001.mai" for d in decks)
    assert any(
        d["path"] == "application/relay_solenoid_10/rsl001/rsl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/hall_sensor_fixture_10/hsl001/hsl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/electromagnetic_clutch_10/ecl001/ecl001.mai"
        for d in decks
    )
    assert any(d["path"] == "application/wpt_misalignment_10/wpm001/wpm001.mai" for d in decks)
    assert any(
        d["path"] == "application/mri_gradient_sequence_10/mgs001/mgs001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/transformer_leakage_10/tlg001/tlg001.mai"
        for d in decks
    )
    assert any(d["path"] == "application/ih_susceptor_ring_10/ihr001/ihr001.mai" for d in decks)
    assert any(
        d["path"] == "application/accelerator_corrector_10/acm001/acm001.mai"
        for d in decks
    )
    manifest_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "src",
        "elf_mcp_server",
        "public_samples",
        "VALIDATED_MANIFEST.json",
    )
    with open(manifest_path, encoding="ascii") as f:
        manifest = json.load(f)
    assert manifest["total_cases"] == 1600
    assert manifest["total_input_files"] == 3200
    assert len(manifest["families"]) == 72
    assert all(v["validation"] == "passed" for v in manifest["families"].values())
    assert all(v["validation_level"] for v in manifest["families"].values())
    levels = {v["validation_level"] for v in manifest["families"].values()}
    assert levels == {"ngsolve_proxy_energy", "ngsolve_numeric_invariant"}
    assert "ngsolve_proxy_energy_positive" in manifest["families"][
        "application/motor/emdlab_ipm_hairpin_10"
    ]["checks"]
    assert "ngsolve_proxy_energy_positive" in manifest["families"][
        "application/emdlab_benchmark_ccore_10"
    ]["checks"]
    assert "ngsolve_proxy_energy_positive" in manifest["families"][
        "application/motor/wound_field_sync_10"
    ]["checks"]
    numeric_manifest = manifest["families"]["application/numeric_validation_anchors_10"]
    assert numeric_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in numeric_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in numeric_manifest["checks"]
    flum_law_manifest = manifest["families"]["application/numeric_flum_law_64"]
    assert flum_law_manifest["cases"] == 64
    assert flum_law_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in flum_law_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in flum_law_manifest["checks"]
    inductance_manifest = manifest["families"]["application/numeric_inductance_energy_100"]
    assert inductance_manifest["cases"] == 100
    assert inductance_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in inductance_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in inductance_manifest["checks"]
    force_manifest = manifest["families"]["application/numeric_force_torque_100"]
    assert force_manifest["cases"] == 100
    assert force_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in force_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in force_manifest["checks"]
    ac_loss_manifest = manifest["families"]["application/numeric_ac_loss_100"]
    assert ac_loss_manifest["cases"] == 100
    assert ac_loss_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in ac_loss_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in ac_loss_manifest["checks"]
    magnetic_circuit_manifest = manifest["families"]["application/numeric_magnetic_circuit_100"]
    assert magnetic_circuit_manifest["cases"] == 100
    assert magnetic_circuit_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in magnetic_circuit_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in magnetic_circuit_manifest["checks"]
    permanent_magnet_manifest = manifest["families"]["application/numeric_permanent_magnet_100"]
    assert permanent_magnet_manifest["cases"] == 100
    assert permanent_magnet_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in permanent_magnet_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in permanent_magnet_manifest["checks"]
    transformer_coupling_manifest = manifest["families"]["application/numeric_transformer_coupling_100"]
    assert transformer_coupling_manifest["cases"] == 100
    assert transformer_coupling_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in transformer_coupling_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in transformer_coupling_manifest["checks"]
    validation_summary = build_validation_summary()
    assert validation_summary["total_cases"] == 1600
    assert validation_summary["total_input_files"] == 3200
    assert validation_summary["total_families"] == 72
    assert validation_summary["level_counts"]["ngsolve_proxy_energy"]["families"] == 64
    assert validation_summary["level_counts"]["ngsolve_proxy_energy"]["cases"] == 926
    assert validation_summary["level_counts"]["ngsolve_numeric_invariant"]["families"] == 8
    assert validation_summary["level_counts"]["ngsolve_numeric_invariant"]["cases"] == 674
    publication_batches = build_publication_batch_summary()
    assert publication_batches["checkpoint_size"] == 100
    assert publication_batches["total_cases"] == 1600
    assert publication_batches["total_batches"] == 16
    assert publication_batches["full_100_case_batches"] == 16
    assert publication_batches["remainder_cases"] == 0
    assert publication_batches["next_checkpoint_cases"] == 1700
    assert publication_batches["additional_cases_needed_for_next_100_case_checkpoint"] == 100
    validation_text = format_validation_summary(validation_summary)
    assert "1600 cases" in validation_text
    assert "ngsolve_proxy_energy" in validation_text
    assert "not a full absolute field/force/torque/loss agreement suite" in validation_text
    assert "100-case publication checkpoints" in validation_text
    assert "100 additional validated cases would make the next optional increment" in validation_text
    quality_summary = build_quality_summary()
    assert quality_summary["label_counts"]["gold_numeric_invariant"]["cases"] == 674
    assert quality_summary["label_counts"]["silver_observable_contract"]["cases"] == 500
    assert quality_summary["label_counts"]["silver_proxy_energy"]["cases"] == 426
    assert quality_summary["quality_gate_status"] == "PASS"
    assert all(gate["status"] == "PASS" for gate in quality_summary["quality_gates"])
    assert {gate["gate"] for gate in quality_summary["quality_gates"]} >= {
        "paired_mai_meg",
        "exact_sample_pairs_unique",
        "manifest_matches_files",
        "publication_batches_cover_cases",
        "public_boundary_text",
        "no_solver_output_files",
        "application_hierarchy",
        "observable_contract_target_is_500_cases",
        "observable_contract_markers_pass",
    }
    quality_text = format_quality_summary(quality_summary)
    assert "Publication Quality Gates (PASS)" in quality_text
    assert "paired_mai_meg" in quality_text
    assert "manifest_matches_files" in quality_text
    assert "physical_quantity_case_coverage" in quality_text
    assert "gold_physics_anchor_coverage" in quality_text
    assert "gold_numeric_invariant" in quality_text
    assert "silver_observable_contract" in quality_text
    assert "silver_proxy_energy" in quality_text
    gold_quality_text = format_quality_summary(build_quality_summary(label="gold"))
    assert "application/numeric_transformer_coupling_100" in gold_quality_text
    enhanced_quality_text = format_quality_summary(build_quality_summary(label="observable"))
    assert "500 cases" in enhanced_quality_text
    assert "application/motor/pm_square_2pole_pickup_100" in enhanced_quality_text
    observable_contract_summary = build_observable_contract_summary()
    assert observable_contract_summary["observable_contract_gate_status"] == "PASS"
    assert observable_contract_summary["enhanced_cases"] == 500
    assert observable_contract_summary["enhanced_family_count"] == 28
    assert observable_contract_summary["failed_case_count"] == 0
    observable_contract_text = format_observable_contract_summary(observable_contract_summary)
    assert "Observable Contract Gates (PASS)" in observable_contract_text
    assert "public_observable_contract_passed" in observable_contract_text
    assert "application/wpt_misalignment_10" in observable_contract_text
    physics_summary = build_physical_quantity_summary()
    assert physics_summary["physical_gate_status"] == "PASS"
    assert all(gate["status"] == "PASS" for gate in physics_summary["physical_gates"])
    assert physics_summary["quantity_counts"]["flux_linkage"]["cases"] == 1600
    assert physics_summary["quantity_counts"]["flux_linkage"]["gold_cases"] == 674
    assert physics_summary["quantity_counts"]["motor_flux_linkage"]["cases"] == 652
    assert physics_summary["quantity_counts"]["force_torque_gradient"]["gold_cases"] == 100
    assert physics_summary["quantity_counts"]["ac_loss"]["gold_cases"] == 100
    assert physics_summary["quantity_counts"]["permanent_magnet_flux"]["gold_cases"] == 100
    assert physics_summary["quantity_counts"]["transformer_coupling"]["gold_cases"] == 100
    physics_text = format_physical_quantity_summary(physics_summary)
    assert "Physical Quantity Gates (PASS)" in physics_text
    assert "flux_linkage" in physics_text
    assert "transformer_coupling" in physics_text
    force_physics = build_physical_quantity_summary(quantity="force")
    assert force_physics["quantity_counts"]["force_torque_gradient"]["gold_cases"] == 100
    assert any(
        row["family"] == "application/numeric_force_torque_100"
        for row in force_physics["families"]
    )
    cross_validation_summary = build_cross_validation_summary()
    assert cross_validation_summary["cross_validation_gate_status"] == "PASS"
    assert all(
        gate["status"] == "PASS"
        for gate in cross_validation_summary["cross_validation_gates"]
    )
    assert cross_validation_summary["gaps"]["families_without_independent_cross_validation"] == 0
    assert cross_validation_summary["gaps"]["cases_without_independent_cross_validation"] == 0
    assert cross_validation_summary["method_counts"]["ngsolve_proxy_energy_positive"]["cases"] == 926
    assert cross_validation_summary["method_counts"]["ngsolve_numeric_invariants_passed"]["cases"] == 674
    assert cross_validation_summary["method_counts"]["elf_flux_invariants_passed"]["cases"] == 674
    cross_validation_text = format_cross_validation_summary(cross_validation_summary)
    assert "Cross-Validation Gates (PASS)" in cross_validation_text
    assert "No family is missing independent NGSolve cross-validation" in cross_validation_text
    assert "Silver-To-Gold Upgrade Candidates" in cross_validation_text
    duplicate_audit = build_duplicate_audit()
    assert duplicate_audit["audit_gate_status"] == "PASS"
    assert duplicate_audit["delete_recommendation"] == "no_public_deck_deletion_recommended"
    assert duplicate_audit["exact_pair_duplicate_groups"] == 0
    assert duplicate_audit["exact_pair_delete_candidates"] == 0
    assert duplicate_audit["mai_reuse_groups"] >= 1
    assert duplicate_audit["meg_reuse_groups"] >= 1
    assert any(
        gate["gate"] == "exact_sample_pairs_unique" and gate["status"] == "PASS"
        for gate in duplicate_audit["gates"]
    )
    duplicate_text = format_duplicate_audit(duplicate_audit)
    assert "No exact pair duplicates were found" in duplicate_text
    assert "MCP Collapse Candidates" in duplicate_text
    handoff = build_local_simulation_handoff(
        "SPM motor flux linkage sweep",
        family="spm",
        quantity="motor",
    )
    assert handoff["schema_version"] == "elf-local-simulation-handoff/v1"
    assert handoff["selected_routes"]
    assert handoff["selected_routes"][0]["family"] == "application/motor/spm_surface_pm_10"
    assert handoff["selected_routes"][0]["representative_decks"]
    assert "mai_text or mai_path" in handoff["runner_input_contract"]["required"]
    assert (
        handoff["runner_input_contract"]["execution_policy"]["preferred"]
        == "direct_solver_exe_no_gui"
    )
    assert (
        handoff["runner_input_contract"]["execution_policy"]["avoid"]
        == "Launcher.exe GUI route"
    )
    assert handoff["parser_output_contract"]["primary_files"]["run_log"] == ".mao"
    assert handoff["parser_output_contract"]["primary_files"]["mesh_script_input"] == ".mei"
    assert "flux_linkage_FLUM" in handoff["parser_output_contract"]["parsed_observables"]
    handoff_text = format_local_simulation_handoff(handoff)
    assert "does not execute ELF/MAGIC" in handoff_text
    assert "Runner Input Contract" in handoff_text
    assert "direct_solver_exe_no_gui" in handoff_text
    assert "primary files" in handoff_text
    assert ".mao" in handoff_text
    assert ".mag" in handoff_text
    assert ".mei" in handoff_text
    forbidden_private_markers = (
        "C:" + "\\temp",
        "C:" + "\\tmp",
        "S:" + "\\",
        "W:" + "\\",
        "_cross" + "val",
    )
    assert not any(marker in handoff_text for marker in forbidden_private_markers)
    linear_handoff = build_local_simulation_handoff(
        "linear PM motor thrust FLUM",
        family="linear",
        quantity="motor",
    )
    assert linear_handoff["selected_routes"][0]["family"] == "application/motor/linear_pm_motor_10"
    linear_handoff_text = format_local_simulation_handoff(linear_handoff)
    assert "direct_solver_exe_no_gui" in linear_handoff_text
    assert ".mao" in linear_handoff_text
    assert ".mag" in linear_handoff_text
    assert ".mei" in linear_handoff_text
    assert not any(marker in linear_handoff_text for marker in forbidden_private_markers)
    assert "Motor Design Loop" in handoff_text
    readiness = build_mcp_readiness()
    assert readiness["readiness"] == "ready_for_tag_push"
    assert all(gate["status"] == "PASS" for gate in readiness["gates"])
    assert any(
        row["name"] == "spm_handoff_routes_to_compact_spm"
        and row["first_family"] == "application/motor/spm_surface_pm_10"
        for row in readiness["route_checks"]
    )
    readiness_text = format_mcp_readiness(readiness)
    assert "ready_for_tag_push" in readiness_text
    assert "Release Steps" in readiness_text
    assert "S:" + "\\" not in readiness_text
    motor_readiness = build_motor_readiness()
    assert motor_readiness["motor_readiness"] == "motor_coverage_ready_validation_upgrade_recommended"
    assert motor_readiness["motor_cases"] == 652
    assert motor_readiness["motor_families"] == 37
    assert motor_readiness["quality_counts"]["silver_observable_contract"] == 18
    assert motor_readiness["quality_counts"]["silver_proxy_energy"] == 19
    assert motor_readiness["validation_counts"]["ngsolve_proxy_energy"] == 37
    assert motor_readiness["gold_numeric_motor_families"] == 0
    assert any(
        gate["gate"] == "motor_gold_numeric_anchors" and gate["status"] == "WARN"
        for gate in motor_readiness["gates"]
    )
    assert any(
        row["name"] == "IPM" and row["families"]
        for row in motor_readiness["archetypes"]
    )
    motor_readiness_text = format_motor_readiness(motor_readiness)
    assert "652 cases across 37 families" in motor_readiness_text
    assert "radia-motor targets" in motor_readiness_text
    assert "S:" + "\\" not in motor_readiness_text
    hybrid_route = build_motor_hybrid_router("IPM hairpin motor flux linkage and MTPA")
    assert hybrid_route["schema_version"] == "elf-motor-hybrid-router/v1"
    assert hybrid_route["inferred_family"] == "ipm"
    assert hybrid_route["elf_deck_routes"][0]["family"] == "application/motor/emdlab_ipm_hairpin_10"
    assert "elf_motor_mmm_quick_check" in hybrid_route["mmm_quick_check"]["call"]
    assert hybrid_route["age_validation"]["lane"] == "radia-motor-age"
    assert 'ngsolve_usage("mtpa")' in hybrid_route["age_validation"]["calls"]
    assert hybrid_route["vim_validation"]["lane"] == "radia-motor-vim"
    assert "demag_field" in hybrid_route["vim_validation"]["targets"]
    assert 'motor_validation_lane_template("hdiv_vim_reduced_fem")' in hybrid_route["vim_validation"]["calls"]
    hybrid_text = format_motor_hybrid_router(hybrid_route)
    assert "ELF/radia motor hybrid router" in hybrid_text
    assert "application/motor/emdlab_ipm_hairpin_10" in hybrid_text
    assert "radia-motor-vim" in hybrid_text
    assert "HDiv-VIM" in hybrid_text
    assert "elf_local_simulation_handoff" in hybrid_text
    assert "S:" + "\\" not in hybrid_text
    wide_routes = {
        "BLDC outer rotor motor": "outer_rotor_bldc",
        "axial flux PM face magnet": "afpm",
        "DFIG slip power": "dfig",
        "locked rotor induction current": "locked_rotor_induction",
        "line start pull-in torque": "line_start_induction",
        "stepper motor detent": "stepper",
        "linear PM translator force": "linear_pm",
        "wound field synchronous rotor field": "wound_field_sync",
    }
    for prompt, family in wide_routes.items():
        wide_route = build_motor_hybrid_router(prompt)
        assert wide_route["inferred_family"] == family
        assert wide_route["elf_deck_routes"]
        assert wide_route["age_validation"]["calls"]
        assert wide_route["vim_validation"]["targets"]
    bldc_quick = build_motor_mmm_quick_check(motor_type="outer_rotor_bldc")
    assert bldc_quick["family"] == "outer_rotor_bldc"
    assert "pm_airgap_flux" in bldc_quick["recommended_age_targets"]
    mmm_check = build_motor_mmm_quick_check(motor_type="spm")
    assert mmm_check["schema_version"] == "elf-motor-mmm-quick/v1"
    assert mmm_check["family"] == "spm"
    assert mmm_check["outputs"]["lambda_pm_peak_wb"] > 0
    assert "back_emf" in mmm_check["recommended_age_targets"]
    mmm_text = format_motor_mmm_quick_check(mmm_check)
    assert "ELF motor 2D MMM/BEM-like quick check" in mmm_text
    assert "not a production solver" in mmm_text
    assert "S:" + "\\" not in mmm_text
    matrix_summary = build_validation_matrix()
    assert matrix_summary["validation_matrix_gate_status"] == "PASS"
    assert all(
        gate["status"] == "PASS"
        for gate in matrix_summary["validation_matrix_gates"]
    )
    assert matrix_summary["selected_family_count"] == matrix_summary["total_families"]
    assert matrix_summary["quantities"]["transformer_coupling"]["gold_cases"] == 100
    assert "ngsolve_numeric_invariants_passed" in matrix_summary["quantities"]["transformer_coupling"]["validation_methods"]
    matrix_text = format_validation_matrix(matrix_summary)
    assert "Validation Matrix Gates (PASS)" in matrix_text
    assert "transformer_coupling" in matrix_text
    assert "application/numeric_transformer_coupling_100/ntc001/ntc001.mai" in matrix_text
    transformer_matrix = build_validation_matrix(quantity="transformer", label="gold")
    assert transformer_matrix["selected_family_count"] >= 1
    assert any(
        row["family"] == "application/numeric_transformer_coupling_100"
        for row in transformer_matrix["families"]
    )
    representatives = build_representative_cards()
    assert len(representatives) >= 32
    assert representatives[0]["quality_label"] == "silver_observable_contract"
    representative_text = format_representative_cards(representatives)
    assert "why representative" in representative_text
    assert "application/motor/emdlab_ipm_hairpin_10/eip001/eip001.mai" in representative_text
    assert "application/numeric_transformer_coupling_100/ntc001/ntc001.mai" in representative_text
    motor_representatives = build_representative_cards(area="motor")
    assert any(card["family"] == "application/motor/emdlab_ipm_hairpin_10" for card in motor_representatives)
    promotion_ja = format_public_promotion("ja")
    assert "1600" in promotion_ja
    assert "品質ラベル" in promotion_ja
    assert "solver 出力" in promotion_ja
    promotion_en = format_public_promotion("en")
    assert "1600 public runnable" in promotion_en
    numeric_summary = build_validation_summary(family="numeric_validation")
    assert numeric_summary["selected_family_count"] == 1
    assert numeric_summary["families"][0]["family"] == "application/numeric_validation_anchors_10"
    numeric_text = format_validation_summary(numeric_summary)
    assert "elf_flux_invariants_passed" in numeric_text
    flum_law_summary = build_validation_summary(family="numeric_flum_law")
    assert flum_law_summary["selected_family_count"] == 1
    assert flum_law_summary["families"][0]["family"] == "application/numeric_flum_law_64"
    assert flum_law_summary["families"][0]["cases"] == 64
    inductance_summary = build_validation_summary(family="numeric_inductance_energy")
    assert inductance_summary["selected_family_count"] == 1
    assert inductance_summary["families"][0]["family"] == "application/numeric_inductance_energy_100"
    assert inductance_summary["families"][0]["cases"] == 100
    force_summary = build_validation_summary(family="numeric_force_torque")
    assert force_summary["selected_family_count"] == 1
    assert force_summary["families"][0]["family"] == "application/numeric_force_torque_100"
    assert force_summary["families"][0]["cases"] == 100
    ac_loss_summary = build_validation_summary(family="numeric_ac_loss")
    assert ac_loss_summary["selected_family_count"] == 1
    assert ac_loss_summary["families"][0]["family"] == "application/numeric_ac_loss_100"
    assert ac_loss_summary["families"][0]["cases"] == 100
    magnetic_circuit_summary = build_validation_summary(family="numeric_magnetic_circuit")
    assert magnetic_circuit_summary["selected_family_count"] == 1
    assert magnetic_circuit_summary["families"][0]["family"] == "application/numeric_magnetic_circuit_100"
    assert magnetic_circuit_summary["families"][0]["cases"] == 100
    permanent_magnet_summary = build_validation_summary(family="numeric_permanent_magnet")
    assert permanent_magnet_summary["selected_family_count"] == 1
    assert permanent_magnet_summary["families"][0]["family"] == "application/numeric_permanent_magnet_100"
    assert permanent_magnet_summary["families"][0]["cases"] == 100
    transformer_coupling_summary = build_validation_summary(family="numeric_transformer_coupling")
    assert transformer_coupling_summary["selected_family_count"] == 1
    assert transformer_coupling_summary["families"][0]["family"] == "application/numeric_transformer_coupling_100"
    assert transformer_coupling_summary["families"][0]["cases"] == 100
    hits = search_sample_decks("HBCN FLUM", ext="mai")
    assert hits
    assert hits[0]["path"].endswith(".mai")
    transformer_hits = search_sample_decks("transformer FLUM", ext="mai")
    assert transformer_hits
    assert transformer_hits[0]["path"].startswith(
        (
            "application/transformer",
            "application/emdlab_1ph_transformer_static_10",
            "application/numeric_transformer_coupling_100",
        )
    )
    transformer_coupling_hits = search_sample_decks("transformer coupling turns ratio HBCU FLUM", ext="mai")
    assert transformer_coupling_hits
    assert transformer_coupling_hits[0]["path"].startswith("application/numeric_transformer_coupling_100")
    mri_hits = search_sample_decks("MRI OHM2 FREQ", ext="mai")
    assert mri_hits
    assert mri_hits[0]["path"].startswith("application/mri")
    im_hits = search_sample_decks("induction motor cage OHM2 FLUM", top_k=20, ext="mai")
    assert im_hits
    assert any(h["path"].startswith("application/motor/induction_cage_10") for h in im_hits)
    spm_hits = search_sample_decks("SPM HBRM FLUM", top_k=20, ext="mai")
    assert spm_hits
    assert any(h["path"].startswith("application/motor/spm_surface_pm_10") for h in spm_hits)
    srm_hits = search_sample_decks("SRM reluctance FLUM", top_k=20, ext="mai")
    assert srm_hits
    assert any(h["path"].startswith("application/motor/srm_switched_reluctance_10") for h in srm_hits)
    spm_route = route_sample_decks("SPM motor flux linkage sweep", limit=3)
    assert spm_route[0]["family"] == "application/motor/spm_surface_pm_10"
    emdlab_ipm_hits = search_sample_decks("EMDLAB-style IPM hairpin FLUM", ext="mai")
    assert emdlab_ipm_hits
    assert emdlab_ipm_hits[0]["path"].startswith("application/motor/emdlab_ipm_hairpin_10")
    emdlab_im_hits = search_sample_decks("induction-machine bar OHM2 FLUM", ext="mai")
    assert emdlab_im_hits
    assert emdlab_im_hits[0]["path"].startswith("application/motor/emdlab_induction_bar_10")
    emdlab_synrm_hits = search_sample_decks("EMDLAB-style SynRM flux-barrier FLUM", ext="mai")
    assert emdlab_synrm_hits
    assert emdlab_synrm_hits[0]["path"].startswith("application/motor/emdlab_synrm_flux_barrier_10")
    emdlab_srm_hits = search_sample_decks("EMDLAB-style SRM pole-variant FLUM", ext="mai")
    assert emdlab_srm_hits
    assert emdlab_srm_hits[0]["path"].startswith("application/motor/emdlab_srm_pole_variants_10")
    emdlab_afpm_hits = search_sample_decks("EMDLAB-style AFPM linearized-airgap FLUM", ext="mai")
    assert emdlab_afpm_hits
    assert emdlab_afpm_hits[0]["path"].startswith("application/motor/emdlab_afpm_linearized_10")
    emdlab_spmsm_static_hits = search_sample_decks("EMDLAB-style SPM static-torque FLUM", ext="mai")
    assert emdlab_spmsm_static_hits
    assert emdlab_spmsm_static_hits[0]["path"].startswith("application/motor/emdlab_spmsm_static_torque_10")
    emdlab_transformer_hits = search_sample_decks("EMDLAB-style single-phase transformer static FLUM", ext="mai")
    assert emdlab_transformer_hits
    assert emdlab_transformer_hits[0]["path"].startswith("application/emdlab_1ph_transformer_static_10")
    emdlab_ccore_hits = search_sample_decks("EMDLAB-style benchmark C-core FLUM", ext="mai")
    assert emdlab_ccore_hits
    assert emdlab_ccore_hits[0]["path"].startswith("application/emdlab_benchmark_ccore_10")
    numeric_hits = search_sample_decks("numeric validation anchor current scaling FLUM", ext="mai")
    assert numeric_hits
    assert numeric_hits[0]["path"].startswith("application/numeric_validation_anchors_10")
    flum_law_hits = search_sample_decks("FLUM law superposition", ext="mai")
    assert flum_law_hits
    assert flum_law_hits[0]["path"].startswith("application/numeric_flum_law_64")
    inductance_hits = search_sample_decks("inductance co-energy FLUM turn scaling", ext="mai")
    assert inductance_hits
    assert inductance_hits[0]["path"].startswith("application/numeric_inductance_energy_100")
    force_hits = search_sample_decks("force torque co-energy gradient", ext="mai")
    assert force_hits
    assert force_hits[0]["path"].startswith("application/numeric_force_torque_100")
    ac_loss_hits = search_sample_decks("AC loss frequency square OHM2", ext="mai")
    assert ac_loss_hits
    assert ac_loss_hits[0]["path"].startswith("application/numeric_ac_loss_100")
    magnetic_circuit_hits = search_sample_decks("magnetic circuit air gap HBCU", ext="mai")
    assert magnetic_circuit_hits
    assert magnetic_circuit_hits[0]["path"].startswith("application/numeric_magnetic_circuit_100")
    permanent_magnet_hits = search_sample_decks("permanent magnet HBRM polarity FLUM", ext="mai")
    assert permanent_magnet_hits
    assert permanent_magnet_hits[0]["path"].startswith("application/numeric_permanent_magnet_100")
    route = route_sample_decks("I want an IPM hairpin motor flux linkage deck", limit=3)
    assert route
    assert route[0]["family"] == "application/motor/emdlab_ipm_hairpin_10"
    route_text = format_sample_deck_routes(route, "IPM hairpin motor flux linkage")
    assert "elf_sample_decks_playbook" in route_text
    assert "application/motor/emdlab_ipm_hairpin_10/eip001/eip001.mai" in route_text
    wpt_route = route_sample_decks("WPT misalignment with a conducting shield", limit=2)
    assert wpt_route[0]["family"] == "application/wpt_misalignment_10"
    outer_route = route_sample_decks("BLDC outer rotor motor", limit=2)
    assert outer_route[0]["family"] == "application/motor/emdlab_bldc_outer_rotor_10"
    transformer_static_route = route_sample_decks("single phase transformer static", limit=2)
    assert transformer_static_route[0]["family"] == "application/emdlab_1ph_transformer_static_10"
    ccore_route = route_sample_decks("benchmark C-core magnet", limit=2)
    assert ccore_route[0]["family"] == "application/emdlab_benchmark_ccore_10"
    numeric_route = route_sample_decks("numeric validation anchor FLUM invariant", limit=2)
    assert numeric_route[0]["family"] == "application/numeric_validation_anchors_10"
    flum_law_route = route_sample_decks("FLUM law current linearity superposition", limit=2)
    assert flum_law_route[0]["family"] == "application/numeric_flum_law_64"
    inductance_route = route_sample_decks("inductance co-energy FLUM turn scaling", limit=2)
    assert inductance_route[0]["family"] == "application/numeric_inductance_energy_100"
    force_route = route_sample_decks("force torque co-energy gradient", limit=2)
    assert force_route[0]["family"] == "application/numeric_force_torque_100"
    ac_loss_route = route_sample_decks("AC loss frequency square OHM2", limit=2)
    assert ac_loss_route[0]["family"] == "application/numeric_ac_loss_100"
    magnetic_circuit_route = route_sample_decks("magnetic circuit air gap HBCU", limit=2)
    assert magnetic_circuit_route[0]["family"] == "application/numeric_magnetic_circuit_100"
    permanent_magnet_route = route_sample_decks("permanent magnet HBRM polarity FLUM", limit=2)
    assert permanent_magnet_route[0]["family"] == "application/numeric_permanent_magnet_100"
    transformer_coupling_route = route_sample_decks("transformer coupling turns ratio HBCU FLUM", limit=2)
    assert transformer_coupling_route[0]["family"] == "application/numeric_transformer_coupling_100"
    wound_route = route_sample_decks("wound-field synchronous motor rotor field", limit=2)
    assert wound_route[0]["family"] == "application/motor/wound_field_sync_10"
    stepper_route = route_sample_decks("stepper motor detent angle", limit=2)
    assert stepper_route[0]["family"] == "application/motor/stepper_motor_10"
    wpt_hits = search_sample_decks("WPT MOMC FLUM", ext="mai")
    assert wpt_hits
    assert wpt_hits[0]["path"].startswith("application/wpt_coupled_coils_10")
    wpt_loop_hits = search_sample_decks("Loop10 WPT MOMC FLUM", ext="mai")
    assert wpt_loop_hits
    assert wpt_loop_hits[0]["path"].startswith("application/wpt_loop_10")
    mri_loop_hits = search_sample_decks("Loop10 MRI OHM2 FREQ", ext="mai")
    assert mri_loop_hits
    assert mri_loop_hits[0]["path"].startswith("application/mri_loop_10")
    sr_loop_hits = search_sample_decks("SR-motor reluctance FLUM", ext="mai")
    assert sr_loop_hits
    assert sr_loop_hits[0]["path"].startswith("application/motor/sr_motor_loop_10")
    spm_loop_hits = search_sample_decks("Loop10 SPM HBRM FLUM", ext="mai")
    assert spm_loop_hits
    assert spm_loop_hits[0]["path"].startswith("application/motor/spm_loop_10")
    ih_hits = search_sample_decks("IH induction-heating MOMC", ext="mai")
    assert ih_hits
    assert ih_hits[0]["path"].startswith("application/ih_induction_heating_10")
    reluctance_hits = search_sample_decks("reluctance motor synchronous saliency", ext="mai")
    assert reluctance_hits
    assert reluctance_hits[0]["path"].startswith("application/motor/reluctance_motor_10")
    hysteresis_hits = search_sample_decks("hysteresis motor high-coercivity", ext="mai")
    assert hysteresis_hits
    assert hysteresis_hits[0]["path"].startswith("application/motor/hysteresis_motor_10")
    transformer_loop_hits = search_sample_decks("Loop10 transformer FLUM", ext="mai")
    assert transformer_loop_hits
    assert transformer_loop_hits[0]["path"].startswith("application/transformer_loop_10")
    accelerator_hits = search_sample_decks("accelerator electromagnet FLUM", ext="mai")
    assert accelerator_hits
    assert accelerator_hits[0]["path"].startswith("application/accelerator_magnet_10")
    actuator_hits = search_sample_decks("Loop11 actuator plunger FLUM", ext="mai")
    assert actuator_hits
    assert actuator_hits[0]["path"].startswith("application/actuator_plunger_10")
    maglev_hits = search_sample_decks("Loop11 maglev bearing FLUM", ext="mai")
    assert maglev_hits
    assert maglev_hits[0]["path"].startswith("application/maglev_bearing_10")
    separator_hits = search_sample_decks("Loop11 magnetic separator FLUM", ext="mai")
    assert separator_hits
    assert separator_hits[0]["path"].startswith("application/magnetic_separator_10")
    brake_hits = search_sample_decks("Loop11 eddy-current brake OHM2", ext="mai")
    assert brake_hits
    assert brake_hits[0]["path"].startswith("application/eddy_current_brake_10")
    ndt_hits = search_sample_decks("Loop11 NDT eddy-current probe OHM2", ext="mai")
    assert ndt_hits
    assert ndt_hits[0]["path"].startswith("application/ndt_eddy_probe_10")
    gear_hits = search_sample_decks("Loop12 magnetic gear HBCN FLUM", ext="mai")
    assert gear_hits
    assert gear_hits[0]["path"].startswith("application/magnetic_gear_10")
    voice_hits = search_sample_decks("Loop12 voice-coil actuator FLUM", ext="mai")
    assert voice_hits
    assert voice_hits[0]["path"].startswith("application/voice_coil_10")
    relay_hits = search_sample_decks("Loop12 relay solenoid FLUM", ext="mai")
    assert relay_hits
    assert relay_hits[0]["path"].startswith("application/relay_solenoid_10")
    hall_hits = search_sample_decks("Loop12 Hall-sensor fixture FLUM", ext="mai")
    assert hall_hits
    assert hall_hits[0]["path"].startswith("application/hall_sensor_fixture_10")
    clutch_hits = search_sample_decks("Loop12 electromagnetic clutch OHM2", ext="mai")
    assert clutch_hits
    assert clutch_hits[0]["path"].startswith("application/electromagnetic_clutch_10")
    pm001 = get_sample_deck("application/motor/pm_cosine_pickup_72/pm001/pm001.mai")
    pm001_legacy = get_sample_deck("motor/pm_cosine_pickup_72/pm001/pm001.mai")
    assert pm001_legacy["path"] == "application/motor/pm_cosine_pickup_72/pm001/pm001.mai"
    text = pm001["text"]
    assert "USE  MAGIC" in text
    assert "HBCN 1 0 1" in text
    assert "HBCN 2 0 2" in text
    assert "FLUM  49" in text
    cards = build_sample_deck_cards(limit=1600)
    assert len(cards) == 1600
    spm_cards = build_sample_deck_cards(limit=20, family="spm_surface_pm_10")
    assert len(spm_cards) == 10
    assert "spm" in spm_cards[0]["tags"]
    assert "MWL8T" in spm_cards[0]["elements"]
    srm_cards = build_sample_deck_cards(limit=20, family="srm_switched_reluctance_10")
    assert len(srm_cards) == 10
    assert "srm" in srm_cards[0]["tags"]
    assert "MMB8T" in srm_cards[0]["elements"]
    induction_cards = build_sample_deck_cards(limit=20, family="induction_cage_10")
    assert len(induction_cards) == 10
    assert "induction" in induction_cards[0]["tags"]
    assert "MAB8T" in induction_cards[0]["elements"]
    transformer_cards = build_sample_deck_cards(limit=20, family="transformer_core_pickup_12")
    assert len(transformer_cards) == 12
    assert "transformer" in transformer_cards[0]["tags"]
    mri_cards = build_sample_deck_cards(limit=20, family="mri_gradient_shield_12")
    assert len(mri_cards) == 12
    assert "MAB8T" in mri_cards[0]["elements"]
    wpt_cards = build_sample_deck_cards(limit=20, family="wpt_coupled_coils_10")
    assert len(wpt_cards) == 10
    assert "wpt" in wpt_cards[0]["tags"]
    assert "MCL8T" in wpt_cards[0]["elements"]
    loop_family_checks = [
        ("application/wpt_loop_10", "wpt", "MCL8T"),
        ("application/mri_loop_10", "mri", "MAB8T"),
        ("application/motor/sr_motor_loop_10", "sr-motor", "MMB8T"),
        ("application/motor/spm_loop_10", "spm", "MWL8T"),
        ("application/ih_induction_heating_10", "ih", "MAB8T"),
        ("application/motor/reluctance_motor_10", "reluctance", "MMB8T"),
        ("application/motor/hysteresis_motor_10", "hysteresis", "MMB8T"),
        ("application/transformer_loop_10", "transformer", "MCL8T"),
        ("application/accelerator_magnet_10", "accelerator", "MMB8T"),
        ("application/actuator_plunger_10", "actuator", "MMB8T"),
        ("application/maglev_bearing_10", "maglev", "MMB8T"),
        ("application/magnetic_separator_10", "separator", "MWL8T"),
        ("application/eddy_current_brake_10", "brake", "MAB8T"),
        ("application/ndt_eddy_probe_10", "ndt", "MAB8T"),
        ("application/magnetic_gear_10", "magnetic-gear", "MWL8T"),
        ("application/voice_coil_10", "voice-coil", "MCL8T"),
        ("application/relay_solenoid_10", "relay", "MMB8T"),
        ("application/hall_sensor_fixture_10", "hall-sensor", "MWL8T"),
        ("application/electromagnetic_clutch_10", "clutch", "MAB8T"),
        ("application/motor/emdlab_bldc_spm_10", "bldc", "MWL8T"),
        ("application/motor/emdlab_ipm_hairpin_10", "ipm", "MWL8T"),
        ("application/motor/emdlab_induction_bar_10", "rotor-bar", "MAB8T"),
        ("application/motor/emdlab_synrm_flux_barrier_10", "synrm", "MMB8T"),
        ("application/motor/emdlab_srm_pole_variants_10", "pole-variant", "MMB8T"),
        ("application/motor/emdlab_afpm_linearized_10", "afpm", "MWL8T"),
        ("application/motor/emdlab_bldc_outer_rotor_10", "outer-rotor", "MWL8T"),
        ("application/motor/emdlab_spmsm_static_torque_10", "static-torque", "MWL8T"),
        ("application/motor/emdlab_srm1216_outer_rotor_10", "12-16", "MMB8T"),
        ("application/motor/emdlab_synrm_fraction_static_torque_10", "fractional-sector", "MMB8T"),
        ("application/emdlab_1ph_transformer_static_10", "single-phase", "MMB8T"),
        ("application/emdlab_benchmark_ccore_10", "c-core", "MMB8T"),
        ("application/motor/ipm_interior_pm_10", "ipm", "MWL8T"),
        ("application/motor/wound_field_sync_10", "wound-field", "MCL8T"),
        ("application/motor/axial_flux_pm_10", "afpm", "MWL8T"),
        ("application/motor/linear_pm_motor_10", "linear-pm", "MWL8T"),
        ("application/motor/stepper_motor_10", "stepper", "MWL8T"),
        ("application/wpt_misalignment_10", "misalignment", "MAB8T"),
        ("application/mri_gradient_sequence_10", "gradient-sequence", "MAB8T"),
        ("application/transformer_leakage_10", "leakage", "MMB8T"),
        ("application/ih_susceptor_ring_10", "susceptor", "MAB8T"),
        ("application/accelerator_corrector_10", "corrector", "MMB8T"),
        ("application/numeric_validation_anchors_10", "numeric-validation", "MCL8T"),
        ("application/numeric_flum_law_64", "flum-law", "MCL8T"),
        ("application/numeric_inductance_energy_100", "inductance", "MCL8T"),
        ("application/numeric_force_torque_100", "force", "MCL8T"),
        ("application/numeric_ac_loss_100", "ac-loss", "MAB8T"),
        ("application/numeric_magnetic_circuit_100", "magnetic-circuit", "MMB8T"),
        ("application/numeric_permanent_magnet_100", "permanent-magnet", "MWL8T"),
        ("application/numeric_transformer_coupling_100", "transformer-coupling", "MMB8T"),
    ]
    expected_family_lengths = {
        "application/numeric_flum_law_64": 64,
        "application/numeric_inductance_energy_100": 100,
        "application/numeric_force_torque_100": 100,
        "application/numeric_ac_loss_100": 100,
        "application/numeric_magnetic_circuit_100": 100,
        "application/numeric_permanent_magnet_100": 100,
        "application/numeric_transformer_coupling_100": 100,
    }
    for family, tag, element in loop_family_checks:
        family_cards = build_sample_deck_cards(limit=120, family=family)
        expected_len = expected_family_lengths.get(family, 10)
        assert len(family_cards) == expected_len
        assert tag in family_cards[0]["tags"]
        assert element in family_cards[0]["elements"]
    team28 = build_team28_cards()
    assert len(team28) == 28
    team28_text = format_team28_cards(team28)
    assert "Python-interface seed manifest" in team28_text
    assert "normal ELF GUI/CLI" in team28_text
    assert "outside this documentation MCP server" in team28_text
    assert "pm_square_2pole_pickup_100" in team28_text
    combined = "\n".join(get_sample_deck(d["path"])["text"] for d in decks)
    forbidden = (
        "C:" + "\\temp",
        "S:" + "\\",
        "_cross" + "val",
        ".mag",
        ".mao",
        ".mat",
        ".mac",
    )
    assert not any(token in combined for token in forbidden)


def test_public_policy_lint_passes():
    from pathlib import Path

    from elf_mcp_server.policy_lint import (
        SAMPLE_OUTPUT_SUFFIXES,
        SMALL_REFERENCE_OUTPUT_MAX_BYTES,
        SMALL_REFERENCE_OUTPUT_SUFFIXES,
        run_policy_lint,
    )

    repo = Path(__file__).resolve().parents[1]
    assert ".mag" in SMALL_REFERENCE_OUTPUT_SUFFIXES
    assert ".mao" in SAMPLE_OUTPUT_SUFFIXES
    assert SMALL_REFERENCE_OUTPUT_MAX_BYTES <= 64 * 1024
    assert run_policy_lint(repo) == []


def test_source_native_loop_policy_public_safe():
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    doc = (repo / "docs" / "SOURCE_NATIVE_LOOP_POLICY.md").read_text(encoding="utf-8")
    assert "source_native_example" in doc
    assert "public sample decks" in doc
    assert "public validation level" in doc
    assert "Product/private solver replay remains outside" in doc
    assert "Learning Closure Gate" in doc
    assert "result_artifact_id" in doc
    assert "verification.source_tool" in doc
    forbidden = ("S:" + "\\", "C:" + "\\temp", "_cross" + "val")
    assert not any(marker in doc for marker in forbidden)


def test_usage_topic_nonempty():
    from elf_mcp_server.elf_knowledge import get_elf_documentation
    assert len(get_elf_documentation("overview")) > 100


def test_force_gap_contract_topic_public_safe():
    from elf_mcp_server.elf_knowledge import get_elf_documentation

    doc = get_elf_documentation("force_gap_contract")
    assert "coaxial_pm_force_gap_sweep_gate" in doc
    assert "gap_m" in doc
    assert "force_N" in doc
    assert "result_set_id" in doc
    assert "observable_id" in doc
    assert "quantity_dimension" in doc
    assert "N/m" in doc
    assert "SOL FORT" in doc
    assert "1/g^4" in doc
    assert "product result files" in doc
    assert "S:" + "\\" not in doc
    assert "C:" + "\\temp" not in doc
    assert "_cross" + "val" not in doc


def test_maxwell_stress_surface_package_topic_public_safe():
    from elf_mcp_server.elf_knowledge import get_elf_documentation

    doc = get_elf_documentation("maxwell_stress_surface_package")
    assert "maxwell_stress_surface_package_gate" in doc
    assert "stress_surface_id" in doc
    assert "result_set_id" in doc
    assert "observable_id" in doc
    assert "fort_z_force" in doc
    assert "package `axis`" in doc
    assert "closed_surface" in doc
    assert "normal_orientation" in doc
    assert "expected_normal_orientation" in doc
    assert "formulation_id" in doc
    assert "kernel_family" in doc
    assert "singular_treatment" in doc
    assert "expects a formulation or kernel" in doc
    assert "sign_convention" in doc
    assert "quantity_dimension" in doc
    assert "N/m" in doc
    assert "SOL FORT" in doc
    assert "product result files" in doc
    assert "S:" + "\\" not in doc
    assert "C:" + "\\temp" not in doc
    assert "_cross" + "val" not in doc


def test_motor_radia_bridge_topic_public_safe():
    from elf_mcp_server.elf_knowledge import get_elf_documentation
    doc = get_elf_documentation("motor_radia_bridge")
    assert "air-gap field" in doc
    assert "MCL8T" in doc
    assert "MCM4T" in doc
    assert "M1MF" in doc
    assert "SOL FORT" in doc
    assert "SOL FIXA" in doc
    assert "passive pickup coil" in doc
    assert "FLUM <pickup_mid>" in doc
    assert "PM-only pickup examples" in doc
    assert "S:" + "\\" not in doc
    assert "C:" + "\\temp" not in doc
    assert "_cross" + "val" not in doc


def test_recipe_tools_public_safe():
    from elf_mcp_server.recipes import (
        list_recipes,
        search_recipes,
        get_recipe,
        format_recipe,
        plan_workflow,
    )
    recipes = list_recipes(tag="motor")
    assert any(r.name == "passive_flum_pickup" for r in recipes)
    assert any(r.name == "maxwell_torque_surface" for r in recipes)
    matches = search_recipes("back EMF pickup", top_k=3)
    assert matches
    assert matches[0][1].name == "passive_flum_pickup"
    recipe = get_recipe("mutual_flux_current_pickup")
    text = format_recipe(recipe)
    plan = plan_workflow("cogging torque sweep")
    combined = text + plan
    assert "FLUM <pickup_mid>" in combined
    assert "maxwell_torque_surface" in combined
    assert "C:\\" not in combined
    assert "_cross" + "val" not in combined
