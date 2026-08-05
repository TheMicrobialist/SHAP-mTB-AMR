# 04 — Interpretability: dependence and faithfulness

**Gap 6.** SHAP is the paper's headline contribution and currently rests on an
independence assumption this data violates — linkage disequilibrium, clonal
population structure, and the co-resistance correlation the paper itself reports.
The Discussion concedes this. Fixing or bounding it is what turns a conceded
weakness into a methodological contribution.

Two of the three below are already cited but not acted on.

---

## The problem (already cited)

### Aas et al. 2021 — Shapley values with dependent features

**Artificial Intelligence 2021;298:103502** ·
[doi:10.1016/j.artint.2021.103502](https://doi.org/10.1016/j.artint.2021.103502)

Shows that standard (marginal/interventional) Shapley estimators evaluate the
model off the data manifold when features are dependent, and gives conditional
approximations that do not.

**Use it for:** re-deriving the attributions. This is the direct fix. Our
`TreeExplainer` call uses a 100-sample **interventional** background, which is
precisely the setting the paper identifies as problematic. Their `shapr`
implementation gives conditional alternatives to compare against.

The comparison itself is the contribution: *do the interventional and conditional
attributions actually differ on this data, and does the cross-drug result
survive the switch?* That is a concrete experiment with a publishable answer
either way, and no new sequencing.

### Kumar et al. 2020 — the conceptual limit

*Problems with Shapley-value-based explanations as feature importance measures.*
**ICML 2020** · [arXiv:2002.11097](https://arxiv.org/abs/2002.11097)

Shapley values are a mathematical allocation, not a causal or human-facing
explanation; recovering them for causal purposes needs assumptions the method
does not supply.

**Use it for:** bounding the claims. Already cited in the Discussion — keep it
there, and let it constrain how the agent's natural-language output is framed.
An interpretation layer that says "the model relied on X" is defensible; one
that implies "X causes resistance" is not.

---

## Proving the attributions are faithful (not yet cited)

The paper validates SHAP by observing that it recovers *rpoB* S450L and *katG*
S315T — and the Discussion already concedes this is weak, since any competent
model would find the most prevalent mutations globally. These give a real test.

### Adebayo et al. 2018 — Sanity Checks for Saliency Maps

**NeurIPS 2018** ·
[proceedings](https://papers.neurips.cc/paper/8160-sanity-checks-for-saliency-maps) ·
[arXiv:1810.03292](https://arxiv.org/abs/1810.03292)

Randomization tests showing several widely used attribution methods produce
explanations independent of both model parameters and training labels — i.e.
they look plausible while explaining nothing.

**Use it for:** a model-randomization check. Retrain on shuffled labels and
confirm the attributions change. If S450L still tops the list under a randomised
model, the "recovers known biology" claim collapses — and knowing that is worth
more than the claim.

### Hooker et al. 2019 — ROAR

*A Benchmark for Interpretability Methods in Deep Neural Networks.*
**NeurIPS 2019** · [arXiv:1806.10758](https://arxiv.org/abs/1806.10758)

RemOve-And-Retrain: delete the top-*t*% of features by attribution, retrain, and
measure the performance drop. A faithful attribution causes a steep drop; an
unfaithful one does not.

**Use it for:** a quantitative faithfulness measure, which the paper currently
lacks entirely. It is cheap here — the models retrain in minutes on 2,693
features, unlike the vision settings ROAR was designed for. Running it across
all four drugs would give the interpretability claim actual evidence, and would
also test whether the diffuse pyrazinamide attributions carry any signal at all.

---

## What to do with this

1. Re-derive attributions with conditional (dependence-aware) estimation and
   compare against the current interventional ones.
2. Quantify the effect of the top-50 impurity pre-selection, which currently
   biases attributions in an unmeasured way.
3. Run a model-randomization sanity check per Adebayo et al.
4. Run ROAR per drug for a faithfulness number.
5. Re-examine the cross-drug result under (1) — jointly with the lineage
   stratification in `01`, since dependence and population structure are the
   same underlying problem seen from two angles.

Items 3 and 4 are the ones that would most change how a reviewer reads the
paper: they convert "we applied SHAP" into "we applied SHAP and tested whether
it was telling us anything."
