# 01 — Lineage and population structure

**Gap 1, the blocking one.** The cross-drug attribution result is the paper's
only novelty claim and is currently uninterpretable: with a pooled,
lineage-agnostic design it is as consistent with population-structure
confounding as with biology. These papers give the tools to settle it.

---

### Napier et al. 2020 — the practical tool for assigning lineage

*Robust barcoding and identification of Mycobacterium tuberculosis lineages for
epidemiological and clinical studies.*
**Genome Medicine 2020;12(1):114** · [doi:10.1186/s13073-020-00817-3](https://doi.org/10.1186/s13073-020-00817-3) · PMID 33317631

90 SNP markers covering 9 main lineages and 3 animal-related species, derived
from 35,298 isolates and implemented in TB-Profiler.

**Use it for:** assigning a lineage to each of the 9,798 isolates directly from
the VCFs already produced. This is the concrete first step of gap 1 and needs no
new sequencing — the barcode positions can be read from existing per-sample
VCFs. Start here.

### Coll et al. 2014 — the original barcode

*A robust SNP barcode for typing Mycobacterium tuberculosis complex strains.*
**Nature Communications 2014;5:4812** · [doi:10.1038/ncomms5812](https://doi.org/10.1038/ncomms5812) · PMID 25176035

The 62-SNP scheme Napier et al. updates. Read for the rationale — how
lineage-defining SNPs are chosen and why they are phylogenetically robust —
rather than for the marker set itself.

### Shitikov & Bespiatykh 2023 — a revised scheme

*A revised SNP-based barcoding scheme for typing Mycobacterium tuberculosis
complex isolates.*
**mSphere 2023;8(4):e0016923** · [doi:10.1128/msphere.00169-23](https://doi.org/10.1128/msphere.00169-23) · PMID 37314207

A more recent revision. Worth checking which scheme reviewers will expect
before committing; cite whichever is used and say why.

---

### Billows et al. 2023 — the method, already cited

*Feature weighted models to address lineage dependency in drug-resistance
prediction from Mycobacterium tuberculosis genome sequences.*
**Bioinformatics 2023;39(7):btad428** · [doi:10.1093/bioinformatics/btad428](https://doi.org/10.1093/bioinformatics/btad428) · PMID 37428143

Already in `references.bib` and cited in the Discussion — but only as an
acknowledgement that the problem exists. It evaluates three concrete
corrections (stratification, feature selection, feature-weighted random forest)
on this exact task and data type.

**Use it for:** the actual experimental design of gap 1. Feature-Weighted Random
Forest is directly applicable, since the pipeline already uses random forests.
Reproducing their comparison on the FORUM-TB matrix would be a real result,
whichever correction wins.

---

## What to do with this

1. Assign lineages with the Napier barcode from the existing VCFs.
2. Report lineage composition of the cohort — this belongs in Table 1 regardless
   of what else follows, and its absence is currently a reviewer's first question.
3. Re-run per-drug models with stratification and with feature weighting,
   following Billows et al.
4. Re-run the cross-drug SHAP analysis within lineage strata, and report whether
   the attribution shifts survive.

Step 4 is the one that matters. If the shifts vanish, that is a publishable
negative result and the paper becomes honest about a confound the field
routinely ignores. If they survive, the paper has a genuine finding. Either
outcome is better than the current position of not knowing.
