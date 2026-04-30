# Methodology

## Parsing

The parser converts raw WhatsApp export text into a structured DataFrame with:

- timestamp
- sender
- message body
- date-derived features such as day, month, hour, and time period

It supports multi-line messages and system notifications.

## Sentiment Analysis

The project uses Hugging Face transformer models for text classification. Messages are filtered to exclude:

- group notifications
- deleted messages
- media placeholders

Evaluation is performed on a manually curated Hinglish/English validation set using:

- accuracy
- macro precision
- macro recall
- macro F1

## Conversation Network

The relationship graph is not simple turn-taking. Edge weights combine:

- fast reply-gap strength
- explicit name mentions
- proximity inside the same conversation session

Conversation sessions are segmented using configurable inactivity gaps.

## Exports

All major outputs can be exported as CSV and Parquet to support:

- exploratory analysis
- dashboards
- downstream machine learning
- reproducible portfolio artifacts
