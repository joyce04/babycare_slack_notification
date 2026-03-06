# 🌅 Daily Child Development Slack Message System

A multi-agent AI system that sends daily child development recommendations translated to Korean via Slack — exercises, toy suggestions, books, health tips, development tips, and safety tips — all backed by scientific research and official medical guidelines.

매일 **한국어**로 아이 발달 추천을 Slack으로 보내주는 멀티 에이전트 AI 시스템입니다 — 운동, 장난감 추천, 도서 추천, 건강 팁, 발달 팁, 안전 팁을 과학적 연구와 공식 의료 가이드라인에 기반하여 제공합니다.

Built with [LangGraph](https://github.com/langchain-ai/langgraph) + [OpenRouter](https://openrouter.ai/) for intelligent recommendation generation, validation, deduplication, and translation.

---

## ✨ Features

- 🤖 **5 LLM Agents** — Researcher, Validator, Deduplicator, Translator, Formatter
- 👶 **Birthdate-based age** — set once, age auto-updates (`"5 months"`, `"2 years 3 months"`)
- 📊 **Month-level milestones** — 10 developmental tiers from newborn to 12 years
- 🎲 **6 categories** — exercise, toy, book, health tip, development tip, and safety tip
- 📚 **Verified references** — every recommendation cites published research (DOI links) or official guidelines (CDC, AAP, WHO, etc.)
- 🔍 **LLM deduplication** — semantic similarity check prevents repetitive recommendations
- 🇰🇷 **Korean Slack messages** — translated by AI, preserving links and citations
- 📝 **CSV tracking** — full history with sent status, reasoning, and references
- ⚙️ **GitHub Actions** — automated weekly collection + daily sending

---

## 🏗️ Architecture

```
         Workflow 1: Collect (weekly)              Workflow 2: Send (daily)
    ┌──────────────────────────────────┐      ┌──────────────────────────┐
    │  Pick Category → Research →      │      │  Filter unsent by age →  │
    │  Validate → Dedup → Translate    │      │  Pick random → Format →  │
    │         ↓ (retry ≤3x)            │      │  Send to Slack           │
    └──────────┬───────────────────────┘      └────────┬─────────────────┘
               │                                       │
               ▼                                       ▼
         recommendations.csv ◄─────────────────── read & mark sent
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd daily-child-dev-alert

# Create venv and install dependencies from pyproject.toml
uv sync
source .venv/bin/activate
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env`:
```env
OPENROUTER_API_KEY=your_key_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
CHILD_BIRTHDATE=2025-09-15
CHILD_NAME=Baby
```

### 3. Collect Recommendations

```bash
# Collect 1 recommendation (age auto-computed from birthdate)
python main.py collect

# Collect 5 recommendations
python main.py collect --count 5

# Override age manually
python main.py collect --age "6 months" --count 3
```

### 4. Send to Slack

```bash
# Preview in console
python main.py send --dry-run

# Send to Slack
python main.py send
```

---

## ⚙️ GitHub Actions

Both workflows run automatically when configured:

| Workflow | Schedule (UTC) | Schedule (PST) | What it does |
|---|---|---|---|
| **Collect** | Daily (10:00 AM UTC) | Daily (2:00 AM PST) | Generates 2 recommendations, commits CSV |
| **Send** | Daily (2:00 PM UTC) | Daily (6:00 AM PST) | Sends 1 age-appropriate recommendation to Slack |

### Required Secrets

| Secret | Description |
|---|---|
| `OPENROUTER_API_KEY` | [OpenRouter API key](https://openrouter.ai/settings/keys) |
| `SLACK_WEBHOOK_URL` | [Slack Incoming Webhook](https://api.slack.com/messaging/webhooks) |
| `CHILD_BIRTHDATE` | Baby's birthdate in `YYYY-MM-DD` format |
| `CHILD_NAME` | Name shown in Slack greeting |

### Optional Variables

| Variable | Default |
|---|---|
| `OPENROUTER_MODEL` | `google/gemini-2.0-flash-001` |

---

## 📁 Project Structure

```
├── main.py              # Unified CLI (main.py collect / main.py send)
├── collect.py           # Workflow 1: LangGraph pipeline → CSV
├── send.py              # Workflow 2: CSV → Slack (age-filtered)
├── graph.py             # LangGraph StateGraph with retry loops
├── agents/
│   ├── state.py         # Shared state definition
│   ├── researcher.py    # Generates recommendations with scientific refs
│   ├── validator.py     # Age-appropriateness & safety check
│   ├── dedup.py         # LLM semantic similarity vs history
│   └── translator.py    # Korean translation
├── tracker.py           # CSV read/write, sent tracking
├── slack_sender.py      # Slack webhook POST
├── config.py            # .env loader + age computation from birthdate
├── .github/workflows/
│   ├── collect.yml      # Weekly collection Action
│   └── send.yml         # Daily send Action
├── pyproject.toml       # Dependencies
└── .env.example         # Configuration template
```

---

## 🧠 How It Works

### Collect Pipeline (LangGraph)

1. **Pick Category** — randomly selects from 6 categories: exercise, toy, book, health tip, development tip, or safety tip
2. **Researcher Agent** — generates a recommendation with steps, reasoning, and a verified reference (DOI link or official medical authority URL)
3. **Validator Agent** — checks age-appropriateness and safety; rejects → retry
4. **Dedup Agent** — compares against last 30 CSV entries using LLM semantic similarity; duplicate → retry
5. **Translator Agent** — translates to Korean preserving all links and citations
6. Saves to `recommendations.csv` with `sent=false`

### Send Pipeline

1. Computes child's current age from `CHILD_BIRTHDATE`
2. Filters unsent recommendations matching the current age
3. Randomly picks one
4. Formats a Korean-language Slack Block Kit message
5. Sends via webhook, marks as `sent=true` in CSV

---

## 📋 CSV Format

```csv
date,type,name_en,name_kr,age_group,skill_area,reasoning,reference,reference_link,english_content,korean_content,amazon_link,sent
```

---

## 🤖 Built With

This project was primarily created with **Antigravity** and **Claude Opus 4.6**.

---

## 📄 License

MIT
