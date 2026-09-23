"""Unit tests for depth calculation and defensive report handling."""
import pandas as pd
import pytest
from pathlib import Path
from workflow_glue.report import output_json


@pytest.fixture
def sample_consensus_fasta(tmp_path):
    """Create a mock multi-sample consensus FASTA file."""
    fasta_path = tmp_path / "all_consensus.fasta"
    content = (
        ">barcode01 MN908947.3\n"
        "ATTAAAGGTTTATACCTTCCCAGGTAACAAACCAACCAACTTTCGATCTCTTGTAGATCT\n"
        ">barcode02 MN908947.3\n"
        "ATTAAAGGTTTATACCTTCCCAGGTAACAAACCAACCAACTTTCGATCTCTTGTAGATCT\n"
        ">barcode03 MN908947.3\n"
        "ATTAAAGGTTTATACCTTCCCAGGTAACAAACCAACCAACTTTCGATCTCTTGTAGATCT\n"
        ">barcode04 MN908947.3\n"
        "NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN\n"
    )
    fasta_path.write_text(content)
    return str(fasta_path)


def test_output_json_normal_both_pools(sample_consensus_fasta):
    """Test normal case with both Pool 1 and Pool 2 present."""
    data = {
        "ref": ["MN908947.3"] * 4,
        "pos": [0, 20, 0, 20],
        "depth": [100, 150, 80, 120],
        "depth_fwd": [50, 75, 40, 60],
        "depth_rev": [50, 75, 40, 60],
        "sample_name": ["barcode01"] * 4,
        "primer_set": [1, 1, 2, 2],
    }
    df = pd.DataFrame(data)
    readcounts = {"barcode01": 500}

    res = output_json(df, sample_consensus_fasta, readcounts)
    assert "data" in res
    assert len(res["data"]) == 4

    b01 = next(item for item in res["data"] if item["barcode"] == "barcode01")
    assert b01["barcode"] == "barcode01"
    assert b01["chromosome"] == "MN908947.3"
    assert b01["seqlen"] == 60
    assert b01["readcount"] == 500
    assert b01["ncount"] == 0
    assert len(b01["coverage"]) == 2

    # Check window 0 (pos 0: start 0, end 10)
    # [start, end, fwd, rev, rg1, rg2]
    row0 = b01["coverage"][0]
    assert row0[0] == 0   # start
    assert row0[1] == 10  # end
    assert row0[2] == 90  # fwd = 50 + 40
    assert row0[3] == 90  # rev = 50 + 40
    assert row0[4] == 100 # rg1
    assert row0[5] == 80  # rg2

    # Check window 1 (pos 20: start 10, end 60 after last-window adjustment)
    row1 = b01["coverage"][1]
    assert row1[0] == 10
    assert row1[1] == 60  # adjusted to seqlen (60)
    assert row1[2] == 135 # fwd = 75 + 60
    assert row1[3] == 135 # rev = 75 + 60
    assert row1[4] == 150 # rg1
    assert row1[5] == 120 # rg2


def test_output_json_missing_pool_2(sample_consensus_fasta):
    """Test dropout case where Pool 2 is missing (reproducing KeyError: 2 in unhandled code)."""
    data = {
        "ref": ["MN908947.3"] * 2,
        "pos": [0, 20],
        "depth": [100, 150],
        "depth_fwd": [50, 75],
        "depth_rev": [50, 75],
        "sample_name": ["barcode01"] * 2,
        "primer_set": [1, 1],
    }
    df = pd.DataFrame(data)
    readcounts = {"barcode01": 250}

    res = output_json(df, sample_consensus_fasta, readcounts)
    assert "data" in res

    b01 = next(item for item in res["data"] if item["barcode"] == "barcode01")
    assert len(b01["coverage"]) == 2
    row0 = b01["coverage"][0]
    assert row0[4] == 100 # rg1
    assert row0[5] == 0   # rg2 (missing pool 2 filled with 0)
    assert row0[2] == 50  # fwd
    assert row0[3] == 50  # rev


