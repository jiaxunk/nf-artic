"""Tests for basecaller model normalization to Clair3 models."""
import pytest
from workflow_glue.util import normalize_basecaller_model


@pytest.mark.parametrize(
    "input_model,expected",
    [
        # Modern Dorado R10.4.1 models
        ("dna_r10.4.1_e8.2_400bps_sup@v5.0.0", "r1041_e82_400bps_sup_v500"),
        ("dna_r10.4.1_e8.2_400bps_hac@v5.0.0", "r1041_e82_400bps_hac_v500"),
        ("dna_r10.4.1_e8.2_400bps_sup@v5.2.0", "r1041_e82_400bps_sup_v520"),
        ("dna_r10.4.1_e8.2_400bps_hac@v5.2.0", "r1041_e82_400bps_hac_v520"),
        ("dna_r10.4.1_e8.2_400bps_sup@v4.3.0", "r1041_e82_400bps_sup_v430"),
        ("dna_r10.4.1_e8.2_400bps_hac@v4.3.0", "r1041_e82_400bps_hac_v430"),
        ("dna_r10.4.1_e8.2_400bps_sup@v4.2.0", "r1041_e82_400bps_sup_v420"),
        ("dna_r10.4.1_e8.2_400bps_hac@v4.2.0", "r1041_e82_400bps_hac_v420"),
        ("dna_r10.4.1_e8.2_400bps_sup@v4.1.0", "r1041_e82_400bps_sup_v410"),
        ("dna_r10.4.1_e8.2_400bps_hac@v4.1.0", "r1041_e82_400bps_hac_v410"),
        ("dna_r10.4.1_e8.2_400bps_sup@v4.0.0", "r1041_e82_400bps_sup_v400"),
        ("dna_r10.4.1_e8.2_400bps_hac@v4.0.0", "r1041_e82_400bps_hac_v400"),
        ("dna_r10.4.1_e8.2_400bps_hac@v6.0.0", "r1041_e82_400bps_hac_v600"),
        # Legacy Guppy / R9.4.1 models
        ("dna_r9.4.1_450bps_hac", "r941_prom_hac_g360+g422"),
        ("dna_r9.4.1_450bps_sup", "r941_prom_sup_g5014"),
        ("dna_r9.4.1_e8_hac@v3.3", "r941_prom_hac_g360+g422"),
        ("dna_r9.4.1_e8_sup@v3.3", "r941_prom_sup_g5014"),
        ("r941_min_hac_g507", "r941_prom_hac_g360+g422"),
        # Direct canonical Clair3 models (passed directly)
        ("r941_prom_hac_g360+g422", "r941_prom_hac_g360+g422"),
        ("r1041_e82_400bps_sup_v500", "r1041_e82_400bps_sup_v500"),
        ("r1041_e82_400bps_hac_v520", "r1041_e82_400bps_hac_v520"),
    ],
)
def test_normalize_basecaller_model(input_model, expected):
    assert normalize_basecaller_model(input_model) == expected
