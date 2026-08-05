# 01. Lineage and population structure

**Blocking gap.** The cross-drug attribution result is the paper's only novelty
claim and is currently uninterpretable: a pooled, lineage-agnostic design cannot
separate biology from population-structure confounding.

---

### Napier et al. 2020: lineage assignment · **start here**
Genome Medicine 12(1):114 · [doi:10.1186/s13073-020-00817-3](https://doi.org/10.1186/s13073-020-00817-3) · PMID 33317631

- **Gives**: 90-SNP barcode, 9 lineages + 3 animal species, from 35,298 isolates; implemented in TB-Profiler
- **Use for**: assigning a lineage to each of the 9,798 isolates
- **Needs**: the existing per-sample VCFs only; no new sequencing, no new tooling
- **Effort**: low

### Coll et al. 2014: original barcode
Nature Communications 5:4812 · [doi:10.1038/ncomms5812](https://doi.org/10.1038/ncomms5812) · PMID 25176035

- **Gives**: the 62-SNP scheme Napier updates; rationale for choosing lineage-defining SNPs
- **Use for**: justifying the approach in Methods, not for the marker set itself
- **Needs**: nothing; background reading
- **Effort**: low

### Shitikov & Bespiatykh 2023: revised scheme
mSphere 8(4):e0016923 · [doi:10.1128/msphere.00169-23](https://doi.org/10.1128/msphere.00169-23) · PMID 37314207

- **Gives**: a more recent barcode revision
- **Use for**: checking which scheme reviewers will expect before committing
- **Needs**: nothing
- **Effort**: low

### Billows et al. 2023: the correction method · *already cited, never used*
Bioinformatics 39(7):btad428 · [doi:10.1093/bioinformatics/btad428](https://doi.org/10.1093/bioinformatics/btad428) · PMID 37428143

- **Gives**: three lineage corrections evaluated on this exact task: stratification, feature selection, Feature-Weighted Random Forest
- **Use for**: the experimental design of this gap; FW-RF applies directly since the pipeline already uses random forests
- **Needs**: lineage labels from Napier first
- **Effort**: medium

---

## Do this

1. Assign lineages with the Napier barcode from existing VCFs.
2. Report cohort lineage composition in Table 1. Its absence is a reviewer's first question regardless of what else follows.
3. Re-run per-drug models with stratification and with feature weighting.
4. Re-run cross-drug SHAP within lineage strata.

**Step 4 is the point.** Shifts vanish → publishable negative result on a
confound the field ignores. Shifts survive → a genuine finding. Either beats
not knowing.
