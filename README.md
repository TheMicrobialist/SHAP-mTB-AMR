# FORUM-TB: An ML-Ready Whole-Genome SNP Matrix for *M. tuberculosis* Drug Resistance Prediction

## Dataset Summary

FORUM-TB is an open-access, machine-learning-ready feature matrix derived from whole-genome sequencing (WGS) of *Mycobacterium tuberculosis* isolates. It provides nucleotide-encoded SNP features across nine known antimicrobial resistance (AMR) genes, paired with drug resistance phenotype labels for four first-line anti-tuberculosis drugs. The dataset is designed to enable reproducible benchmarking of ML models for TB drug resistance prediction, without requiring raw sequencing data or bioinformatics expertise.

**Key numbers:**
- 9,798 isolates (global, publicly available)
- 2,693 genomic features (AMR gene positions)
- 4 drug resistance labels (Rifampicin, Isoniazid, Ethambutol, and Pyrazinamide)
- 247 KB compressed

---

## Motivation 

Drug-resistant tuberculosis (DR-TB) remains a critical global health challenge. Current diagnostic tools are either too slow (culture-based DST: 3–16 weeks), too limited in drug coverage (GeneXpert: rifampicin only), or lack explainability (rule-based WGS tools). This dataset was created to support the development of interpretable machine learning models that can predict multi-drug resistance profiles from genomic data, moving beyond rule-based catalogues toward data-driven, explainable approaches.

---

## Dataset Details

### Data Source

Raw FASTQ files were downloaded from the European Nucleotide Archive (ENA) and NCBI Sequence Read Archive (SRA).

All source data are publicly available and de-identified. No patient-identifiable information is included.

### Processing Pipeline

All processing was performed on the Digital Research Alliance of Canada (CCDB) HPC cluster using the following tools:

| Step | Tool | Version | Parameters |
|---|---|---|---|
| Quality control | fastp | 1.0.1 | default |
| Alignment | BWA-MEM | 0.7.18 | default |
| Variant calling | bcftools call | 1.22 | default |
| VCF filtering | bcftools filter | 1.22 | QUAL≥20, MQ≥30 |
| Reference genome | H37Rv | NC_000962.3 | — |

Full pipeline code is available at:
https://github.com/TheMicrobialist/SHAP-mTB-AMR (v0.2.0)

### Feature Engineering

From 705,226 unique variant positions across the genome, features were filtered to:

1. **SNPs only** — single nucleotide changes (len(REF)==1 and len(ALT)==1); indels excluded
2. **AMR genes only** — positions intersected with H37Rv GFF annotation (GCF_000195955.2), restricted to nine known resistance genes:

| Drug | Genes |
|---|---|
| RIFAMPICIN | rpoB |
| ISONIAZID | katG, inhA, fabG1 |
| ETHAMBUTOL | embB, embA, embC |
| PYRAZINAMIDE | pncA, rpsA |

3. **Outlier removal** — 3 samples with >10,000 variants removed (likely contamination or MiSeq platform artefacts): ERR1034652, ERR1035353, ERR1213920

### Encoding

Nucleotides are encoded as integers in a single column per position:

| Value | Meaning |
|---|---|
| 0 | REF (reference allele, same as H37Rv) |
| 1 | A |
| 2 | T |
| 3 | C |
| 4 | G |

Missing variant calls (position not in VCF for a sample) are assumed to be REF and encoded as 0.

---

## File Format

`ml_matrix.csv.gz` — gzip-compressed CSV file

**Columns:**
- `SAMPLE` — SRA/ENA run accession (e.g. ERR038266)
- `pos_XXXXXX` — 2,693 genomic position columns (nucleotide encoded 0–4)
- `ISONIAZID` — resistance label (1=Resistant, 0=Susceptible, blank=unknown)
- `RIFAMPICIN` — resistance label
- `ETHAMBUTOL` — resistance label
- `PYRAZINAMIDE` — resistance label

**Dimensions:** 9,799 rows × 2,697 columns (9,798 samples + 1 header)

**Load in Python:**
```python
import pandas as pd
df = pd.read_csv("ml_matrix.csv.gz", index_col="SAMPLE")

# Features
X = df[[c for c in df.columns if c.startswith("pos_")]]

# Labels for one drug
y = df["RIFAMPICIN"].dropna().astype(int)
X = X.loc[y.index]
```

---

## Resistance Label Coverage

| Drug | Labelled samples | Resistant | Susceptible |
|---|---|---|---|
| RIFAMPICIN | 9,630 | 7,144 (74.2%) | 2,486 (25.8%) |
| ISONIAZID | 9,580 | 8,238 (86.0%) | 1,342 (14.0%) |
| ETHAMBUTOL | 8,196 | 4,082 (49.8%) | 4,114 (50.2%) |
| PYRAZINAMIDE | 5,749 | 2,610 (45.4%) | 3,139 (54.6%) |

---

## Benchmark Results

Random Forest classifier (n=300 trees, balanced class weights, 5-fold stratified CV):

| Drug | Test Accuracy | AUC-ROC | CV AUC-ROC |
|---|---|---|---|
| RIFAMPICIN | 95.0% | 0.975 | 0.969 ± 0.004 |
| ISONIAZID | 90.5% | 0.948 | 0.946 ± 0.008 |
| ETHAMBUTOL | 81.2% | 0.894 | 0.900 ± 0.007 |
| PYRAZINAMIDE | 81.9% | 0.886 | 0.883 ± 0.007 |

**Biological validation:** Top SHAP features confirmed against known resistance mutations:
- `pos_761155` → rpoB codon 450 → **S450L** (C→T) — most prevalent rifampicin resistance mutation globally
- `pos_2155168` → katG codon 315 → **S315T** (C→G) — most prevalent isoniazid resistance mutation globally
- `pos_4247429` → embB codon 306 → **M306I/V** — most common ethambutol resistance mutation

Full benchmark scripts: `scripts/rf_shap_v2.py`

---

## Intended Use

This dataset is intended for:
- Benchmarking ML models for TB AMR prediction
- Explainability research (SHAP, LIME, interaction networks)
- Training and evaluation of resistance prediction algorithms
- Reproducible science and open TB genomics research

---

## Authors

| Name | Location | Contact |
|---|---|---|
| Noah LeGall, Ph.D. | San Diego, CA, USA |   |
| Nanzhen (Aspen) Qiao, Ph.D. | Kingston, ON, Canada |  |

---

## License

**Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**

---

## Related Resources

- GitHub repository: https://github.com/TheMicrobialist/SHAP-mTB-AMR
- The Microbialist blog: https://themicrobialist.substack.com