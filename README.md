# 🧠 RepoMind — AI GitHub Repository Analyzer

RepoMind uses **Grok API (xAI)** + **LangChain** to analyze any public GitHub repository and produce a structured engineering report.

---

## 📋 Report Sections

- **Project Summary** — Purpose and scope
- **Tech Stack** — Languages, frameworks, tools detected
- **Code Quality** — Structure, patterns, documentation
- **Risks / Issues** — Severity-tagged issues
- **Improvement Suggestions** — Actionable recommendations
- **Production Readiness Score** — 0–10 with justification

---

## ⚙️ Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API key

Copy `.env.example` to `.env` and fill in your key:

```bash
cp .env.example .env
```

Edit `.env`:
```
GROK_API_KEY=your_grok_api_key_here
```

### 3. Run

```bash
# Interactive
python main.py

# With URL argument
python main.py https://github.com/psf/requests
```

---

## 📁 Project Structure

```
repomind/
├── main.py                  # Entry point
├── config.py                # Config + env loading
├── .env                     # Your API key (not committed)
├── .env.example             # Template
├── requirements.txt
├── tools/
│   └── github_tool.py       # GitHub API fetching
├── agents/
│   └── analyzer_agent.py    # LangChain + Grok chain
└── utils/
    └── parser.py            # Formatting helpers
```

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM Provider | Grok API (xAI) via OpenAI-compatible endpoint |
| LLM Framework | LangChain (latest) |
| GitHub Data | GitHub REST API v3 (no auth required) |
| Language | Python 3.10+ |
