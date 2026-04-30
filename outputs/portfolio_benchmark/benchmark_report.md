# Sentiment Benchmark Report

- Dataset rows: 45
- Labels: Negative, Neutral, Positive
- Models benchmarked: 3
- Selected model: `tabularisai/multilingual-sentiment-analysis`
- Selection rule: highest macro F1, then highest accuracy

## Summary Metrics

| model_name | accuracy | macro_precision | macro_recall | macro_f1 |
| --- | --- | --- | --- | --- |
| tabularisai/multilingual-sentiment-analysis | 0.6889 | 0.68 | 0.6889 | 0.6762 |
| lxyuan/distilbert-base-multilingual-cased-sentiments-student | 0.6 | 0.5917 | 0.6 | 0.5619 |
| rohanrajpal/bert-base-multilingual-codemixed-cased-sentiment | 0.4 | 0.3759 | 0.4 | 0.3743 |

## Why This Model Was Chosen

`tabularisai/multilingual-sentiment-analysis` achieved the strongest macro F1 on the mixed Hinglish/English validation set, which is the most balanced metric for three-class sentiment tasks. It was therefore kept as the recommended default for portfolio and analysis workflows.

## Reproducibility

- Dataset path: `C:\Users\ishan\OneDrive\Desktop\whatsapp_chat_analyser\data\sample\sentiment_validation.csv`
- Config path: `C:\Users\ishan\OneDrive\Desktop\whatsapp_chat_analyser\config\defaults.json`
- Generated artifacts directory: `outputs\portfolio_benchmark`