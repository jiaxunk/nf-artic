# 2. Upgrade to staphb/artic:1.11.1 with Clair3

Date: 2026-09-22

## Status

Accepted

## Context

The legacy `nf-artic` pipeline relied on `ontresearch/wf-artic` with ARTIC v1.2.1 and Medaka/Longshot variant calling. Medaka was deprecated by the ARTIC Network starting in ARTIC v1.5.0+, replacing Medaka with Clair3 and modern alignment/filtering utilities (`primalbedtools`, `artic_vcf_merge`, `artic_vcf_filter`).

Modern sequencing runs also produce Oxford Nanopore R10.4.1 flowcell data basecalled by Dorado (SUP/HAC models), which were not supported by legacy Medaka models.

## Decision

1. Upgrade the core alignment, trimming, and variant calling engine from `jiaxunk/nf-artic:latest` to `staphb/artic:1.11.1`.
2. Map both Dorado R10.4.1/R9.4.1 basecaller strings and Guppy strings to native bundled Clair3 models in `/opt/conda/envs/artic/bin/models/`.
3. Auto-format 5- and 6-column primer scheme BED files to 7 columns (`chrom`, `start`, `end`, `name`, `pool`, `strand`, `sequence`/placeholder `.`) on the fly for compatibility with `primalbedtools`.
4. Decouple HTML report generation (`label "report"`) from core ARTIC calling (`label "artic"`).

## Consequences

- Direct support for both legacy R9.4.1 and modern R10.4.1 sequencing chemistries without needing external model downloads.
- Accurate and fast variant calling with Clair3.
- Maintained backwards compatibility with existing EPI2ME Desktop and Nextflow pipeline ingress.
