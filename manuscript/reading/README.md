# Reading list — work needed to reach a target venue

Papers and standards this project should draw on, organised by the gap each one
closes. Gaps and their priority come from `../submission/readiness-checklist.md`;
this file says *what to read and use* for each.

Every entry below was verified 2026-08-05 against PubMed, Crossref or arXiv.
Nothing here is already cited in the manuscript — for what is, see
`../references.bib` (24 entries, all verified).

| File | Covers |
|---|---|
| `README.md` | This index and the priority order |
| `01-lineage-and-population-structure.md` | Gap 1 — the blocking one |
| `02-benchmarking-and-comparison.md` | Gaps 2–4 — comparison, external validation, statistics |
| `03-dataset-paper-standards.md` | NeurIPS E&D hard requirements |
| `04-interpretability-methods.md` | Gap 6 — SHAP under dependence, and proving attributions are faithful |
| `05-representation-and-transfer.md` | Gap 5 — beyond position-encoded SNPs |

## Priority

Read in this order. The first two decide whether the paper has a defensible
novel claim at all; the rest raise the ceiling.

1. **`01`** — lineage. Without it the cross-drug result is uninterpretable, and
   that result is the only novelty the paper claims.
2. **`02`** — benchmarking. Converts "we don't claim competitive accuracy" into
   a measured statement, whichever way it falls.
3. **`03`** — dataset standards. Cheap, mechanical, and a hard gate for NeurIPS
   Evaluations & Datasets. Do it early so it is not a deadline scramble.
4. **`04`** — interpretability. The headline contribution currently rests on an
   assumption the data violates; this is how to fix or bound it.
5. **`05`** — representation. Highest ceiling, highest cost. A next-paper
   direction more than a revision item.

## One caution

Reading more will not fix this paper. The gaps are experimental, not
bibliographic — lineage stratification has to be *run*, comparators have to be
*executed* on a shared test set. Use this list to do those things correctly,
not as a substitute for doing them.
