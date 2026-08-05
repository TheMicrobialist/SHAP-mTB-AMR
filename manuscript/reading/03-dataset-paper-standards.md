# 03 — Dataset paper standards

**Hard requirements for NeurIPS Evaluations & Datasets.** Mechanical, not
scientific — which is why it should be done early, not in deadline week.

---

### Croissant — **required, and we don't have one**
NeurIPS 2024 Datasets & Benchmarks Track ·
[paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/9547b09b722f2948ff3ddb5d86002bc0-Paper-Datasets_and_Benchmarks_Track.pdf) ·
[MLCommons](https://mlcommons.org/working-groups/data/croissant/)

- **Gives** — JSON-LD metadata format for ML datasets; supported natively by Hugging Face, Kaggle, OpenML
- **Use for** — `ml_matrix.croissant.json`. NeurIPS requires it in **every** dataset-track submission
- **Needs** — the **Responsible AI extension fields**, not just base format. Dataset is already on HF, so this may be configuration rather than authoring
- **Effort** — low

### Gebru et al. 2021 — Datasheets for Datasets
CACM 64(12):86–92 · [doi:10.1145/3458723](https://doi.org/10.1145/3458723) · [arXiv:1803.09010](https://arxiv.org/abs/1803.09010)

- **Gives** — questionnaire on provenance, collection method, intended and out-of-scope use
- **Use for** — the part Croissant explicitly does **not** cover: cohort definition and collection methodology. Forces per-source documentation of the heterogeneous DST methods and critical concentrations the Discussion currently only concedes in prose
- **Needs** — tracing label provenance back to source studies
- **Effort** — medium (the tracing, not the writing)

### Mitchell et al. 2019 — Model Cards
FAccT 2019, pp. 220–229 · [doi:10.1145/3287560.3287596](https://doi.org/10.1145/3287560.3287596)

- **Gives** — per-model reporting: intended use, out-of-scope use, disaggregated performance, ethics
- **Use for** — the four released `.joblib` models. Disaggregated performance is the relevant part — per-lineage, per-drug rather than one pooled AUC
- **Needs** — lineage labels from `01` for the disaggregation
- **Effort** — low

---

## Do this

1. Generate Croissant + Responsible AI fields for the feature matrix.
2. Mint a permanent DOI (Zenodo) — a GitHub path is not an acceptable dataset citation.
3. Write a datasheet; document label provenance per source study honestly.
4. Write model cards; disaggregate once `01` is done.
5. **Prepare an anonymised release** — repo, Hugging Face Space, and the author names in the dashboard landing text all currently identify the authors.

Item 5 is easy to forget and fatal at a double-blind deadline. Plan it early.
