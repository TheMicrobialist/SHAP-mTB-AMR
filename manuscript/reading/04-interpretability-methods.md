# 04 — Interpretability: dependence and faithfulness

**Gap 6.** SHAP is the headline contribution and rests on an independence
assumption this data violates — linkage disequilibrium, clonal population
structure, and the co-resistance correlation the paper itself reports.

---

## The problem

### Aas et al. 2021 — Shapley values with dependent features · *already cited*
Artificial Intelligence 298:103502 · [doi:10.1016/j.artint.2021.103502](https://doi.org/10.1016/j.artint.2021.103502)

- **Gives** — proof that marginal/interventional estimators evaluate the model off the data manifold under dependence; conditional approximations that don't; the `shapr` implementation
- **Use for** — re-deriving attributions. Our `TreeExplainer` call uses a 100-sample **interventional** background — exactly the flagged setting
- **Needs** — the existing models and feature matrix only
- **Effort** — medium
- **The result is the contribution** — do interventional and conditional attributions actually differ here, and does the cross-drug result survive the switch? Publishable either way

### Kumar et al. 2020 — the conceptual limit · *already cited*
ICML 2020 · [arXiv:2002.11097](https://arxiv.org/abs/2002.11097)

- **Gives** — Shapley values are a mathematical allocation, not a causal or human-facing explanation
- **Use for** — bounding claims, including how the agent phrases output. "The model relied on X" is defensible; "X causes resistance" is not
- **Needs** — nothing
- **Effort** — low

---

## Proving attributions are faithful — *not yet cited*

The paper validates SHAP by noting it recovers *rpoB* S450L and *katG* S315T.
The Discussion already concedes this is weak: any competent model finds the most
prevalent mutations globally. These give a real test.

### Adebayo et al. 2018 — Sanity Checks for Saliency Maps
NeurIPS 2018 · [proceedings](https://papers.neurips.cc/paper/8160-sanity-checks-for-saliency-maps) · [arXiv:1810.03292](https://arxiv.org/abs/1810.03292)

- **Gives** — randomization tests exposing attribution methods that are independent of model parameters and labels, i.e. plausible-looking but empty
- **Use for** — retrain on shuffled labels, confirm attributions change
- **Needs** — a retraining loop; models retrain in minutes here
- **Effort** — low
- **Stakes** — if S450L still tops the list under a randomised model, the "recovers known biology" claim collapses. Worth knowing

### Hooker et al. 2019 — ROAR
NeurIPS 2019 · [arXiv:1806.10758](https://arxiv.org/abs/1806.10758)

- **Gives** — RemOve-And-Retrain: delete top-*t*% features by attribution, retrain, measure the drop. Steep drop = faithful
- **Use for** — the quantitative faithfulness number the paper currently lacks entirely; also tests whether diffuse PZA attributions carry any signal
- **Needs** — repeated retraining; cheap at 2,693 features, unlike the vision settings ROAR was built for
- **Effort** — low–medium

---

## Do this

1. Re-derive attributions with conditional estimation; compare to interventional.
2. Quantify the effect of the top-50 impurity pre-selection (currently unmeasured bias).
3. Model-randomization sanity check (Adebayo).
4. ROAR per drug for a faithfulness number.
5. Re-examine cross-drug under (1), **jointly with `01`** — dependence and population structure are one problem seen from two angles.

Items 3–4 most change how a reviewer reads the paper: they turn "we applied
SHAP" into "we tested whether SHAP told us anything."
