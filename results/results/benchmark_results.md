## Benchmark Results — Multi-Model AMR Classification
> Models: Random Forest, LightGBM, XGBoost, Linear SVM (SGD), LR L1 (Lasso), LR ElasticNet, LR L2 (Ridge) | 5-fold stratified CV | 80/20 train/test split
> \* = best CV AUC-ROC per drug. ± values are std dev across 5 folds.

### RIFAMPICIN
| Model | Test Acc | Test AUC-ROC | CV Acc | CV AUC-ROC |
|---|---|---|---|---|
| Random Forest * | 0.9496 | 0.9753 | 0.9364 ± 0.0041 | 0.9690 ± 0.0037 |
| LightGBM | 0.9502 | 0.9730 | 0.9363 ± 0.0030 | 0.9675 ± 0.0023 |
| XGBoost | 0.9408 | 0.9695 | 0.9330 ± 0.0038 | 0.9643 ± 0.0019 |
| Linear SVM (SGD) | 0.8951 | 0.9022 | 0.8899 ± 0.0314 | 0.9155 ± 0.0130 |
| LR L1 (Lasso) | 0.9341 | 0.9667 | 0.9280 ± 0.0050 | 0.9607 ± 0.0031 |
| LR ElasticNet | 0.9320 | 0.9651 | 0.9267 ± 0.0043 | 0.9602 ± 0.0034 |
| LR L2 (Ridge) | 0.9252 | 0.9587 | 0.9198 ± 0.0049 | 0.9568 ± 0.0044 |

### ISONIAZID
| Model | Test Acc | Test AUC-ROC | CV Acc | CV AUC-ROC |
|---|---|---|---|---|
| Random Forest * | 0.9045 | 0.9475 | 0.9055 ± 0.0038 | 0.9464 ± 0.0077 |
| LightGBM | 0.8904 | 0.9396 | 0.8942 ± 0.0046 | 0.9391 ± 0.0047 |
| XGBoost | 0.8789 | 0.9370 | 0.8783 ± 0.0017 | 0.9364 ± 0.0060 |
| Linear SVM (SGD) | 0.8841 | 0.8734 | 0.8753 ± 0.0132 | 0.8782 ± 0.0186 |
| LR L1 (Lasso) | 0.8951 | 0.9427 | 0.8920 ± 0.0043 | 0.9433 ± 0.0068 |
| LR ElasticNet | 0.8977 | 0.9419 | 0.8907 ± 0.0054 | 0.9428 ± 0.0062 |
| LR L2 (Ridge) | 0.8951 | 0.9379 | 0.8909 ± 0.0067 | 0.9382 ± 0.0060 |

### PYRAZINAMIDE
| Model | Test Acc | Test AUC-ROC | CV Acc | CV AUC-ROC |
|---|---|---|---|---|
| Random Forest * | 0.8191 | 0.8862 | 0.8099 ± 0.0130 | 0.8831 ± 0.0074 |
| LightGBM | 0.8000 | 0.8744 | 0.7937 ± 0.0123 | 0.8699 ± 0.0095 |
| XGBoost | 0.7791 | 0.8588 | 0.7765 ± 0.0087 | 0.8595 ± 0.0097 |
| Linear SVM (SGD) | 0.7817 | 0.7825 | 0.7657 ± 0.0202 | 0.7912 ± 0.0177 |
| LR L1 (Lasso) | 0.8000 | 0.8660 | 0.8007 ± 0.0098 | 0.8660 ± 0.0085 |
| LR ElasticNet | 0.8052 | 0.8613 | 0.8012 ± 0.0108 | 0.8614 ± 0.0090 |
| LR L2 (Ridge) | 0.7974 | 0.8536 | 0.7939 ± 0.0120 | 0.8488 ± 0.0114 |

### ETHAMBUTOL
| Model | Test Acc | Test AUC-ROC | CV Acc | CV AUC-ROC |
|---|---|---|---|---|
| Random Forest * | 0.8116 | 0.8936 | 0.8202 ± 0.0056 | 0.8997 ± 0.0066 |
| LightGBM | 0.8140 | 0.8858 | 0.8184 ± 0.0091 | 0.8938 ± 0.0096 |
| XGBoost | 0.8104 | 0.8798 | 0.8106 ± 0.0081 | 0.8840 ± 0.0083 |
| Linear SVM (SGD) | 0.7274 | 0.7359 | 0.7433 ± 0.0143 | 0.7796 ± 0.0154 |
| LR L1 (Lasso) | 0.8030 | 0.8688 | 0.7984 ± 0.0076 | 0.8696 ± 0.0099 |
| LR ElasticNet | 0.7921 | 0.8640 | 0.7942 ± 0.0074 | 0.8651 ± 0.0096 |
| LR L2 (Ridge) | 0.7902 | 0.8534 | 0.7925 ± 0.0054 | 0.8569 ± 0.0079 |

---
> \* = best CV AUC-ROC per drug. ± values are std dev across 5 folds.
