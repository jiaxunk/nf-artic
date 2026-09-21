import json
import re
import subprocess
from pathlib import Path
import pytest
import jsonschema

WF_DIR = Path(__file__).resolve().parent.parent


# --- 1. Container Configuration Tests ---

def test_pangolin_container_in_nextflow_config():
    config_text = (WF_DIR / "nextflow.config").read_text()
    
    # Assert params.wf.pangolin_container exists and points to staphb/pangolin:*
    match = re.search(r"pangolin_container\s*=\s*['\"]([^'\"]+)['\"]", config_text)
    assert match is not None, "params.wf.pangolin_container not found in nextflow.config"
    container_val = match.group(1)
    assert container_val.startswith("staphb/pangolin:"), (
        f"Expected params.wf.pangolin_container to point to 'staphb/pangolin:*', got '{container_val}'"
    )


def test_process_with_label_pangolin_uses_container_param():
    config_text = (WF_DIR / "nextflow.config").read_text()
    
    # Check process withLabel:pangolin container
    label_match = re.search(r"withLabel:\s*pangolin\s*\{[^}]*container\s*=\s*['\"]([^'\"]+)['\"]", config_text)
    assert label_match is not None, "withLabel:pangolin block with container not found in nextflow.config"
    assert "pangolin_container" in label_match.group(1), (
        f"withLabel:pangolin container should reference params.wf.pangolin_container, got '{label_match.group(1)}'"
    )


# --- 2. Remove In-Container Write Commands ---

def test_main_nf_no_in_container_pangolin_update():
    main_text = (WF_DIR / "main.nf").read_text()
    
    # Locate process pangolin
    pangolin_proc_match = re.search(r"process\s+pangolin\s*\{(?P<body>.*?)\n\}", main_text, re.DOTALL)
    assert pangolin_proc_match is not None, "process pangolin not found in main.nf"
    pangolin_body = pangolin_proc_match.group("body")
    
    assert "pangolin --update" not in pangolin_body, (
        "process pangolin still contains in-container 'pangolin --update' command"
    )


# --- 3. Dedicated Upstream Runtime Staging Process ---

def test_main_nf_defines_staging_process_and_datadir_usage():
    main_text = (WF_DIR / "main.nf").read_text()
    
    # Check that getPangolinData process exists
    staging_match = re.search(r"process\s+getPangolinData\s*\{(?P<body>.*?)\n\}", main_text, re.DOTALL)
    assert staging_match is not None, "process getPangolinData staging process not found in main.nf"
    
    # Check that process pangolin accepts pangolin_data and uses --datadir
    pangolin_proc_match = re.search(r"process\s+pangolin\s*\{(?P<body>.*?)\n\}", main_text, re.DOTALL)
    assert pangolin_proc_match is not None, "process pangolin not found in main.nf"
    pangolin_body = pangolin_proc_match.group("body")
    
    assert "--datadir" in pangolin_body, "process pangolin should pass --datadir when staged data is provided"


def test_main_nf_staging_channel_wiring():
    main_text = (WF_DIR / "main.nf").read_text()
    
    # Check pipeline wiring: when params.update_data is true/false, staged data is created/routed
    assert "getPangolinData" in main_text, "getPangolinData should be invoked in main.nf"
    assert "update_data" in main_text, "update_data should guard the staging channel"


# --- 4. CLI Parameters & Schema Compatibility ---

def test_cli_parameters_in_nextflow_schema():
    schema_path = WF_DIR / "nextflow_schema.json"
    assert schema_path.exists(), "nextflow_schema.json not found"
    
    with open(schema_path, "r") as f:
        schema = json.load(f)
        
    jsonschema.Draft7Validator.check_schema(schema)
    
    # Check required pangolin parameters exist in schema
    adv_props = schema.get("definitions", {}).get("advanced_options", {}).get("properties", {})
    assert "pangolin_threads" in adv_props, "pangolin_threads missing in schema advanced_options"
    assert "update_data" in adv_props, "update_data missing in schema advanced_options"
    assert "pangolin_options" in adv_props, "pangolin_options missing in schema advanced_options"
    
    rep_props = schema.get("definitions", {}).get("reporting_options", {}).get("properties", {})
    assert "report_lineage" in rep_props, "report_lineage missing in schema reporting_options"


def test_nextflow_config_and_help_syntax():
    res_cfg = subprocess.run(
        ["nextflow", "config", "."],
        cwd=str(WF_DIR),
        capture_output=True,
        text=True
    )
    assert res_cfg.returncode == 0, f"nextflow config failed:\n{res_cfg.stderr}\n{res_cfg.stdout}"
    
    res_help = subprocess.run(
        ["nextflow", "run", "main.nf", "--help"],
        cwd=str(WF_DIR),
        capture_output=True,
        text=True
    )
    assert res_help.returncode == 0, f"nextflow run main.nf --help failed:\n{res_help.stderr}\n{res_help.stdout}"
