#!/usr/bin/env bash
set -e

if [ ! -f .env ]; then
    echo "❌ .env file not found. Copy .env.example and fill in your values."
    exit 1
fi

source .env

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN is not set in .env"
    exit 1
fi

if [ -z "$TELEGRAM_USER_ID" ]; then
    echo "❌ TELEGRAM_USER_ID is not set in .env"
    exit 1
fi

if [ -z "$HOST_DATA_DIR" ]; then
    echo "❌ HOST_DATA_DIR is not set in .env"
    exit 1
fi

if [ ! -f "$HOST_DATA_DIR/credentials.json" ]; then
    echo "❌ credentials.json not found in $HOST_DATA_DIR"
    exit 1
fi

if [ ! -f "$HOST_DATA_DIR/gmail_token.json" ]; then
    echo "❌ gmail_token.json not found in $HOST_DATA_DIR"
    echo "   Run auth.py locally to generate it, then copy it here."
    exit 1
fi

if ! command -v docker &>/dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

echo "✅ Config looks good"
echo "   Data dir: $HOST_DATA_DIR"
echo ""
docker compose up -d --build
echo ""
echo "✅ Bot is running. Logs: docker compose logs -f"
