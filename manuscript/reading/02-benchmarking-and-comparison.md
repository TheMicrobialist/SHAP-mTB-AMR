# 02 — Benchmarking, comparison and external validation

**Gaps 2–4.** The Discussion currently says cross-study numbers are
incomparable, which is true and also means we have never measured where this
pipeline stands. These are the comparators to run against and the datasets to
run on.

All four papers below are already in `references.bib` — they are cited as prior
work but have not been *used* as comparators. That is the gap.

---

## Comparators to run head-to-head

### Phelan et al. 2019 — TB-Profiler

**Genome Medicine 2019;11(1):41** · [doi:10.1186/s13073-019-0650-x](https://doi.org/10.1186/s13073-019-0650-x) · PMID 31234910

The de facto standard tool, 13 drugs, widely deployed. Runs from FASTQ or BAM,
so it can be pointed at the same isolates. Also the natural source of lineage
calls (see `01`), which makes it two tools in one.

### Gröschel et al. 2021 — GenTB

**Genome Medicine 2021;13(1):138** · [doi:10.1186/s13073-021-00953-4](https://doi.org/10.1186/s13073-021-00953-4) · PMID 34461978

The closest comparator by design: it ships a **random forest** and a wide-and-deep
neural net, so it isolates the effect of feature representation rather than model
family. Its benchmark against 20,408 isolates is also the template to imitate —
mean sensitivity and specificity per drug across a shared ground-truth set.

### Yang et al. 2019 — DeepAMR

**Bioinformatics 2019;35(18):3240–3249** · [doi:10.1093/bioinformatics/btz067](https://doi.org/10.1093/bioinformatics/btz067) · PMID 30689732

Multi-task denoising autoencoder for *co-occurrent* resistance — the same problem
the `MultiOutputClassifier` extension addresses, and it reports AUCs above ours.
This is the paper the multi-label section must engage with directly rather than
cite in passing.

### Ngo & Teo 2019 — benchmarking methodology

**BMC Bioinformatics 2019;20(1):68** · [doi:10.1186/s12859-019-2658-z](https://doi.org/10.1186/s12859-019-2658-z) · PMID 30736750

Benchmarks databases *and* algorithms, and shows reported performance is
strongly sensitive to which database and isolate set is used. Read this before
designing the comparison — it is the evidence for why a shared test set is
required, and a guide to the failure modes of doing it badly.

---

## External validation set

### CRyPTIC Consortium 2022 — the compendium

**PLOS Biology 2022;20(8):e3001721** · [doi:10.1371/journal.pbio.3001721](https://doi.org/10.1371/journal.pbio.3001721) · PMID 35944069

12,289 isolates with **quantitative MICs** for 13 drugs. Already cited, not yet
used.

Two distinct reasons this matters:

1. **Independence.** An external cohort not drawn from the ENA/SRA isolates used
   for training — gap 3.
2. **Label quality.** Quantitative MICs let the pyrazinamide question be
   decomposed. The Discussion argues weak PZA performance confounds harder
   genetics, an unsuitable representation, and noisy binary labels; MIC data
   separates the third from the first two. That decomposition would be a
   genuinely novel contribution, and it is achievable with existing public data.

---

## Statistical rigour (gap 4)

No reading required — this is a methodology fix, listed here so it is not
forgotten. Random Forest currently "wins" on margins as small as 0.0015 CV
AUC-ROC from a single split with no confidence intervals. Repeated splits or
nested CV, CIs on every reported metric, and either a test for the ranking or
withdrawal of the ranking claim. Cheap, and the single highest ratio of
reviewer-confidence gained to effort spent in this whole list.

---

## What to do with this

1. Define one held-out evaluation set — ideally CRyPTIC isolates absent from the
   training data.
2. Run TB-Profiler, GenTB (both models) and, if feasible, DeepAMR on it.
3. Report side by side per drug, with confidence intervals, including where
   FORUM-TB loses.
4. Use the MIC data to test whether PZA label noise explains the PZA gap.

Step 3 is not a risk to manage but the point of the exercise. A resource paper
that honestly reports being mid-field, with the comparison actually run, is far
stronger than one that avoids the question.
