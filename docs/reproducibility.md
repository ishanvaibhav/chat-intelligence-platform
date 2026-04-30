# Reproducibility Notes

## Environment

- Python `3.13`
- Core dependencies are pinned in `requirements.txt`
- Notebook and test tooling live in `requirements-dev.txt`

## Data

- Sample chat file: `data/sample/whatsapp_chat_sample.txt`
- Sentiment benchmark set: `data/sample/sentiment_validation.csv`
- The sentiment benchmark is a manually curated Hinglish/English validation set intended for portfolio benchmarking and reproducible comparisons.

## Config

- Default runtime parameters are stored in `config/defaults.json`
- Sentiment and graph settings can be overridden through the Streamlit sidebar or CLI config path

## Repeatable Commands

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
pytest -q
python scripts\run_pipeline.py --chat-file data\sample\whatsapp_chat_sample.txt --output-dir outputs\portfolio_pipeline
python scripts\evaluate_models.py --dataset data\sample\sentiment_validation.csv --output-dir outputs\portfolio_benchmark
python scripts\generate_portfolio_assets.py
```

## Outputs

- Export tables: `outputs/portfolio_pipeline`
- Benchmark metrics and report: `outputs/portfolio_benchmark`
- README-ready images: `assets/figures`
