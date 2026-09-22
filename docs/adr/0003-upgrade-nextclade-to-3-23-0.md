# 3. Upgrade Nextclade to 3.23.0 and Refresh SARS-CoV-2 Dataset

Date: 2026-09-22

## Status

Accepted

## Context

The pipeline was configured with `nextstrain/nextclade:3.8.2` and an offline pre-bundled SARS-CoV-2 dataset frozen on `2024-02-16T04-00-32Z`. Newer Nextstrain clade definitions, recombinant lineages, and Pango annotations required updating to Nextclade v3.23.0 and refreshing the bundled offline dataset.

## Decision

1. Upgrade `nextclade_container` in `nextflow.config` to `nextstrain/nextclade:3.23.0`.
2. Bundle the latest SARS-CoV-2 dataset `2026-09-07--17-10-15Z` in `data/nextclade/datasets/sarscov2/`.
3. Normalize dataset tag parsing in `main.nf` to support both ISO `T` timestamps (`yyyy-MM-dd'T'HH-mm-ss'Z'`) and double-dash `--` Nextclade tag formats seamlessly.

## Consequences

- Up-to-date clade and lineage classifications for contemporary SARS-CoV-2 variants.
- Full offline execution capability with current 2026 reference trees.
- Seamless compatibility with dynamic dataset retrieval via `--update_data true`.
