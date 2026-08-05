# 05 — Representation and transfer learning

**Gap 5, and the direction with the highest ceiling.** The Discussion argues the
position-encoded SNP matrix is structurally unsuited to pyrazinamide: *pncA*
resistance comes from loss-of-function substitutions spread across the whole gene
with no hotspots, so each causal variant is individually rare and no single
column carries signal. That is a representation problem, and no amount of model
tuning fixes it.

This is realistically a **next-paper direction** rather than a revision item.
Included because it is where the work goes if it continues.

---

## Pretrained genomic models

### Ji et al. 2021 — DNABERT

**Bioinformatics 2021;37(15):2112–2120** ·
[doi:10.1093/bioinformatics/btab083](https://doi.org/10.1093/bioinformatics/btab083) · PMID 33538820

BERT for DNA using k-mer tokenisation, pretrained then fine-tuned per task. The
paper reports that a model pretrained on the human genome transfers usefully to
other organisms.

**Use it for:** the fine-tuning template. The relevant question for FORUM-TB is
whether a sequence-level representation of the nine AMR genes outperforms
per-position encoding — most plausibly for pyrazinamide, where the encoding
demonstrably fails.

### Dalla-Torre et al. 2025 — Nucleotide Transformer

**Nature Methods 2025;22(2):287–297** ·
[doi:10.1038/s41592-024-02523-z](https://doi.org/10.1038/s41592-024-02523-z) · PMID 39609566

Foundation models for genomics with a careful evaluation across many downstream
tasks, including how much fine-tuning data is actually needed.

**Use it for:** deciding whether this route is viable at 9,798 isolates. Their
low-data fine-tuning results are the relevant evidence — a foundation-model
approach is only worth attempting if it works at this sample size, and their
paper is the place to check before investing.

---

## Cheaper alternatives worth trying first

Foundation models are the fashionable answer, not necessarily the right one.
Two lower-cost changes target the same failure and should be tried first:

1. **Variant-level aggregation.** Collapse per-position columns into per-gene
   loss-of-function indicators — frameshift, premature stop, known
   deleterious substitution. This directly addresses the *pncA* problem
   (many rare variants, one shared functional consequence) without any deep
   learning, and is a few days of feature engineering.

2. **Protein-level features.** Encode the amino-acid change rather than the
   nucleotide. The agent's `lookup_position` tool already computes codon and
   residue from `reference/H37Rv.fasta`, so most of this machinery exists —
   see `scripts/shap_agent.py`.

Option 1 is the highest expected value in this whole file: cheap, directly
motivated by the paper's own diagnosis, and likely to move the pyrazinamide
number. It should be tried before anything involving a transformer.

---

## What to do with this

1. Build per-gene loss-of-function aggregate features and re-run pyrazinamide.
2. If that helps, add amino-acid-level encoding using the existing codon
   machinery.
3. Only then evaluate whether a pretrained genomic model beats either — and
   check the Nucleotide Transformer low-data results first to decide whether it
   is worth the compute.

Steps 1 and 2 are within reach of the current codebase. Step 3 is a separate
project, and framing it that way in the paper's future-work section is more
credible than promising it as an imminent extension.
