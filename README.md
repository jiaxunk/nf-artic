# Artic Network SARS-CoV-2 Analysis (`nf-artic`)

Run the ARTIC SARS-CoV-2 methodology on Oxford Nanopore sequencing data.

---

## Introduction

> [!IMPORTANT]
> **Deprecation Notice of `wf-artic` & Purpose of `nf-artic`**
> The original [`wf-artic`](https://github.com/epi2me-labs/wf-artic) workflow developed by Oxford Nanopore Technologies (ONT) EPI2ME Labs is **officially deprecated** and no longer actively maintained.
> 
> **`nf-artic`** is developed and maintained as an **immediate, modernized, drop-in replacement** for `wf-artic`. It preserves full compatibility with the EPI2ME Desktop environment and command-line workflows while upgrading core bioinformatics tools and resolving long-standing upstream issues.

### Key Modernizations from `wf-artic` to `nf-artic`

- **Clair3-powered ARTIC Engine**: Migrated from legacy `medaka` to `Clair3` (via `staphb/artic:1.11.1` / ARTIC FieldBioinformatics), delivering state-of-the-art consensus accuracy and native support for R10.4.1 (and R9.4.1) chemistries.
- **Nextclade 3.23.0 & 2026 Datasets**: Upgraded Nextclade to `v3.23.0` with the latest bundled offline dataset (61 clades, >5,000 Pango lineages) alongside dynamic runtime update capabilities (`--update_data true`).
- **Automated Dorado / Guppy Basecaller Model Mapping**: Automatically detects Dorado / Guppy basecaller models from FASTQ headers and maps them to appropriate Clair3 model checkpoints (`--override_basecaller_cfg` supported for manual overrides).
- **Robust Multi-Pool Coverage Handling**: Standardized uniform 20bp stepped coverage depth grids across the entire reference genome, preventing report failures on low-coverage or single-pool dropout samples.
- **EPI2ME Desktop Compatibility**: Fully conforms to the modern EPI2ME JSON schema and sample sheet specifications.

---

## Compute requirements

Recommended requirements:

+ CPUs = 4
+ Memory = 8GB

Minimum requirements:

+ CPUs = 2
+ Memory = 4GB

Approximate run time: 5 minutes per sample

ARM processor support: False

---

## Install and run

These are instructions to install and run the workflow on command line.
You can also access the workflow via the
[EPI2ME Desktop application](https://labs.epi2me.io/downloads/).

The workflow uses [Nextflow](https://www.nextflow.io/) to manage
compute and software resources,
therefore Nextflow will need to be
installed before attempting to run the workflow.

The workflow can currently be run using either
[Docker](https://www.docker.com/products/docker-desktop)
or [Singularity](https://docs.sylabs.io/guides/3.0/user-guide/index.html)
to provide isolation of the required software.
Both methods are automated out-of-the-box provided
either Docker or Singularity is installed.
This is controlled by the
[`-profile`](https://www.nextflow.io/docs/latest/config.html#config-profiles)
parameter as exemplified below.

It is not required to clone or download the git repository
in order to run the workflow.
More information on running EPI2ME workflows can
be found on the [EPI2ME website](https://labs.epi2me.io/wfindex).

The following command can be used to obtain the workflow.
This will pull the repository into the assets folder of
Nextflow and provide a list of all parameters
available for the workflow as well as an example command:

```bash
nextflow run jiaxunk/nf-artic --help
```

To update the workflow to the latest version on the command line, use:
```bash
nextflow pull jiaxunk/nf-artic
```

### Running with Demo Data

A demo dataset is provided for testing of the workflow:
```bash
wget https://github.com/jiaxunk/nf-artic/releases/download/v1.0.0/nf-artic-demo.tar.gz
tar -xzvf nf-artic-demo.tar.gz
```

The workflow can then be run with the downloaded demo data using:
```bash
nextflow run jiaxunk/nf-artic \
    --fastq 'nf-artic-demo/fastq' \
    --sample_sheet 'nf-artic-demo/sample_sheet.csv' \
    --scheme_name 'SARS-CoV-2' \
    --scheme_version 'Midnight-ONT/V3' \
    -profile standard
```

---

## Related protocols

This workflow is designed to take input sequences that have been produced from [Oxford Nanopore Technologies](https://nanoporetech.com/) devices.

The Midnight protocol for sample preparation and sequencing can be found in the [Nanopore community](https://community.nanoporetech.com/docs/prepare/library_prep_protocols/pcr-tiling-of-sars-cov-2-virus-rbk114-and-midnight-rt/v/mrt_9186_v114_revd_19apr2023).

---

## Input example

This workflow accepts FASTQ files as input.

The FASTQ input parameters for this workflow accept one of three cases: (i) the path to a single FASTQ; (ii) the path to a top-level directory containing FASTQ files; (iii) the path to a directory containing one level of sub-directories which in turn contain FASTQ files. In the first and second cases (i and ii), a sample name can be supplied with `--sample`. In the last case (iii), the data is assumed to be multiplexed with the names of the sub-directories as barcodes. In this case, a sample sheet can be provided with `--sample_sheet`.

```text
(i)                     (ii)                 (iii)    
input_reads.fastq   ─── input_directory  ─── input_directory
                        ├── reads0.fastq     ├── barcode01
                        └── reads1.fastq     │   ├── reads0.fastq
                                             │   └── reads1.fastq
                                             ├── barcode02
                                             │   ├── reads0.fastq
                                             │   ├── reads1.fastq
                                             │   └── reads2.fastq
                                             └── barcode03
                                                 └── reads0.fastq
```

---

## Input parameters

### Input Options

| Nextflow parameter name  | Type | Description | Help | Default |
|--------------------------|------|-------------|------|---------|
| fastq | string | FASTQ files to use in the analysis. | Path to FASTQ file or directory containing multiplexed sub-directories. | |
| analyse_unclassified | boolean | Analyse unclassified reads from input directory. | If selected and if input is multiplexed, unclassified reads are also processed. | False |

### Primer Scheme Selection

| Nextflow parameter name  | Type | Description | Help | Default |
|--------------------------|------|-------------|------|---------|
| scheme_name | string | Primer scheme name. | Set to `SARS-CoV-2` or a custom scheme name. | SARS-CoV-2 |
| scheme_version | string | Primer scheme version. | Supported schemes include `ARTIC/V3`, `ARTIC/V4.1`, `ARTIC/V5.3.2`, `Midnight-ONT/V3`, `NEB-VarSkip/v2`, etc. | ARTIC/V3 |
| custom_scheme | string | Path to a custom scheme. | Path to directory containing `<SCHEME_NAME>.scheme.bed` and `<SCHEME_NAME>.reference.fasta`. | |

### Sample Options

| Nextflow parameter name  | Type | Description | Help | Default |
|--------------------------|------|-------------|------|---------|
| sample_sheet | string | CSV file mapping barcodes to aliases. | Requires `barcode` and `alias` columns. | |
| sample | string | Single sample name for non-multiplexed data. | Permissible when passing a single FASTQ file or folder. | |

### Output Options

| Nextflow parameter name  | Type | Description | Default |
|--------------------------|------|-------------|---------|
| out_dir | string | Directory for output of all workflow results. | output |

### Reporting Options

| Nextflow parameter name  | Type | Description | Default |
|--------------------------|------|-------------|---------|
| report_depth | integer | Min. depth for percentage coverage in report. | 100 |
| report_clade | boolean | Show Nextclade clade assignment in report. | True |
| report_coverage | boolean | Show genome coverage plots in report. | True |
| report_lineage | boolean | Show Pangolin lineage assignment in report. | True |
| report_variant_summary | boolean | Show variant table in report. | True |

### Advanced Options

| Nextflow parameter name  | Type | Description | Help | Default |
|--------------------------|------|-------------|------|---------|
| artic_threads | number | CPU threads per ARTIC task. | | 4 |
| pangolin_threads | number | CPU threads per Pangolin task. | | 4 |
| update_data | boolean | Update Nextclade/Pangolin datasets at runtime. | When set to `false`, pre-bundled offline datasets are used. | True |
| override_basecaller_cfg | string | Override auto-detected basecaller model. | Used to manually specify a Clair3 model (e.g. `r1041_e82_400bps_sup_v500`). | |
| normalise | integer | Depth ceiling for coverage normalisation. | | 200 |
| min_len | number | Minimum read length (default: set by scheme). | | |
| max_len | number | Maximum read length (default: set by scheme). | | |

---

## Outputs

Output files may be aggregated or provided per sample (prefixed with `{{ alias }}`):

| Title | File path | Description | Type |
|-------|-----------|-------------|------|
| Workflow report | `nf-artic-report.html` | Interactive HTML report for all samples. | aggregated |
| Consensus sequences | `all_consensus.fasta` | Final consensus FASTA for all samples. | aggregated |
| Pangolin results | `lineage_report.csv` | Pangolin lineage and scorpio assignment CSV. | aggregated |
| Nextclade results | `nextclade.json` | Nextclade clade, mutations, and QC metrics. | aggregated |
| Coverage data | `all_depth.txt` | 20bp binned coverage depth matrix. | aggregated |
| Variants | `{{ alias }}.pass.named.vcf.gz` | High confidence PASS variants. | per-sample |
| Variants index | `{{ alias }}.pass.named.vcf.gz.tbi` | Tabix index for variants VCF. | per-sample |
| Alignments | `{{ alias }}.primertrimmed.rg.sorted.bam` | Primer-trimmed mapped BAM alignments. | per-sample |
| Alignments index | `{{ alias }}.primertrimmed.rg.sorted.bam.bai` | BAM index. | per-sample |

---

## Pipeline overview

The pipeline wraps the [ARTIC Network](https://artic.network/) [FieldBioinformatics](https://github.com/artic-network/fieldbioinformatics) analysis workflow:

1. **Ingress & QC**: FASTQ files are validated and summarized using `fastcat`.
2. **Alignment & Primer Trimming**: Reads are aligned to the reference genome with `minimap2` and primer binding regions are soft-clipped / trimmed.
3. **Variant Calling & Consensus Polishing**: High-confidence variants and consensus sequences are generated using `Clair3` neural network models.
4. **Clade & Lineage Assignment**: Final consensus sequences are annotated with `Nextclade` (v3.23.0) and `Pangolin`.
5. **Reporting**: A rich, standalone HTML report (`nf-artic-report.html`) and JSON payload (`artic.json`) are generated.

---

## FAQ & Issue Tracker

If you encounter issues or have feature requests, please submit an issue on the [GitHub Issues](https://github.com/jiaxunk/nf-artic/issues) page.

---

> [!NOTE]
> **AI Assistance Disclaimer**
> This workflow was modernized and maintained with the assistance of AI pair-programming agents (Google Antigravity / DeepMind). All pipeline logic, schema definitions, and containerized processes have been validated against Oxford Nanopore Technologies (ONT) EPI2ME standards.
