import json
import re
import subprocess
from pathlib import Path
import pytest
import jsonschema

WF_DIR = Path(__file__).resolve().parent.parent


# --- 1. Container Configuration Tests ---

def test_nextclade_container_in_nextflow_config():
    config_text = (WF_DIR / "nextflow.config").read_text()
    
    # Assert params.wf.nextclade_container exists and points to nextstrain/nextclade:*
    match = re.search(r"nextclade_container\s*=\s*['\"]([^'\"]+)['\"]", config_text)
    assert match is not None, "params.wf.nextclade_container not found in nextflow.config"
    container_val = match.group(1)
    assert container_val.startswith("nextstrain/nextclade:"), (
        f"Expected params.wf.nextclade_container to point to 'nextstrain/nextclade:*', got '{container_val}'"
    )


def test_process_with_label_nextclade_uses_container_param():
    config_text = (WF_DIR / "nextflow.config").read_text()
    
    # Check process withLabel:nextclade container
    label_match = re.search(r"withLabel:\s*nextclade\s*\{[^}]*container\s*=\s*['\"]([^'\"]+)['\"]", config_text)
    assert label_match is not None, "withLabel:nextclade block with container not found in nextflow.config"
    assert "nextclade_container" in label_match.group(1), (
        f"withLabel:nextclade container should reference params.wf.nextclade_container, got '{label_match.group(1)}'"
    )


# --- 2. Remove In-Task Dataset Downloads ---

def test_main_nf_no_in_process_dataset_get():
    main_text = (WF_DIR / "main.nf").read_text()
    
    # Locate process nextclade
    nextclade_proc_match = re.search(r"process\s+nextclade\s*\{(?P<body>.*?)\n\}", main_text, re.DOTALL)
    assert nextclade_proc_match is not None, "process nextclade not found in main.nf"
    nextclade_body = nextclade_proc_match.group("body")
    
    assert "nextclade dataset get" not in nextclade_body, (
        "process nextclade still contains in-task 'nextclade dataset get' command"
    )


# --- 3. Dedicated Upstream Runtime Staging Process ---

def test_main_nf_defines_getNextcladeData_staging_process():
    main_text = (WF_DIR / "main.nf").read_text()
    
    # Check that getNextcladeData process exists
    staging_match = re.search(r"process\s+getNextcladeData\s*\{(?P<body>.*?)\n\}", main_text, re.DOTALL)
    assert staging_match is not None, "process getNextcladeData staging process not found in main.nf"
    staging_body = staging_match.group("body")
    assert "nextclade dataset get" in staging_body, "process getNextcladeData should run 'nextclade dataset get'"
    assert "sars-cov-2" in staging_body, "process getNextcladeData should request 'sars-cov-2' dataset"


def test_main_nf_nextclade_v3_cli_syntax():
    main_text = (WF_DIR / "main.nf").read_text()
    
    # Check that process nextclade uses Nextclade v3 syntax
    nextclade_proc_match = re.search(r"process\s+nextclade\s*\{(?P<body>.*?)\n\}", main_text, re.DOTALL)
    assert nextclade_proc_match is not None, "process nextclade not found in main.nf"
    nextclade_body = nextclade_proc_match.group("body")
    
    assert "--input-dataset" in nextclade_body, "process nextclade should use --input-dataset"
    assert "--output-json nextclade.json" in nextclade_body, "process nextclade should output nextclade.json"
    assert "--output-csv consensus.errors.csv" in nextclade_body, "process nextclade should output consensus.errors.csv"
    assert "nextclade.version" in nextclade_body, "process nextclade should record version to nextclade.version"


def test_main_nf_staging_channel_wiring():
    main_text = (WF_DIR / "main.nf").read_text()
    
    # Check pipeline wiring: when params.update_data is true/false, staged data is created/routed
    assert "getNextcladeData" in main_text, "getNextcladeData should be invoked in main.nf"
    assert "update_data" in main_text, "update_data should guard the nextclade staging channel"


# --- 4. CLI Parameters & Schema Compatibility ---

def test_cli_parameters_in_nextflow_schema():
    schema_path = WF_DIR / "nextflow_schema.json"
    assert schema_path.exists(), "nextflow_schema.json not found"
    
    with open(schema_path, "r") as f:
        schema = json.load(f)
        
    jsonschema.Draft7Validator.check_schema(schema)
    
    # Check required nextclade parameters exist in schema
    adv_props = schema.get("definitions", {}).get("advanced_options", {}).get("properties", {})
    assert "update_data" in adv_props, "update_data missing in schema advanced_options"
    assert "nextclade_data_tag" in adv_props, "nextclade_data_tag missing in schema advanced_options"
    
    rep_props = schema.get("definitions", {}).get("reporting_options", {}).get("properties", {})
    assert "report_clade" in rep_props, "report_clade missing in schema reporting_options"


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
