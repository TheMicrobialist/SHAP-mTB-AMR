# 03 — Dataset paper standards

**Hard requirements for NeurIPS Evaluations & Datasets**, and good practice
anywhere. Mechanical rather than scientific work, which is exactly why it should
be done early instead of in the week before a deadline.

---

### Croissant — required, and not currently present

*Croissant: A Metadata Format for ML-Ready Datasets.*
**NeurIPS 2024, Datasets & Benchmarks Track** ·
[proceedings PDF](https://proceedings.neurips.cc/paper_files/paper/2024/file/9547b09b722f2948ff3ddb5d86002bc0-Paper-Datasets_and_Benchmarks_Track.pdf) ·
[MLCommons working group](https://mlcommons.org/working-groups/data/croissant/)

A JSON-LD metadata format for ML datasets, integrated by Hugging Face, Kaggle and
OpenML. **NeurIPS requires it in every dataset-track submission**, and the
FORUM-TB matrix does not have one.

**Use it for:** generating `ml_matrix.croissant.json`. Note the track specifically
requires the **Responsible AI extension fields**, not just the base format. The
dataset is already on Hugging Face, which supports Croissant natively — this may
be closer to a configuration task than an authoring one.

### Gebru et al. 2021 — Datasheets for Datasets

**Communications of the ACM 2021;64(12):86–92** ·
[doi:10.1145/3458723](https://doi.org/10.1145/3458723) ·
[arXiv:1803.09010](https://arxiv.org/abs/1803.09010)

The provenance-and-motivation questionnaire: why the dataset was created, how it
was collected, what it should and should not be used for. Croissant carries
structural metadata but explicitly *not* collection methodology or cohort
definition — a datasheet covers that.

**Use it for:** the questions this dataset answers badly today. Phenotype labels
were pooled from heterogeneous source studies with unrecorded DST methods and
critical concentrations; the Discussion already concedes this is a limitation.
A datasheet forces it to be documented per-source rather than waved at, and that
documentation is itself a contribution reviewers will credit.

### Mitchell et al. 2019 — Model Cards

**FAccT (FAT\*) 2019, pp. 220–229** ·
[doi:10.1145/3287560.3287596](https://doi.org/10.1145/3287560.3287596)

Per-model reporting: intended use, out-of-scope use, evaluation factors,
disaggregated performance, ethical considerations.

**Use it for:** the four released `.joblib` models. Disaggregated performance is
the relevant part — reporting per-lineage and per-drug performance rather than a
single pooled AUC connects directly to gap 1, and "not for clinical use" belongs
in a structured field rather than only in the paper's prose.

---

## What to do with this

1. Generate a Croissant file with Responsible AI fields for the feature matrix.
2. Mint a permanent DOI (Zenodo). A GitHub path is not an acceptable dataset
   citation for a dataset-track submission.
3. Write a datasheet, with the label-provenance limitation documented honestly
   per source study.
4. Write model cards for the four released models, with per-lineage
   disaggregation once gap 1 is done.
5. Prepare an anonymised release for double-blind review — the repository, the
   Hugging Face Space, and the author names in the dashboard's landing text all
   currently identify the authors.

Item 5 is easy to overlook and fatal at submission time. Plan it before the
deadline week.
