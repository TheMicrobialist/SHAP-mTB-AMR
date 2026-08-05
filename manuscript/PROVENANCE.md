# Provenance — where every number in the manuscript comes from

Internal working note. **Not part of the manuscript** and not compiled into the
PDF. This exists so any figure in the paper can be traced back to the file it
came from without cluttering the preprint with repository paths.

Paths are relative to the repository root.

## Tables

| Table | Content | Source file |
|---|---|---|
| 1 | Dataset summary — per-drug labelled isolates, class balance | `resistance_dataset/ml_matrix.csv.gz` (label columns); phenotype counts from `resistance_dataset/master_table_resistance.csv` |
| 2 | Per-drug Random Forest performance, and the per-class precision/recall/F1 in the footnote | `results/metrics_{DRUG}_v2.txt` (one file per drug) |
| 3 | Seven-model CV AUC-ROC comparison | `results/results/benchmark_results.md` |
| 4 | Cross-drug SHAP attribution (RIF–INH pair) | `results/shap_cross_drug_RIF_INH.csv` — full pair has 41 shared-position rows; the five with the largest `max_abs_delta` are shown |
| 5 | Multi-label benchmark (Hamming loss, subset accuracy, macro AUC) | `results/benchmark_multi_v1.csv` |
| 6 | Case study, isolate ERR040120 | `results/predictions/ERR040120_predictions.json` |
| 7 | Pipeline tool versions and parameters | `README.md` processing-pipeline table; `environment.yml` |

Rendered table numbers follow the order of appearance in the compiled PDF, which
is not the same as the numeric suffix of the `tables/tableN_*.tex` filenames.

## Figures

| Figure | Content | Source |
|---|---|---|
| 1 | Framework overview schematic | `figures/fig1_pipeline.tex` (TikZ, authored for the manuscript) |
| 2 | SHAP summary (beeswarm) plots, 4 panels | `results/shap_summary_{DRUG}_v2.png`, copied to `figures/fig2{a-d}_shap_*.png` |
| 3 | Model comparison bar charts, RIF and INH | `results/results/benchmark_{DRUG}_v3.png`, copied to `figures/fig3{a,b}_benchmark_*.png` |

## In-text figures

| Claim | Source |
|---|---|
| 9,798 isolates; 2,693 features | `resistance_dataset/ml_matrix.csv.gz` (shape 9798 × 2698, i.e. SAMPLE + 2,693 positions + 4 drug labels) |
| 705,226 unique variant positions | `scripts/vcf_to_csv.py` output, reported in `README.md` |
| 3 outliers removed (ERR1034652, ERR1035353, ERR1213920) | `scripts/qc_variants.py` |
| 5,180 isolates with all four labels | `results/benchmark_multi_v1.csv` run configuration |
| Tool versions (fastp 1.0.1, BWA-MEM 0.7.18, bcftools 1.22) | `README.md` processing-pipeline table |

## Re-checking

The agent tooling in `scripts/shap_agent.py` reads several of these files
directly, so `python3 scripts/test_shap_agent_tools.py` independently confirms
the Table 4 and Table 6 values still match their sources.
