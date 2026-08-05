# Reading list: work needed to reach a target venue

Papers and standards grouped by which gap each closes. Gaps and priority come
from `../submission/readiness-checklist.md`. All metadata verified 2026-08-05
against PubMed / Crossref / arXiv.

Each entry uses the same four fields:

- **Gives**: what the paper provides
- **Use for**: how it applies here
- **Needs**: prerequisites before it can be used
- **Effort**: low / medium / high

| # | File | Gap | Priority |
|---|---|---|---|
| 01 | `01-lineage-and-population-structure.md` | Lineage confounding | **Blocking** |
| 02 | `02-benchmarking-and-comparison.md` | Comparison, external validation, stats | High |
| 03 | `03-dataset-paper-standards.md` | NeurIPS hard requirements | High, mechanical |
| 04 | `04-interpretability-methods.md` | SHAP dependence + faithfulness | Medium |
| 05 | `05-representation-and-transfer.md` | Beyond position-encoded SNPs | **Deprioritised, see 06** |
| 06 | `06-on-device-llm-decision.md` | On-device LLM question + **BIG-TB** | **Read first** |

## Order

1. **01**: decides whether the cross-drug result is real. It is the only
   novelty claimed.
2. **02**: converts "we don't claim competitive accuracy" into a measurement.
3. **03**: cheap, mechanical, hard gate for NeurIPS. Do early, not at deadline.
4. **04**: the headline contribution currently has no faithfulness evidence.
5. **05**: highest ceiling, highest cost.

## Read 06 first

It answers the on-device LLM question (no), but more importantly it flags
**BIG-TB**: a 17,000-genome TB benchmark with a prediction *and* attribution
task, released 2026-02-02. It overlaps this project's niche, independently
reports our central finding, answers gap 5 negatively, and supplies the shared
benchmark gaps 2 and 3 ask for. It changes the priorities below.

## Caution

Reading will not fix this paper. The gaps are experimental. Lineage
stratification must be **run**, comparators must be **executed** on a shared
test set. Four of the key papers below are already cited in `../references.bib`;
they were never used.
