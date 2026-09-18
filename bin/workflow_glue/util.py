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


def normalize_medaka_model(model: str) -> str:
    """Translate Dorado/MinKNOW/Guppy basecaller model strings into canonical Medaka model strings.

    Supports:
    - Modern Dorado models (e.g. dna_r10.4.1_e8.2_400bps_hac@v5.2.0 -> r1041_e82_400bps_hac_v5.2.0)
    - Legacy Guppy models (e.g. dna_r9.4.1_450bps_hac -> r941_min_hac_g507)
    - Direct Medaka model strings (e.g. r1041_e82_400bps_sup_v5.0.0)
    - Direct file paths / archive URLs (passed untouched)
    - Cleanly strips legacy :consensus suffix if present
    """
    import re

    if not model:
        return model

    model = str(model).strip()

    # 1. Direct file paths or URIs
    if "/" in model or "\\" in model or model.endswith((".tar.gz", ".hdf5", ".pt", ".onnx", ".tar")):
        return model

    # 2. Strip legacy :consensus / :variant suffix
    if ":" in model:
        model = model.split(":")[0]

    # 3. If already a canonical Medaka model identifier
    if re.match(r"^(r1041_|r941_|r103_|r94_)[a-zA-Z0-9_\.]+$", model) and "@" not in model:
        return model

    # 4. Check for legacy R9 / Guppy models
    if "r9.4.1" in model or "r941" in model:
        if "hac" in model:
            return "r941_min_hac_g507"
        elif "sup" in model:
            return "r941_min_sup_g507"
        elif "fast" in model:
            return "r941_min_fast_g303"
        elif "high" in model:
            return "r941_min_high_g360"

    # 5. Translate modern Dorado models (e.g., dna_r10.4.1_e8.2_400bps_hac@v5.2.0)
    res = re.sub(r"^dna_", "", model)
    res = res.replace("@", "_")
    res = re.sub(r"r10\.4\.1", "r1041", res)
    res = re.sub(r"r9\.4\.1", "r941", res)
    res = re.sub(r"e8\.([0-9])", r"e8\1", res)

    return res

