import json
import re
import subprocess
from pathlib import Path
import pytest
import jsonschema

WF_DIR = Path(__file__).resolve().parent.parent

def test_manifest_name_in_nextflow_config():
    config_text = (WF_DIR / "nextflow.config").read_text()
    
    # Check manifest.name is 'nf-artic'
    match = re.search(r"manifest\s*\{[^}]*name\s*=\s*['\"]([^'\"]+)['\"]", config_text, re.DOTALL)
    assert match is not None, "manifest block with name not found in nextflow.config"
    assert match.group(1) in ["jiaxunk/nf-artic", "nf-artic"], f"Expected manifest name 'jiaxunk/nf-artic', got '{match.group(1)}'"

def test_epi2melabs_tags_in_nextflow_config():
    config_text = (WF_DIR / "nextflow.config").read_text()
    match = re.search(r"epi2melabs\s*\{[^}]*tags\s*=\s*['\"]([^'\"]+)['\"]", config_text, re.DOTALL)
    assert match is not None, "epi2melabs block with tags not found in nextflow.config"
    tags = [t.strip() for t in match.group(1).split(",")]
    assert "nf-artic" in tags, f"Expected 'nf-artic' in epi2melabs.tags: {tags}"
    assert "faVirusCovid" in config_text, "Expected faVirusCovid icon in nextflow.config"

def test_nextflow_schema_json():
    schema_path = WF_DIR / "nextflow_schema.json"
    assert schema_path.exists(), "nextflow_schema.json not found"
    
    with open(schema_path, "r") as f:
        schema = json.load(f)
        
    assert schema.get("title") == "nf-artic", f"Expected schema title 'nf-artic', got '{schema.get('title')}'"
    
    # Verify schema validity
    jsonschema.Draft7Validator.check_schema(schema)
    
    # Parameter contract check
    assert "definitions" in schema
    assert "input" in schema["definitions"]
    assert "fastq" in schema["definitions"]["input"]["properties"]

def test_main_nf_report_naming():
    main_text = (WF_DIR / "main.nf").read_text()
    
    assert "wf-artic-report.html" not in main_text, "Found old wf-artic-report.html in main.nf"
    assert "wf-artic-*.html" not in main_text, "Found old wf-artic-*.html in main.nf"
    assert "nf-artic-report.html" in main_text, "Expected nf-artic-report.html in main.nf"
    assert "nf-artic-*.html" in main_text, "Expected nf-artic-*.html in main.nf"

def test_python_report_scripts():
    report_py = (WF_DIR / "bin/workflow_glue/report.py").read_text()
    assert '"wf-artic"' not in report_py, "Found 'wf-artic' in report.py"
    assert '"nf-artic"' in report_py, "Expected 'nf-artic' in report.py"
    
    report_error_py = (WF_DIR / "bin/workflow_glue/report_error.py").read_text()
    assert '"wf-artic"' not in report_error_py, "Found 'wf-artic' in report_error.py"
    assert '"nf-artic"' in report_error_py, "Expected 'nf-artic' in report_error.py"

def test_output_definition_json():
    output_def_path = WF_DIR / "output_definition.json"
    if output_def_path.exists():
        with open(output_def_path, "r") as f:
            output_def = json.load(f)
        report_file = output_def.get("files", {}).get("workflow-report", {}).get("filepath")
        assert report_file == "nf-artic-report.html", f"Expected report filepath 'nf-artic-report.html', got '{report_file}'"

def test_nextflow_config_syntax():
    result = subprocess.run(
        ["nextflow", "config", "."],
        cwd=str(WF_DIR),
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"nextflow config failed with error:\n{result.stderr}\n{result.stdout}"

def test_docs_and_readme():
    readme_text = (WF_DIR / "README.md").read_text()
    assert "The nf-artic workflow implements" in readme_text
    assert "nextflow run nf-artic --help" in readme_text
    assert "nf-artic-report.html" in readme_text
    
    intro_text = (WF_DIR / "docs/02_introduction.md").read_text()
    assert "The nf-artic workflow implements" in intro_text
    
    outputs_text = (WF_DIR / "docs/07_outputs.md").read_text()
    assert "nf-artic-report.html" in outputs_text

