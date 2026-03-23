#!/bin/bash

# Usage:
# process_tb_sample.sh RUN_ID FASTQ_DIR QC_DIR BAM_DIR VCF_DIR REF


set -euo pipefail

# ---------- Resume protection ----------
# If final VCF already exists, skip this sample
RUN_ID=$1
FASTQ_DIR=$2
QC_DIR=$3
BAM_DIR=$4
VCF_DIR=$5
REF=$6

if [ -f "$VCF_DIR/${RUN_ID}.vcf.gz" ]; then
    echo "${RUN_ID} already processed. Skipping."
    exit 0
fi

THREADS=${THREADS:-8}

# Ensure output directories exist 
mkdir -p "$QC_DIR"
mkdir -p "$BAM_DIR"
mkdir -p "$VCF_DIR"

# Print paths for debugging in SLURM logs
echo "FASTQ_DIR: $FASTQ_DIR"
echo "QC_DIR: $QC_DIR"
echo "BAM_DIR: $BAM_DIR"
echo "VCF_DIR: $VCF_DIR"
echo "RUN_ID: $RUN_ID"

# ---------- 1. Use existing FASTQ ----------

FASTQ1="$FASTQ_DIR/${RUN_ID}_1.fastq.gz"
FASTQ2="$FASTQ_DIR/${RUN_ID}_2.fastq.gz"

if [ ! -f "$FASTQ1" ]; then
    echo "FASTQ R1 not found for $RUN_ID. Skipping."
    exit 1
fi

# Detect paired-end or single-end
if [ -f "$FASTQ2" ]; then
    PAIRED=1
else
    echo "R2 not found for $RUN_ID. Proceeding as single-end."
    PAIRED=0
fi

# ---------- 2. QC ----------
if [ "$PAIRED" -eq 1 ]; then
    fastp \
      -i "$FASTQ1" \
      -I "$FASTQ2" \
      -o "$QC_DIR/${RUN_ID}_1.clean.fastq" \
      -O "$QC_DIR/${RUN_ID}_2.clean.fastq" \
      --thread "$THREADS" \
      --detect_adapter_for_pe \
      --qualified_quality_phred 20 \
      --length_required 30
else
    fastp \
      -i "$FASTQ1" \
      -o "$QC_DIR/${RUN_ID}.clean.fastq" \
      --thread "$THREADS" \
      --qualified_quality_phred 20 \
      --length_required 30
fi

# ---------- 3. Alignment ----------
if [ "$PAIRED" -eq 1 ]; then
    bwa mem -t "$THREADS" "$REF" \
      "$QC_DIR/${RUN_ID}_1.clean.fastq" \
      "$QC_DIR/${RUN_ID}_2.clean.fastq" | \
      samtools sort -@ "$THREADS" -o "$BAM_DIR/${RUN_ID}.bam"
else
    bwa mem -t "$THREADS" "$REF" \
      "$QC_DIR/${RUN_ID}.clean.fastq" | \
      samtools sort -@ "$THREADS" -o "$BAM_DIR/${RUN_ID}.bam"
fi

samtools index "$BAM_DIR/${RUN_ID}.bam"

# ---------- 4. Variant calling ----------
bcftools mpileup -Ou -f "$REF" "$BAM_DIR/${RUN_ID}.bam" | \
  bcftools call -mv -Oz -o "$VCF_DIR/${RUN_ID}.vcf.gz"

bcftools index "$VCF_DIR/${RUN_ID}.vcf.gz"

# ---------- 5. Cleanup large intermediates ----------
# Do NOT delete FASTQ (stored in /scratch for reuse)
rm -f "$QC_DIR/${RUN_ID}_1.clean.fastq" "$QC_DIR/${RUN_ID}_2.clean.fastq" "$QC_DIR/${RUN_ID}.clean.fastq"
rm -f "$BAM_DIR/${RUN_ID}.bam" "$BAM_DIR/${RUN_ID}.bam.bai"

echo "[$RUN_ID] pipeline finished successfully"
