#!/bin/bash
set -euox pipefail

sample_name=$1
fastq_file=$2
min_len=$3
max_len=$4
basecall_model=$5
scheme_name=$6
scheme_dir=$7
scheme_version=$8
threads=$9
max_softclip_length=${10}
normalise=${11}

# Normalize basecaller model string to canonical Clair3 model format
if command -v workflow-glue >/dev/null 2>&1; then
    clair3_model=$(workflow-glue normalize_model "${basecall_model}" 2>/dev/null || echo "${basecall_model}")
elif command -v python3 >/dev/null 2>&1; then
    clair3_model=$(python3 -c "
import sys
sys.path.insert(0, '/workspace/bin')
sys.path.insert(0, '$(dirname $0)')
try:
    from workflow_glue.util import normalize_basecaller_model
    print(normalize_basecaller_model('${basecall_model}'))
except Exception:
    print('${basecall_model}')
" 2>/dev/null || echo "${basecall_model}")
else
    clair3_model="${basecall_model}"
fi

function mock_artic {
    echo "Mocking artic results"
    TAB="$(echo -e '\t')"
    cat << EOF | bgzip > "${sample_name}.pass.vcf.gz"
##fileformat=VCFv4.2
##source=Clair3 v2.0.2
#CHROM${TAB}POS${TAB}ID${TAB}REF${TAB}ALT${TAB}QUAL${TAB}FILTER${TAB}INFO${TAB}FORMAT${TAB}SAMPLE
EOF
    cp "${sample_name}.pass.vcf.gz" "${sample_name}.merged.gvcf.vcf.gz"
    echo -e ">${sample_name} Artic-Fail\nN" > "${sample_name}.consensus.fasta"
}

# Locate reference FASTA and scheme BED files
bed_file=""
ref_file=""

for candidate in \
    "${scheme_dir}/${scheme_version}/${scheme_name}.scheme.bed" \
    "${scheme_dir}/${scheme_name}/${scheme_version}/${scheme_name}.scheme.bed" \
    "${scheme_dir}/${scheme_name}.scheme.bed" \
    $(find "${scheme_dir}" -name "*scheme.bed" -o -name "*.bed" 2>/dev/null | head -n 1); do
    if [[ -n "${candidate:-}" ]] && [[ -f "${candidate}" ]]; then
        bed_file="${candidate}"
        break
    fi
done

for candidate in \
    "${scheme_dir}/${scheme_version}/${scheme_name}.reference.fasta" \
    "${scheme_dir}/${scheme_name}/${scheme_version}/${scheme_name}.reference.fasta" \
    "${scheme_dir}/${scheme_name}.reference.fasta" \
    $(find "${scheme_dir}" -name "*reference.fasta" -o -name "*.fasta" 2>/dev/null | head -n 1); do
    if [[ -n "${candidate:-}" ]] && [[ -f "${candidate}" ]]; then
        ref_file="${candidate}"
        break
    fi
done

if [[ -z "${bed_file}" ]] || [[ -z "${ref_file}" ]]; then
    echo "Error: Could not locate primer scheme BED or reference FASTA in '${scheme_dir}'" >&2
    exit 1
fi

echo "Using scheme BED: ${bed_file}"
echo "Using reference FASTA: ${ref_file}"

# Format scheme BED to 7 columns required by primalbedtools
python3 -c "
with open('${bed_file}') as fin, open('scheme7.bed', 'w') as fout:
    for line in fin:
        parts = line.strip().split()
        if not parts: continue
        if len(parts) == 5:
            strand = '+' if 'LEFT' in parts[3] or 'fwd' in parts[3].lower() else '-'
            parts.extend([strand, '.'])
        elif len(parts) == 6:
            parts.append('.')
        fout.write('\t'.join(parts) + '\n')
"

# Organize FASTQ input into sample directory for guppyplex
if [[ -d "${fastq_file}" ]]; then
    READ_DIR="${fastq_file}"
else
    mkdir -p "${sample_name}"
    if [[ "${fastq_file}" != "${sample_name}/${sample_name}.fastq.gz" ]]; then
        cp -L "${fastq_file}" "${sample_name}/${sample_name}.fastq.gz" 2>/dev/null || ln -sf "${fastq_file}" "${sample_name}/${sample_name}.fastq.gz"
    fi
    READ_DIR="${sample_name}"
fi

artic guppyplex --skip-quality-check \
    --min-length "${min_len}" --max-length "${max_len}" \
    --directory "${READ_DIR}" --prefix "${sample_name}" \
    && echo " - artic guppyplex finished"

READFILE=$(ls -1 "${sample_name}_"*.fastq | head -n 1)

# Model directory containing bundled Clair3 models
MODEL_DIR="/opt/conda/envs/artic/bin/models"
if [[ ! -d "${MODEL_DIR}" ]]; then
    MODEL_DIR="/opt/conda/bin/models"
fi

echo "Running artic minion with model: ${clair3_model} from ${MODEL_DIR}"

artic minion \
    --model "${clair3_model}" \
    --model-dir "${MODEL_DIR}" \
    --normalise "${normalise}" \
    --threads "${threads}" \
    --read-file "${READFILE}" \
    --bed scheme7.bed \
    --ref "${ref_file}" \
    "${sample_name}" \
    || mock_artic

# Format and index VCF outputs
if [[ -f "${sample_name}.merged.vcf.gz" ]] && [[ ! -f "${sample_name}.merged.gvcf.vcf.gz" ]]; then
    cp "${sample_name}.merged.vcf.gz" "${sample_name}.merged.gvcf.vcf.gz"
fi

for vcf_set in "pass" "merged.gvcf"; do
    if [[ -f "${sample_name}.${vcf_set}.vcf.gz" ]]; then
        zcat "${sample_name}.${vcf_set}.vcf.gz" | sed "s/SAMPLE/${sample_name}/" | bgzip -c > "${sample_name}.${vcf_set}.named.vcf.gz"
        bcftools index -t "${sample_name}.${vcf_set}.named.vcf.gz"
    fi
done

# Standardize consensus header
if [[ -f "${sample_name}.consensus.fasta" ]]; then
    sed -i "s/^>\S*/>${sample_name}/" "${sample_name}.consensus.fasta"
fi

# Ensure trimmed BAM channels are present
if [[ -f "${sample_name}.primertrimmed.rg.sorted.bam" ]]; then
    cp -L "${sample_name}.primertrimmed.rg.sorted.bam" "${sample_name}.trimmed.rg.sorted.bam" || ln -sf "${sample_name}.primertrimmed.rg.sorted.bam" "${sample_name}.trimmed.rg.sorted.bam"
    cp -L "${sample_name}.primertrimmed.rg.sorted.bam.bai" "${sample_name}.trimmed.rg.sorted.bam.bai" || ln -sf "${sample_name}.primertrimmed.rg.sorted.bam.bai" "${sample_name}.trimmed.rg.sorted.bam.bai"
fi

# Calculate strand depth stats across primer pools on 20bp stepped grid
python3 -c "
import pysam, os

bam_path = '${sample_name}.primertrimmed.rg.sorted.bam'
ref_path = '${ref_file}'
sample = '${sample_name}'

ref_dict = {}
if os.path.exists(bam_path) and os.path.getsize(bam_path) > 0:
    try:
        samfile = pysam.AlignmentFile(bam_path, 'rb')
        ref_dict = dict(zip(samfile.references, samfile.lengths))
    except Exception:
        ref_dict = {}

if not ref_dict and os.path.exists(ref_path):
    try:
        with pysam.FastxFile(ref_path) as fa:
            for entry in fa:
                ref_dict[entry.name] = len(entry.sequence)
    except Exception:
        pass

with open(f'{sample}.depth.txt', 'w') as out_f:
    out_f.write('ref\tpos\tdepth\tdepth_fwd\tdepth_rev\tsample_name\tprimer_set\n')
    for rname, rlen in ref_dict.items():
        grid_points = range(0, rlen, 20)
        grid_set = set(grid_points)
        counts = {1: {p: [0, 0] for p in grid_points}, 2: {p: [0, 0] for p in grid_points}}

        if os.path.exists(bam_path) and os.path.getsize(bam_path) > 0:
            try:
                samfile = pysam.AlignmentFile(bam_path, 'rb')
                for col in samfile.pileup(rname, stepper='nofilter', min_base_quality=0, max_depth=100000):
                    pos = col.reference_pos
                    if pos in grid_set:
                        for read in col.pileups:
                            al = read.alignment
                            if al.is_unmapped or al.is_secondary or al.is_supplementary:
                                continue
                            rg = al.get_tag('RG') if al.has_tag('RG') else None
                            try:
                                pset = int(rg)
                            except (ValueError, TypeError):
                                continue
                            if pset in counts:
                                if al.is_reverse:
                                    counts[pset][pos][1] += 1
                                else:
                                    counts[pset][pos][0] += 1
            except Exception:
                pass

        for pset in [1, 2]:
            for pos in grid_points:
                fwd, rev = counts[pset][pos]
                tot = fwd + rev
                out_f.write(f'{rname}\t{pos}\t{tot}\t{fwd}\t{rev}\t{sample}\t{pset}\n')
"

