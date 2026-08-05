# FORUM-TB Trained Models

Trained Random Forest models for TB drug resistance prediction.

## Download

Models are hosted on HuggingFace Hub (244MB total):
https://huggingface.co/nanzhen102/FORUM-TB-models

## Download via Python

```python
from huggingface_hub import hf_hub_download
import joblib

for drug in ["RIFAMPICIN", "ISONIAZID", "ETHAMBUTOL", "PYRAZINAMIDE"]:
    path = hf_hub_download(
        repo_id="nanzhen102/FORUM-TB-models",
        filename=f"rf_{drug}_v2.joblib"
    )
    print(f"Downloaded: {path}")
```

## Models
| File | Drug | AUC-ROC | Size |
|---|---|---|---|
| rf_RIFAMPICIN_v2.joblib | Rifampicin | 0.975 | 61MB |
| rf_ISONIAZID_v2.joblib | Isoniazid | 0.948 | 48MB |
| rf_ETHAMBUTOL_v2.joblib | Ethambutol | 0.894 | 77MB |
| rf_PYRAZINAMIDE_v2.joblib | Pyrazinamide | 0.886 | 58MB |
