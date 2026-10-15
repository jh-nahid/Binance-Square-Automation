# Binance Square Automation

A compact Python automation that gathers live Binance market data, optionally reads recent Binance announcements, generates a Binance Square post with Gemini, and publishes it only when `POST_MODE=live` and the required secret keys are present.

This project is intentionally safe by default:
- the scheduler runs in `dry` mode unless you explicitly switch to `live`
- it avoids publishing irrelevant or noisy information
- it keeps content structured around the selected content pillar
- it enforces a strict two-hashtag ending and only allows up to two cashtags

## Features

- 24h market snapshot from Binance
- optional Binance announcement fetch
- dynamic content pillar selection
- Gemini-powered post generation
- deterministic fallback text generation if Gemini is unavailable
- safe GitHub Actions scheduling
- environment-driven configuration

## Required environment variables

Create a `.env` file or set the same variables in GitHub Actions secrets.

```bash
BINANCE_SQUARE_API_KEY=your_binance_square_key
GEMINI_API_KEY=your_google_gemini_key
POST_MODE=dry
SHARE_EVENTS=false
USE_TRENDING_HASHTAGS=false
```

### Variable meanings

- `BINANCE_SQUARE_API_KEY`: Binance Square OpenAPI key
- `GEMINI_API_KEY`: Google Gemini API key
- `POST_MODE`: `dry` or `live`
- `SHARE_EVENTS`: `true` to include official Binance event text; `false` keeps it private by default
- `USE_TRENDING_HASHTAGS`: `true` to replace the default pillar hashtags with a trending pair; `false` keeps the designed pillar hashtags

## Local setup

1. Clone the repository
2. Create a virtual environment
3. Install dependencies
4. Copy `.env.example` to `.env` and fill your keys
5. Run the script

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

## Safe defaults

The script is intentionally configured to be conservative:

- `POST_MODE=dry` means it prints the post to the console instead of submitting it
- `SHARE_EVENTS=false` prevents the script from exposing sensitive event wording in public content
- fallback generation means the job still completes even if Gemini is unavailable

This reduces failed cron runs and avoids publishing broken content.

## GitHub Actions

The workflow runs on a schedule and supports manual publishing. By default it stays in `dry` mode to prevent accidental public posts.

To publish live:

1. open the workflow in GitHub Actions
2. click Run workflow
3. choose `live` in the input
4. make sure both required secrets exist

## File overview

```text
.
├── .env.example          Environment template
├── .github/
│   └── workflows/
│       └── binance_poster.yml
├── README.md            Project guide
├── bot.py               Main automation script
├── requirements.txt      Python dependencies
└── .gitignore           Local env and cache exclusions
```

## Notes

- This repo is intentionally lightweight and script-based; it is not a full web app.
- It is best used as a cron-driven content generator for Binance Square.
- Always validate the generated post locally in `dry` mode before switching to `live`.
