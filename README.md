<div align="center">

# telegram-mail-bot

A private Gmail digest bot for Telegram. Polls your inbox, summarizes new emails with a local LLM (Ollama), and delivers bullet-point digests straight to your phone.

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-v20+-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://github.com/python-telegram-bot/python-telegram-bot)
[![License](https://img.shields.io/badge/License-MIT-6B7280?style=flat-square)](LICENSE)

</div>

---

## Features

- **Auto-polling** — checks Gmail every N minutes in the background
- **AI summaries** — emails are summarized by a local Ollama instance (no data leaves your server)
- **Pause / Snooze** — pause polling or snooze for 4h directly from the keyboard
- **History** — view the last 5 summaries at any time
- **Single-user auth** — only your Telegram ID can interact with the bot

---

## Tech Stack

| | Tool |
|-|------|
| Language | Python 3.12+ |
| Telegram | python-telegram-bot v20+ |
| Gmail | Google Gmail API + OAuth 2.0 |
| LLM | [Ollama](https://ollama.com) (local) |
| Runtime | Docker |

---

## Project Structure

```
telegram-mail-bot/
├── main.py
├── auth.py                      # Run locally once to generate gmail_token.json
├── Dockerfile
├── docker-compose.yml
├── setup.sh
├── handlers/
│   ├── command_handlers.py      # Keyboard buttons and auth check
│   └── polling_handler.py       # Background email polling task
└── services/
    ├── gmail_service.py         # Gmail API integration
    ├── ollama_service.py        # Ollama HTTP client
    ├── prompt_builder.py        # LLM prompt formatting
    └── state_manager.py         # Persist state, history, snooze
```

---

## Setup

### 1. Gmail OAuth (run once, locally)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → enable **Gmail API**
3. **Credentials** → OAuth 2.0 Client ID → Desktop app → download JSON → save as `credentials.json`
4. **OAuth consent screen** → Test users → add your Gmail address
5. Run `auth.py` on your **local machine** (requires a browser):

```bash
pip install google-auth-oauthlib python-dotenv
python auth.py
```

This opens a browser → sign in → generates `gmail_token.json`.

6. Copy both files to your server's data directory:

```bash
scp credentials.json gmail_token.json user@server:/path/to/data/
```

---

### 2. Configure

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_USER_ID` | Your Telegram ID — from [@userinfobot](https://t.me/userinfobot) |
| `HOST_DATA_DIR` | Absolute path to your data directory on the host |
| `OLLAMA_HOST` | Ollama server URL (default: `http://localhost:11434`) |
| `OLLAMA_MODEL` | Model name (default: `llama3.2:3b`) |
| `POLLING_INTERVAL_SECONDS` | How often to check Gmail (default: `120`) |

---

### 3. Ollama

```bash
ollama pull llama3.2:3b   # fast, ~2GB RAM
# or
ollama pull llama3.1:8b   # better quality, ~5GB RAM
```

If Ollama runs on a different server, set `OLLAMA_HOST=http://<server_ip>:11434`.

---

### 4. Run

```bash
bash setup.sh
```

Logs: `docker compose logs -f`

---

## Interface

```
[ 📋 History ] [ 🗑 Clear History ]
[ ⏸ Pause   ] [ 💤 Snooze 4h    ]
[ ℹ️ Status  ]
```

| Button | Description |
|---|---|
| History | Last 5 email summaries |
| Clear History | Wipe stored summaries |
| Pause / Resume | Stop or restart email polling |
| Snooze 4h | Pause for 4 hours, then auto-resume |
| Status | Current polling state and last poll time |

---

## Summary Format

```
📮 New emails

[URGENT] From: boss@company.com
Subject: Server down — prod DB
• Restore from backup immediately
• ETA expected by 18:00

[INFO] From: newsletter@github.com
Subject: GitHub Digest — April
• 3 repos starred by your team this week
```

---

## License

[MIT](LICENSE)
