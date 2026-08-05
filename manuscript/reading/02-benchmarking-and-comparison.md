# 02. Benchmarking, comparison, external validation

**Gaps 2–4.** The Discussion says cross-study numbers are incomparable. That is true,
and it also means we have never measured where this pipeline stands.

All four comparators below are **already cited in `../references.bib`** as prior
work. None has been run.

---

## Comparators to run head-to-head

### Phelan et al. 2019: TB-Profiler
Genome Medicine 11(1):41 · [doi:10.1186/s13073-019-0650-x](https://doi.org/10.1186/s13073-019-0650-x) · PMID 31234910

- **Gives**: de facto standard tool, 13 drugs, runs from FASTQ/BAM
- **Use for**: head-to-head comparison; also supplies the lineage calls needed in `01`
- **Needs**: a defined held-out isolate set
- **Effort**: low (installable tool)

### Gröschel et al. 2021: GenTB
Genome Medicine 13(1):138 · [doi:10.1186/s13073-021-00953-4](https://doi.org/10.1186/s13073-021-00953-4) · PMID 34461978

- **Gives**: random forest **and** wide-and-deep net; a 20,408-isolate benchmark protocol
- **Use for**: isolating representation effects from model-family effects, since it shares our model class; its benchmark is the template to imitate
- **Needs**: same held-out set
- **Effort**: low–medium

### Yang et al. 2019: DeepAMR
Bioinformatics 35(18):3240–3249 · [doi:10.1093/bioinformatics/btz067](https://doi.org/10.1093/bioinformatics/btz067) · PMID 30689732

- **Gives**: multi-task autoencoder for co-occurrent resistance; AUC 0.944–0.987, above ours
- **Use for**: the multi-label section must engage this directly, not cite it in passing
- **Needs**: same held-out set; may need reimplementation
- **Effort**: medium–high

### Ngo & Teo 2019: benchmarking methodology
BMC Bioinformatics 20(1):68 · [doi:10.1186/s12859-019-2658-z](https://doi.org/10.1186/s12859-019-2658-z) · PMID 30736750

- **Gives**: evidence that reported performance swings with database and isolate-set choice
- **Use for**: designing the comparison; read **before** running anything
- **Needs**: nothing
- **Effort**: low

---

## External validation set

### CRyPTIC Consortium 2022: the compendium · *already cited, never used*
PLOS Biology 20(8):e3001721 · [doi:10.1371/journal.pbio.3001721](https://doi.org/10.1371/journal.pbio.3001721) · PMID 35944069

- **Gives**: 12,289 isolates, **quantitative MICs**, 13 drugs
- **Use for**: (a) an external cohort independent of our ENA/SRA training data; (b) decomposing the pyrazinamide problem: MICs separate label noise from the genetics and representation explanations
- **Needs**: download + harmonise to our feature encoding; check isolate overlap with training set
- **Effort**: medium

---

## Statistical rigour: no reading needed

Random Forest currently "wins" on margins as small as 0.0015 CV AUC-ROC, single
split, no confidence intervals.

- **Required**: repeated splits or nested CV; CIs on every metric; a test for the ranking, or drop the ranking claim
- **Effort**: low
- **Payoff**: highest reviewer-confidence-per-hour in this entire list

---

## Do this

1. Define one held-out set, ideally CRyPTIC isolates absent from training.
2. Run TB-Profiler, GenTB (both models), DeepAMR if feasible.
3. Report side by side, per drug, with CIs, **including where FORUM-TB loses**.
4. Use MICs to test whether PZA label noise explains the PZA gap.

Step 3 losing is not a risk to manage. It is the result. A resource paper that
honestly reports mid-field standing, comparison actually run, beats one that
avoids the question.
