"""
FORUM-TB Dashboard
==================
Interpretable M. tuberculosis drug resistance prediction
from whole-genome sequencing (WGS) data.

Usage:
    streamlit run dashboard/app.py

Modes:
    Demo mode:  loads pre-computed results (no computation needed)
    Live mode:  uploads VCF and computes prediction + SHAP
                (requires x86 Linux — use HuggingFace Spaces)
"""

import gzip
import json
import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import joblib
import streamlit as st

warnings.filterwarnings("ignore")

# ── Config ─────────────────────────────────────────────────────────────────────
DRUGS       = ["RIFAMPICIN", "ISONIAZID", "ETHAMBUTOL", "PYRAZINAMIDE"]
HF_REPO     = "nanzhen102/FORUM-TB-models"
# Path relative to repo root, not dashboard/
DEMO_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "results", "predictions", "ERR040120_predictions.json"
)
MATRIX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "resistance_dataset", "ml_matrix.csv.gz"
)
DEMO_SAMPLE = "ERR040120"
NUC_ENCODE  = {"A": 1, "T": 2, "C": 3, "G": 4}
TOP_N_SHAP  = 20

AMR_GENES = {
    "rpoB":  (759807,  763325),
    "katG":  (2153889, 2156111),
    "inhA":  (1674202, 1675011),
    "fabG1": (1673440, 1674183),
    "embB":  (4246514, 4249810),
    "embA":  (4243233, 4246517),
    "embC":  (4239863, 4243147),
    "pncA":  (2288681, 2289241),
    "rpsA":  (1833542, 1834987),
}

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FORUM-TB",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Helper functions ───────────────────────────────────────────────────────────
def get_gene(pos_str):
    pos = int(str(pos_str).replace("pos_", ""))
    for gene, (start, end) in AMR_GENES.items():
        if start <= pos <= end:
            return gene
    return "unknown"


def parse_vcf(file_bytes):
    variants = {}
    try:
        content = gzip.decompress(file_bytes).decode("utf-8")
    except Exception:
        content = file_bytes.decode("utf-8")
    for line in content.splitlines():
        if line.startswith("#"):
            continue
        parts = line.strip().split("\t")
        if len(parts) < 5:
            continue
        _, pos, _, ref, alt = parts[0], int(parts[1]), parts[2], parts[3], parts[4]
        if len(ref) == 1 and len(alt) == 1:
            variants[pos] = alt.upper()
    return variants


def encode_sample(variants, feature_cols):
    vec = pd.Series(0, index=feature_cols, dtype=int)
    matched = 0
    for pos, alt in variants.items():
        col = f"pos_{pos}"
        if col in vec.index:
            vec[col] = NUC_ENCODE.get(alt, 0)
            matched += 1
    return vec, matched


def plot_shap_bar(shap_data, drug, top_n=TOP_N_SHAP):
    """shap_data: list of dicts with position, gene, shap_value"""
    top = sorted(shap_data, key=lambda x: abs(x["shap_value"]), reverse=True)[:top_n]
    top = sorted(top, key=lambda x: x["shap_value"])

    labels = [f"{d['position']}\n({d['gene']})" for d in top]
    values = [d["shap_value"] for d in top]
    colors = ["#e74c3c" if v > 0 else "#3498db" for v in values]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(range(len(values)), values, color=colors, alpha=0.85)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("SHAP value (impact on prediction)")
    ax.set_title(f"{drug} — Top {top_n} features", fontsize=11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(color="#e74c3c", label="→ Resistant"),
        Patch(color="#3498db", label="→ Susceptible"),
    ], fontsize=8, loc="lower right")
    plt.tight_layout()
    return fig


@st.cache_resource(show_spinner="Loading feature columns...")
def load_feature_cols():
    df = pd.read_csv(MATRIX_PATH, nrows=0, index_col="SAMPLE")
    return [c for c in df.columns if c.startswith("pos_")]


@st.cache_resource(show_spinner="Loading background data...")
def load_background(feature_cols):
    df = pd.read_csv(MATRIX_PATH, index_col="SAMPLE")
    return df[feature_cols].sample(100, random_state=42)


@st.cache_resource(show_spinner="Downloading model from HuggingFace...")
def load_model(drug):
    from huggingface_hub import hf_hub_download
    import shap
    path = hf_hub_download(repo_id=HF_REPO, filename=f"rf_{drug}_v2.joblib")
    return joblib.load(path)


