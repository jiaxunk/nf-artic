# syntax=docker/dockerfile:1
FROM mambaorg/micromamba:1.5.8-jammy

LABEL maintainer="nf-artic developers"
LABEL description="Unified nf-artic container with modern Medaka 2.2.1, ARTIC pipeline, and workflow-glue"

USER root

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    bzip2 \
    ca-certificates \
    curl \
    git \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Medaka, ARTIC, HTSlib tools, and dependencies via Bioconda, Conda-Forge, and Nanoporetech channels
RUN micromamba install -y -n base -c conda-forge -c bioconda -c nanoporetech \
    python=3.10 \
    medaka \
    fastcat \
    samtools \
    bcftools \
    minimap2 \
    htslib \
    pysam \
    pandas \
    jinja2 \
    biopython \
    jsonschema \
    requests \
    pip \
    pomoxis \
    'artic<1.4' \
    && micromamba clean --all --yes

ENV PATH="/opt/conda/bin:$PATH"

# Install aplanat and clint using no-build-isolation
RUN pip install --no-cache-dir 'setuptools<70' wheel && \
    pip install --no-cache-dir --no-build-isolation \
        clint \
        aplanat

# Copy workflow scripts and workflow-glue package
COPY bin/run_artic.sh /usr/local/bin/run_artic.sh
COPY bin/get_nexclade_data.sh /usr/local/bin/get_nexclade_data.sh
COPY bin/workflow-glue /usr/local/bin/workflow-glue
COPY bin/workflow_glue /opt/conda/lib/python3.10/site-packages/workflow_glue

RUN chmod +x /usr/local/bin/run_artic.sh \
             /usr/local/bin/get_nexclade_data.sh \
             /usr/local/bin/workflow-glue

WORKDIR /data

USER $MAMBA_USER
CMD ["/bin/bash"]