def test_output_json_missing_pool_1(sample_consensus_fasta):
    """Test dropout case where Pool 1 is missing."""
    data = {
        "ref": ["MN908947.3"] * 2,
        "pos": [0, 20],
        "depth": [80, 120],
        "depth_fwd": [40, 60],
        "depth_rev": [40, 60],
        "sample_name": ["barcode01"] * 2,
        "primer_set": [2, 2],
    }
    df = pd.DataFrame(data)
    readcounts = {"barcode01": 200}

    res = output_json(df, sample_consensus_fasta, readcounts)
    assert "data" in res

    b01 = next(item for item in res["data"] if item["barcode"] == "barcode01")
    assert len(b01["coverage"]) == 2
    row0 = b01["coverage"][0]
    assert row0[4] == 0   # rg1 (missing pool 1 filled with 0)
    assert row0[5] == 80  # rg2
    assert row0[2] == 40  # fwd
    assert row0[3] == 40  # rev


def test_output_json_string_primer_set(sample_consensus_fasta):
    """Test when primer_set column contains string values '1' and '2'."""
    data = {
        "ref": ["MN908947.3"] * 4,
        "pos": [0, 20, 0, 20],
        "depth": [100, 150, 80, 120],
        "depth_fwd": [50, 75, 40, 60],
        "depth_rev": [50, 75, 40, 60],
        "sample_name": ["barcode01"] * 4,
        "primer_set": ["1", "1", "2", "2"],
    }
    df = pd.DataFrame(data)
    readcounts = {"barcode01": 500}

    res = output_json(df, sample_consensus_fasta, readcounts)
    b01 = next(item for item in res["data"] if item["barcode"] == "barcode01")
    assert len(b01["coverage"]) == 2
    assert b01["coverage"][0][4] == 100
    assert b01["coverage"][0][5] == 80


def test_output_json_completely_empty_dataframe(sample_consensus_fasta):
    """Test completely empty depth dataframe."""
    df_empty_schema = pd.DataFrame(
        columns=["ref", "pos", "depth", "depth_fwd", "depth_rev", "sample_name", "primer_set"]
    )
    readcounts = {}

    res = output_json(df_empty_schema, sample_consensus_fasta, readcounts)
    assert "data" in res
    assert len(res["data"]) == 4
    for item in res["data"]:
        assert item["coverage"] == []

    # Test with totally bare empty dataframe
    res_bare = output_json(pd.DataFrame(), sample_consensus_fasta, readcounts)
    assert "data" in res_bare
    assert len(res_bare["data"]) == 4
    for item in res_bare["data"]:
        assert item["coverage"] == []


def test_output_json_multiple_samples_varying_pools(sample_consensus_fasta):
    """Test multiple samples with varying pool combinations (both pools, pool 1 only, pool 2 only, no reads)."""
    rows = [
        # barcode01: both pools
        {"ref": "MN908947.3", "pos": 0, "depth": 100, "depth_fwd": 50, "depth_rev": 50, "sample_name": "barcode01", "primer_set": 1},
        {"ref": "MN908947.3", "pos": 0, "depth": 80, "depth_fwd": 40, "depth_rev": 40, "sample_name": "barcode01", "primer_set": 2},
        # barcode02: pool 1 only
        {"ref": "MN908947.3", "pos": 0, "depth": 90, "depth_fwd": 45, "depth_rev": 45, "sample_name": "barcode02", "primer_set": 1},
        # barcode03: pool 2 only
        {"ref": "MN908947.3", "pos": 0, "depth": 70, "depth_fwd": 35, "depth_rev": 35, "sample_name": "barcode03", "primer_set": 2},
        # barcode04: no rows in depth df
    ]
    df = pd.DataFrame(rows)
    readcounts = {"barcode01": 300, "barcode02": 150, "barcode03": 120, "barcode04": 0}

    res = output_json(df, sample_consensus_fasta, readcounts)
    assert len(res["data"]) == 4

    data_map = {item["barcode"]: item for item in res["data"]}

    # barcode01: both pools present
    b01 = data_map["barcode01"]
    assert len(b01["coverage"]) == 1
    assert b01["coverage"][0][4] == 100 # rg1
    assert b01["coverage"][0][5] == 80  # rg2

    # barcode02: pool 1 only
    b02 = data_map["barcode02"]
    assert len(b02["coverage"]) == 1
    assert b02["coverage"][0][4] == 90  # rg1
    assert b02["coverage"][0][5] == 0   # rg2

    # barcode03: pool 2 only
    b03 = data_map["barcode03"]
    assert len(b03["coverage"]) == 1
    assert b03["coverage"][0][4] == 0   # rg1
    assert b03["coverage"][0][5] == 70  # rg2

    # barcode04: no coverage rows
    b04 = data_map["barcode04"]
    assert b04["coverage"] == []
    assert b04["ncount"] == 60
