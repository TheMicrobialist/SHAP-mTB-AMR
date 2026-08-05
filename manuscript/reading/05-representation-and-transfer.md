# 05 — Representation and transfer learning

**Gap 5, highest ceiling, highest cost.** The Discussion argues the
position-encoded SNP matrix is structurally unsuited to pyrazinamide: *pncA*
loss-of-function substitutions spread across the whole gene with no hotspots, so
each causal variant is individually rare and no column carries signal. No amount
of model tuning fixes a representation problem.

Realistically a **next-paper direction**, not a revision item.

---

## Try first — cheaper, same target

### 1. Per-gene loss-of-function aggregation · **highest expected value here**

- **Gives** — collapses rare per-position variants into a shared functional signal: frameshift, premature stop, known deleterious substitution
- **Use for** — the *pncA* problem directly — many rare variants, one consequence
- **Needs** — feature engineering only; no deep learning, no new data
- **Effort** — low (days)

### 2. Protein-level encoding

- **Gives** — amino-acid change instead of nucleotide
- **Use for** — a representation closer to the biology
- **Needs** — mostly built: `lookup_position` in `scripts/shap_agent.py` already computes codon and residue from `reference/H37Rv.fasta`
- **Effort** — low–medium

---

## Pretrained genomic models

### Ji et al. 2021 — DNABERT
Bioinformatics 37(15):2112–2120 · [doi:10.1093/bioinformatics/btab083](https://doi.org/10.1093/bioinformatics/btab083) · PMID 33538820

- **Gives** — BERT for DNA via k-mer tokenisation, pretrain-then-finetune; transfers across organisms
- **Use for** — fine-tuning template; test whether sequence-level representation of the nine AMR genes beats per-position encoding, most plausibly for PZA
- **Needs** — GPU; sequence extraction per isolate rather than the current matrix
- **Effort** — high

### Dalla-Torre et al. 2025 — Nucleotide Transformer
Nature Methods 22(2):287–297 · [doi:10.1038/s41592-024-02523-z](https://doi.org/10.1038/s41592-024-02523-z) · PMID 39609566

- **Gives** — genomics foundation models with careful downstream evaluation, including **how much fine-tuning data is actually needed**
- **Use for** — deciding whether this route is viable at 9,798 isolates. Check their low-data results **before** investing compute
- **Needs** — GPU
- **Effort** — high

---

## Do this

1. Build per-gene loss-of-function features; re-run pyrazinamide.
2. If that helps, add amino-acid encoding using the existing codon machinery.
3. Only then evaluate pretrained models — and check Nucleotide Transformer's
   low-data results first.

Steps 1–2 are within reach of the current codebase. Step 3 is a separate
project; framing it that way in future-work is more credible than promising it
as an imminent extension.
