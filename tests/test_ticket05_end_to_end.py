import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

WF_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def sample_sheet_run_output(tmp_path_factory):
    """Run full Nextflow pipeline with sample sheet and return output directory."""
    out_dir = tmp_path_factory.mktemp("test_e2e_samplesheet")
    cmd = [
        "nextflow", "run", "main.nf",
        "-profile", "standard",
        "--fastq", "test_data/fastq",
        "--sample_sheet", "test_data/sample_sheet.csv",
        "--override_basecaller_cfg", "dna_r9.4.1_e8_hac@v3.3",
        "--out_dir", str(out_dir),
        "-resume"
    ]
    res = subprocess.run(cmd, cwd=str(WF_DIR), capture_output=True, text=True)
    assert res.returncode == 0, f"Pipeline execution failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    return out_dir


@pytest.fixture(scope="session")
def multiplex_auto_model_output(tmp_path_factory):
    """Run full Nextflow pipeline without sample sheet (auto Dorado model extraction)."""
    out_dir = tmp_path_factory.mktemp("test_e2e_multiplex_auto")
    cmd = [
        "nextflow", "run", "main.nf",
        "-profile", "standard",
        "--fastq", "test_data/fastq",
        "--out_dir", str(out_dir),
        "-resume"
    ]
    res = subprocess.run(cmd, cwd=str(WF_DIR), capture_output=True, text=True)
    assert res.returncode == 0, f"Pipeline auto model execution failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    return out_dir


# --- 1. End-to-End Pipeline Output File Generation Tests ---

def test_pipeline_generates_all_core_outputs_with_sample_sheet(sample_sheet_run_output):
    """Verify all mandatory output files are created with sample sheet execution."""
    out_dir = sample_sheet_run_output
    expected_files = [
        "nf-artic-report.html",
        "all_consensus.fasta",
        "all_variants.vcf.gz",
        "versions.txt",
        "lineage_report.csv",
        "nextclade.json",
        "all_depth.txt",
        "metadata.json",
        "artic.json",
    ]
    for fname in expected_files:
        fpath = out_dir / fname
        assert fpath.exists(), f"Expected output file '{fname}' was not generated in {out_dir}"
        assert fpath.stat().st_size > 0, f"Output file '{fname}' is empty"


def test_pipeline_generates_all_core_outputs_multiplex_auto(multiplex_auto_model_output):
    """Verify all mandatory output files are created with multiplexed auto-model execution."""
    out_dir = multiplex_auto_model_output
    expected_files = [
        "nf-artic-report.html",
        "all_consensus.fasta",
        "all_variants.vcf.gz",
        "versions.txt",
        "lineage_report.csv",
        "nextclade.json",
        "all_depth.txt",
    ]
    for fname in expected_files:
        fpath = out_dir / fname
        assert fpath.exists(), f"Expected output file '{fname}' was not generated in {out_dir}"
        assert fpath.stat().st_size > 0, f"Output file '{fname}' is empty"


# --- 2. Output Content & Integrity Validation Tests ---

def test_versions_txt_content(sample_sheet_run_output):
    """Verify versions.txt records modern tool versions."""
    versions_file = sample_sheet_run_output / "versions.txt"
    content = versions_file.read_text()
    assert "medaka," in content, "medaka version missing from versions.txt"
    assert "minimap2," in content, "minimap2 version missing from versions.txt"
    assert "bcftools," in content, "bcftools version missing from versions.txt"
    assert "samtools," in content, "samtools version missing from versions.txt"
    assert "artic," in content, "artic version missing from versions.txt"


def test_html_report_validity(sample_sheet_run_output):
    """Verify standalone HTML report content."""
    html_file = sample_sheet_run_output / "nf-artic-report.html"
    content = html_file.read_text(encoding="utf-8", errors="ignore")
    assert "<!DOCTYPE html>" in content or "<html" in content, "Report is not a valid HTML document"
    assert "SARS-CoV-2" in content or "ARTIC" in content or "sample" in content, "Report missing expected text"


def test_nextclade_json_validity(sample_sheet_run_output):
    """Verify nextclade.json is valid JSON with clade results."""
    json_file = sample_sheet_run_output / "nextclade.json"
    with open(json_file, "r") as f:
        data = json.load(f)
    assert isinstance(data, (dict, list)), "nextclade.json is not a valid JSON structure"


def test_lineage_report_csv_validity(sample_sheet_run_output):
    """Verify lineage_report.csv has expected header and entries."""
    csv_file = sample_sheet_run_output / "lineage_report.csv"
    with open(csv_file, mode="r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        assert header is not None, "lineage_report.csv is empty"
        assert "taxon" in header or "sample_name" in header or "lineage" in header, (
            f"Unexpected header in lineage_report.csv: {header}"
        )


def test_all_consensus_fasta_validity(sample_sheet_run_output):
    """Verify all_consensus.fasta contains FASTA headers for samples."""
    fasta_file = sample_sheet_run_output / "all_consensus.fasta"
    content = fasta_file.read_text()
    assert content.startswith(">"), "all_consensus.fasta does not start with a FASTA header '>'"
    assert "SRR12480552" in content or "SRR12447502" in content, "Expected sample aliases missing in consensus FASTA"


# --- 3. Dynamic Dorado Model & Override Basecaller Cfg Tests ---

def test_override_basecaller_cfg_in_artic_logs(sample_sheet_run_output):
    """Verify override_basecaller_cfg passed the normalized model into artic runs."""
    log_files = list(sample_sheet_run_output.glob("*.artic.log.txt"))
    assert len(log_files) > 0, "No *.artic.log.txt found in output"
    for log_path in log_files:
        log_content = log_path.read_text()
        assert "r941_min_hac_g507" in log_content, (
            f"Normalized Medaka model 'r941_min_hac_g507' not found in {log_path.name}"
        )


def test_auto_dorado_model_in_multiplex_artic_logs(multiplex_auto_model_output):
    """Verify automatic Dorado model extraction from FASTQ headers in multiplex run."""
    log_files = list(multiplex_auto_model_output.glob("*.artic.log.txt"))
    assert len(log_files) > 0, "No *.artic.log.txt found in multiplex output"
    for log_path in log_files:
        log_content = log_path.read_text()
        assert "r941_min_hac_g507" in log_content, (
            f"Extracted/normalized Medaka model 'r941_min_hac_g507' not found in {log_path.name}"
        )
