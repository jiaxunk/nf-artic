# 4. Fix Depth Calculation and Defensive Report Pool Handling

Date: 2026-09-23

## Status

Accepted

## Context

When amplicon sequencing samples encounter primer pool dropout or zero mapped reads in one of the primer pools (e.g., Pool 2 has 0 reads), `workflow_glue.report.output_json()` crashed with `KeyError: 2` on `rg2 = group_by_primer.get_group(2)`.

Additionally, depth extraction in `bin/run_artic.sh` previously only emitted individual single-base coordinates with non-zero pileup depth. This omitted positions with 0 coverage and omitted dropped primer pools entirely from the depth table, resulting in inconsistent coordinate grids across pools and samples.

## Decision

1. **Defensive Report Handling (`bin/workflow_glue/report.py`)**:
   - Defensively query primer pool groupings for both integer (`1`, `2`) and string (`'1'`, `'2'`) pool identifiers.
   - Perform an outer join on `pos` between `rg1` and `rg2`, filling missing pool depths with `0`.
   - Ensure mandatory columns (`['pos', 'depth', 'depth_fwd', 'depth_rev']`) are present and sanitized before joining.
   - Guard against empty or schema-less dataframes by returning an empty coverage list for each consensus entry.
   - Safely cast `primer_set` to numeric during Bokeh plot generation to prevent type mismatches.

2. **20bp Stepped Coverage Grid (`bin/run_artic.sh`)**:
   - Implement a standardized 20bp stepped coverage grid (`pos = 0, 20, 40, ...`) across the full reference genome length for both Pool 1 and Pool 2.
   - Extract reference lengths from the BAM header or fallback to the reference FASTA file.
   - Populate forward, reverse, and total depth at each 20bp window coordinate, outputting zero-depth rows for unmapped or dropped regions to guarantee uniform matrix dimensions matching upstream `wf-artic`.

3. **Test-Driven Verification**:
   - Add unit test suite `bin/workflow_glue/tests/test_depth_and_report.py` verifying normal two-pool coverage, Pool 1 dropout, Pool 2 dropout, string pool identifiers, completely empty dataframes, and multi-sample combinations.

## Consequences

- Prevents pipeline crashes during HTML report and `artic.json` generation when samples suffer from severe amplicon pool dropout.
- Generates consistent, lightweight 20bp stepped coverage profiles across the entire reference genome.
- Preserves full backwards compatibility with EPI2ME Desktop JSON data contracts and Bokeh reporting components.
