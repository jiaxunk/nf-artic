import os
import re
import subprocess
import sys
from pathlib import Path
import pytest

WF_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WF_DIR / "bin"))

try:
    from workflow_glue.util import normalize_medaka_model
except ImportError:
    normalize_medaka_model = None


# --- 1. Dynamic Model Normalization Unit Tests ---

@pytest.mark.parametrize("dorado_model,expected_medaka_model", [
    ("dna_r10.4.1_e8.2_400bps_hac@v5.2.0", "r1041_e82_400bps_hac_v5.2.0"),
    ("dna_r10.4.1_e8.2_400bps_sup@v4.2.0", "r1041_e82_400bps_sup_v4.2.0"),
    ("dna_r10.4.1_e8.2_400bps_hac@v4.3.0", "r1041_e82_400bps_hac_v4.3.0"),
    ("dna_r10.4.1_e8.2_400bps_sup@v5.0.0", "r1041_e82_400bps_sup_v5.0.0"),
    ("dna_r10.4.1_e8.2_400bps_sup@v5.2.0", "r1041_e82_400bps_sup_v5.2.0"),
    ("dna_r10.4.1_e8.2_400bps_sup@v6.0.0", "r1041_e82_400bps_sup_v6.0.0"),
    ("dna_r10.4.1_e8.2_400bps_hac@v6.0.0", "r1041_e82_400bps_hac_v6.0.0"),
    ("dna_r10.4.1_e8.2_260bps_hac@v5.0.0", "r1041_e82_260bps_hac_v5.0.0"),
    ("dna_r10.4.1_e8.2_260bps_sup@v4.0.0", "r1041_e82_260bps_sup_v4.0.0"),
    ("dna_r10.4.1_e8.2_400bps_fast@v5.0.0", "r1041_e82_400bps_fast_v5.0.0"),
])
def test_normalize_dorado_models(dorado_model, expected_medaka_model):
    assert normalize_medaka_model is not None, "normalize_medaka_model not implemented"
    result = normalize_medaka_model(dorado_model)
    assert result == expected_medaka_model, f"Expected {expected_medaka_model}, got {result}"


@pytest.mark.parametrize("guppy_model,expected_medaka_model", [
    ("dna_r9.4.1_450bps_hac", "r941_min_hac_g507"),
    ("dna_r9.4.1_450bps_sup", "r941_min_sup_g507"),
    ("dna_r9.4.1_450bps_fast", "r941_min_fast_g303"),
    ("dna_r9.4.1_e8_hac@v3.3", "r941_min_hac_g507"),
    ("dna_r9.4.1_e8_sup@v3.3", "r941_min_sup_g507"),
])
def test_normalize_legacy_guppy_models(guppy_model, expected_medaka_model):
    assert normalize_medaka_model is not None, "normalize_medaka_model not implemented"
    result = normalize_medaka_model(guppy_model)
    assert result == expected_medaka_model, f"Expected {expected_medaka_model}, got {result}"


@pytest.mark.parametrize("direct_model,expected_medaka_model", [
    ("r1041_e82_400bps_sup_v5.0.0", "r1041_e82_400bps_sup_v5.0.0"),
    ("r1041_e82_400bps_hac_v5.2.0", "r1041_e82_400bps_hac_v5.2.0"),
    ("r941_min_hac_g507", "r941_min_hac_g507"),
    ("r941_min_high_g360", "r941_min_high_g360"),
    ("r941_min_high_g360:consensus", "r941_min_high_g360"),
    ("r1041_e82_400bps_sup_v5.0.0:consensus", "r1041_e82_400bps_sup_v5.0.0"),
])
def test_direct_medaka_models_and_legacy_suffix_strip(direct_model, expected_medaka_model):
    assert normalize_medaka_model is not None, "normalize_medaka_model not implemented"
    result = normalize_medaka_model(direct_model)
    assert result == expected_medaka_model, f"Expected {expected_medaka_model}, got {result}"


@pytest.mark.parametrize("file_path", [
    "/opt/models/r1041_custom.tar.gz",
    "./my_model.tar.gz",
    "../models/custom_medaka",
    "s3://bucket/model.tar.gz",
])
def test_direct_model_file_paths(file_path):
    assert normalize_medaka_model is not None, "normalize_medaka_model not implemented"
    result = normalize_medaka_model(file_path)
    assert result == file_path, f"Direct file path should not be altered: expected {file_path}, got {result}"


# --- 2. CLI Normalization Subcommand ---

def test_workflow_glue_cli_normalize_model():
    glue_script = WF_DIR / "bin" / "workflow-glue"
    cmd = [
        sys.executable,
        str(glue_script),
        "normalize_model",
        "dna_r10.4.1_e8.2_400bps_hac@v5.2.0"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"workflow-glue normalize_model failed: {res.stderr}"
    assert res.stdout.strip() == "r1041_e82_400bps_hac_v5.2.0"


# --- 3. Pipeline Integration Tests (main.nf & run_artic.sh) ---

def test_main_nf_basecall_model_passing():
    main_text = (WF_DIR / "main.nf").read_text()
    # In runArtic process, basecall_model should NOT have hardcoded :consensus suffix appended
    assert "${basecall_model}:consensus" not in main_text, (
        "main.nf still appends legacy ':consensus' suffix to basecall_model in runArtic"
    )
    assert "${basecall_model}" in main_text, "main.nf should pass basecall_model to run_artic.sh"


def test_run_artic_normalizes_model():
    script_text = (WF_DIR / "bin" / "run_artic.sh").read_text()
    assert "normalize_model" in script_text or "workflow-glue" in script_text or "normalize_medaka_model" in script_text, (
        "run_artic.sh should normalize the input medaka model using workflow-glue normalize_model"
    )


# --- 4. Modernized Dockerfile Tests ---

def test_dockerfile_exists_and_contains_packages():
    dockerfile_path = WF_DIR / "Dockerfile"
    assert dockerfile_path.exists(), "Dockerfile must exist in wf-artic"

    content = dockerfile_path.read_text()
    # Check essential tools
    assert "medaka" in content, "Dockerfile must install medaka"
    assert "artic" in content, "Dockerfile must install artic"
    assert "samtools" in content, "Dockerfile must install samtools"
    assert "bcftools" in content, "Dockerfile must install bcftools"
    assert "minimap2" in content, "Dockerfile must install minimap2"
    assert "workflow-glue" in content or "workflow_glue" in content or "bin" in content, "Dockerfile must include workflow-glue"


# --- 5. Config Parameterization Tests ---

def test_nextflow_config_container_parameter():
    config_text = (WF_DIR / "nextflow.config").read_text()
    # Check params.wf.artic_container definition
    assert "artic_container" in config_text, "params.wf.artic_container should be defined in nextflow.config"

    # Check process withLabel:artic uses artic_container
    artic_label_match = re.search(r"withLabel:\s*artic\s*\{[^}]*container\s*=\s*['\"]([^'\"]+)['\"]", config_text)
    assert artic_label_match is not None, "withLabel:artic container not found"
    assert "artic_container" in artic_label_match.group(1), (
        f"withLabel:artic container should use artic_container, got '{artic_label_match.group(1)}'"
    )

    # Validate nextflow config syntax
    res = subprocess.run(["nextflow", "config", "."], cwd=str(WF_DIR), capture_output=True, text=True)
    assert res.returncode == 0, f"nextflow config failed:\n{res.stderr}\n{res.stdout}"
