"""The odd helper function.

Be careful what you place in here. This file is imported into all glue.
"""
import argparse
import logging


_log_name = None


def get_main_logger(name):
    """Create the top-level logger."""
    global _log_name
    _log_name = name
    logging.basicConfig(
        format='[%(asctime)s - %(name)s] %(message)s',
        datefmt='%H:%M:%S', level=logging.INFO)
    return logging.getLogger(name)


def get_named_logger(name):
    """Create a logger with a name.

    :param name: name of logger.
    """
    name = name.ljust(10)[:10]  # so logging is aligned
    logger = logging.getLogger('{}.{}'.format(_log_name, name))
    return logger


def wf_parser(name):
    """Make an argument parser for a workflow command."""
    return argparse.ArgumentParser(
        name,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False)


def _log_level():
    """Parser to set logging level and acquire software version/commit."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, add_help=False)

    modify_log_level = parser.add_mutually_exclusive_group()
    modify_log_level.add_argument(
        '--debug', action='store_const',
        dest='log_level', const=logging.DEBUG, default=logging.INFO,
        help='Verbose logging of debug information.')
    modify_log_level.add_argument(
        '--quiet', action='store_const',
        dest='log_level', const=logging.WARNING, default=logging.INFO,
        help='Minimal logging; warnings only.')

    return parser


def normalize_basecaller_model(model: str) -> str:
    """Translate Dorado/MinKNOW/Guppy basecaller model strings into canonical Clair3 model identifiers.

    Supports:
    - Modern Dorado R10.4.1 models (e.g. dna_r10.4.1_e8.2_400bps_sup@v5.0.0 -> r1041_e82_400bps_sup_v500)
    - Legacy Guppy / R9.4.1 models (e.g. dna_r9.4.1_450bps_hac -> r941_prom_hac_g360+g422)
    - Direct Clair3 model identifiers (e.g. r1041_e82_400bps_sup_v520)
    - Direct file paths / archive URLs (passed untouched)
    """
    import re

    if not model:
        return model

    model = str(model).strip()

    # 1. Direct file paths or URIs
    if "/" in model or "\\" in model or model.endswith((".tar.gz", ".hdf5", ".pt", ".onnx", ".tar")):
        return model

    # 2. Strip legacy :consensus / :variant suffix if present
    if ":" in model:
        model = model.split(":")[0]

    # 3. Direct canonical Clair3 models
    if re.match(r"^(r1041_|r941_|r104_|ont_|hifi_|ilmn_)[a-zA-Z0-9_\+\.]+$", model) and "@" not in model:
        # Check if legacy min / fast string
        if "min_hac" in model or "min_fast" in model or "min_high" in model:
            return "r941_prom_hac_g360+g422"
        elif "min_sup" in model:
            return "r941_prom_sup_g5014"
        return model

    # 4. Check for legacy R9 / Guppy models
    if "r9.4.1" in model or "r941" in model:
        if "sup" in model.lower():
            return "r941_prom_sup_g5014"
        return "r941_prom_hac_g360+g422"

    # 5. Translate modern Dorado models (e.g. dna_r10.4.1_e8.2_400bps_sup@v5.0.0 -> r1041_e82_400bps_sup_v500)
    res = re.sub(r"^dna_", "", model)
    # Convert @vX.Y.Z -> _vXYZ (e.g. @v5.0.0 -> _v500, @v5.2.0 -> _v520)
    m = re.search(r"@v(\d+)\.(\d+)\.(\d+)", res)
    if m:
        version_suffix = f"_v{m.group(1)}{m.group(2)}{m.group(3)}"
        res = re.sub(r"@v\d+\.\d+\.\d+", version_suffix, res)
    else:
        res = res.replace("@", "_")

    res = re.sub(r"r10\.4\.1", "r1041", res)
    res = re.sub(r"r9\.4\.1", "r941", res)
    res = re.sub(r"e8\.([0-9])", r"e8\1", res)

    return res


# Backward-compatibility alias
normalize_medaka_model = normalize_basecaller_model