def compute_prediction_and_shap(feature_vec, drug, background):
    import shap
    rf   = load_model(drug)
    X    = pd.DataFrame([feature_vec], columns=feature_vec.index)
    prob = rf.predict_proba(X)[0][1]
    pred = "Resistant" if prob >= 0.5 else "Susceptible"

    importances  = pd.Series(rf.feature_importances_, index=feature_vec.index)
    top_features = importances.nlargest(50).index.tolist()
    bg_top       = background[top_features]

    explainer = shap.TreeExplainer(
        rf, data=bg_top, feature_perturbation="interventional"
    )
    X_top     = pd.DataFrame([feature_vec[top_features].values], columns=top_features)
    shap_vals = explainer.shap_values(X_top, check_additivity=False)

    if isinstance(shap_vals, list):
        arr = shap_vals[1][0]
    else:
        arr = shap_vals[0, :, 1] if shap_vals.ndim == 3 else shap_vals[0]

    shap_series = pd.Series(arr, index=top_features)
    top_shap = [
        {
            "position":      feat,
            "gene":          get_gene(feat),
            "encoded_value": int(feature_vec.get(feat, 0)),
            "shap_value":    round(float(shap_series[feat]), 6)
        }
        for feat in shap_series.abs().nlargest(TOP_N_SHAP).index
    ]
    return pred, round(float(prob), 4), top_shap


# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🧬 FORUM-TB")
st.markdown(
    "**Interpretable *M. tuberculosis* drug resistance prediction "
    "from whole-genome sequencing data.**"
)
st.info(
    "⚠️ **Input requirement:** Filtered VCF files only "
    "(bcftools output, QUAL≥20, MQ≥30, aligned to H37Rv NC_000962.3). "
    "Raw FASTQ not supported. "
    "See the [pipeline](https://github.com/TheMicrobialist/SHAP-mTB-AMR) "
    "to generate a compatible VCF."
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Mode")
    demo_mode = st.checkbox(
        "🎯 Demo mode (pre-computed sample)",
        value=True,
        help=(
            "Load pre-computed results for ERR040120 (MDR-TB isolate). "
            "Turn off to upload your own VCF and compute live. "
            "Live mode requires x86 Linux — use HuggingFace Spaces."
        )
    )

    if demo_mode:
        st.success("Using pre-computed demo sample: ERR040120")
        vcf_file = None
    else:
        st.warning(
            "⚠️ Live mode may crash on Mac (ARM). "
            "Deploy to [HuggingFace Spaces](https://huggingface.co/spaces) "
            "for reliable live computation."
        )
        st.markdown("### Upload VCF")
        vcf_file = st.file_uploader(
            "Choose a VCF file",
            type=["vcf", "gz"],
            help="Filtered VCF from bcftools aligned to H37Rv"
        )

    st.markdown("### Select Drugs")
    selected_drugs = st.multiselect(
        "Predict resistance for:",
        options=DRUGS,
        default=DRUGS,
        format_func=lambda x: x.capitalize()
    )

    if demo_mode:
        run_button = st.button(
            "🔬 Show Demo Results",
            disabled=len(selected_drugs) == 0,
            use_container_width=True
        )
    else:
        run_button = st.button(
            "🔬 Predict Resistance",
            disabled=(vcf_file is None or len(selected_drugs) == 0),
            use_container_width=True
        )

    st.markdown("---")
    st.markdown(
        "**Project FORUM**\n\n"
        "[GitHub](https://github.com/TheMicrobialist/SHAP-mTB-AMR) · "
        "[Dataset](https://www.kaggle.com/datasets/nanzhen/forum-tb) · "
        "[Models](https://huggingface.co/nanzhen102/FORUM-TB-models) · "
        "[Blog](https://themicrobialist.substack.com)"
    )

# ── Landing page ───────────────────────────────────────────────────────────────
if not run_button:
    col1, col2, col3, col4 = st.columns(4)
    for col, (val, label) in zip(
        [col1, col2, col3, col4],
        [("9,798","Training isolates"),("2,693","AMR gene features"),
         ("0.975","Rifampicin AUC-ROC"),("4","First-line drugs")]
    ):
        with col:
            st.metric(label, val)

    st.markdown("---")
    st.markdown(
        "### How it works\n"
        "1. Select **Demo mode** to explore pre-computed results, "
        "or upload your own filtered VCF\n"
        "2. Select which drugs to predict\n"
        "3. Random Forest predicts resistance from 9 AMR gene positions\n"
        "4. SHAP explains which mutations drove the prediction\n\n"
        "**Biological validation:** Top SHAP features independently "
        "recovered S450L (rpoB) and S315T (katG) — the two most "
        "clinically prevalent resistance mutations globally."
    )
    st.stop()

# ── Load results ───────────────────────────────────────────────────────────────
if demo_mode:
    # Load pre-computed results
    if not os.path.exists(DEMO_JSON):
        st.error(
            f"Demo results not found: {DEMO_JSON}\n\n"
            "Run `python3 scripts/vcf_to_prediction.py "
            "--vcf test_data/ERR040120.filtered.vcf.gz --all-drugs` first."
        )
        st.stop()

    with open(DEMO_JSON) as f:
        all_results_raw = json.load(f)

    # Filter to selected drugs
    all_results = {k: v for k, v in all_results_raw.items() if k in selected_drugs}
    sample_name = DEMO_SAMPLE

    st.success(
        f"✅ **Demo sample: {sample_name}** — "
        "pre-computed MDR-TB isolate (resistant to all 4 drugs)"
    )

else:
    # Live computation
    sample_name = vcf_file.name.replace(".filtered.vcf.gz","").replace(".vcf.gz","").replace(".vcf","")

    with st.spinner("Loading data..."):
        feature_cols = load_feature_cols()
        background   = load_background(feature_cols)

    with st.spinner("Parsing VCF..."):
        file_bytes = vcf_file.read()
        variants   = parse_vcf(file_bytes)
        feature_vec, n_matched = encode_sample(variants, feature_cols)

    st.success(
        f"✅ **{sample_name}** — "
        f"{len(variants):,} SNPs parsed, "
        f"{n_matched} matched to AMR gene positions"
    )

    if n_matched == 0:
        st.error("No variants matched to AMR gene positions. Check VCF alignment to H37Rv.")
        st.stop()

    all_results = {}
    for drug in selected_drugs:
        with st.spinner(f"Computing {drug}..."):
            pred, prob, top_shap = compute_prediction_and_shap(
                feature_vec, drug, background
            )
        all_results[drug] = {
            "sample":                sample_name,
            "drug":                  drug,
            "prediction":            pred,
            "probability_resistant": prob,
            "top_shap_features":     top_shap
        }

# ── Display results ────────────────────────────────────────────────────────────
st.markdown(f"## Results — {sample_name}")
st.markdown("---")

# Summary table
st.markdown("### Resistance Profile")
summary = []
for drug, res in all_results.items():
    emoji = "🔴" if res["prediction"] == "Resistant" else "🟢"
    summary.append({
        "Drug":       drug.capitalize(),
        "Prediction": f"{emoji} {res['prediction']}",
        "Probability (resistant)": f"{res['probability_resistant']:.1%}",
    })
st.dataframe(pd.DataFrame(summary), hide_index=True, use_container_width=True)

# SHAP plots
st.markdown("### SHAP Explanations")
st.caption(
    "🔴 Red = pushes toward **Resistant** · "
    "🔵 Blue = pushes toward **Susceptible**"
)

cols = st.columns(min(len(all_results), 2))
for i, (drug, res) in enumerate(all_results.items()):
    fig = plot_shap_bar(res["top_shap_features"], drug)
    with cols[i % 2]:
        st.pyplot(fig)
        plt.close(fig)

# Mutation tables
st.markdown("### Top Mutations")
for drug, res in all_results.items():
    with st.expander(f"{drug} — top {TOP_N_SHAP} features"):
        rows = []
        for f in res["top_shap_features"]:
            nuc = {0:"REF",1:"A",2:"T",3:"C",4:"G"}.get(f.get("encoded_value",0),"?")
            rows.append({
                "Position":   f["position"],
                "Gene":       f["gene"],
                "Nucleotide": nuc,
                "SHAP value": round(f["shap_value"], 4),
                "Direction":  "→ Resistant" if f["shap_value"] > 0 else "→ Susceptible"
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# Download
st.markdown("---")
st.download_button(
    label="⬇️ Download results (JSON)",
    data=json.dumps(all_results, indent=2),
    file_name=f"{sample_name}_predictions.json",
    mime="application/json"
)

st.caption(
    "FORUM-TB v0.1.0 · Random Forest + SHAP · "
    "Research use only — not for clinical diagnosis · "
    "[GitHub](https://github.com/TheMicrobialist/SHAP-mTB-AMR)"
)