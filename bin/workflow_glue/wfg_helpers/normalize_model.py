"""Workflow glue helper to normalize basecaller model strings to Medaka models."""
from ..util import normalize_medaka_model, wf_parser


def argparser():
    """Make an argument parser."""
    parser = wf_parser("normalize_model")
    parser.add_argument("model", help="Basecaller model string or file path")
    return parser


def main(args):
    """Entry point for CLI."""
    normalized = normalize_medaka_model(args.model)
    print(normalized)
