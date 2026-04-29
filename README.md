# Solane AI Discord Bot

Solane AI publishes live EVE Online freight intel for Solane Run through clean,
persistent Discord messages. It is intentionally a thin client: `solane-api`
remains the source of truth for ESI, zKillboard, Route Intel, risk controls,
pricing policy and service state.

## Beta Scope

- Route risk and HighSec danger watch.
- Corruption LVL4/LVL5 watch.
- Service and Tranquility status.
- Persistent Discord messages: post once, then edit.
- Public-safe codebase: no Discord token, API secret or pricing logic in Git.

## Local Setup

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Fill `.env` with:

- `DISCORD_TOKEN`
- `DISCORD_RISK_CHANNEL_ID`
- `DISCORD_CORRUPTION_CHANNEL_ID`
- `DISCORD_SERVICE_CHANNEL_ID`
- `SOLANE_API_BASE_URL`

Then run:

```powershell
.\.venv\Scripts\python.exe -m solane_ai
```

## Discord Install

The beta bot uses Gateway, not HTTP interactions. Suggested minimal invite URL:

```text
https://discord.com/oauth2/authorize?client_id=1498868232386510948&scope=bot&permissions=84992
```

Permissions included:

- View Channels
- Send Messages
- Embed Links
- Read Message History

The value `1498868232386510948` is the public application/client ID. The real
bot token is a separate secret from the Discord Developer Portal Bot tab and
must only live in `.env` or production secrets.

## Docker

```powershell
docker compose up --build -d
```

The bot expects `solane-api` to be reachable from the same Docker network in
production.

## Security

- Never commit `.env`, `data/`, `.cache/`, logs or Discord tokens.
- The bot needs only minimal Discord permissions: view channel, send messages,
  embed links, read message history, manage its own messages.
- Business-sensitive logic belongs in the private Solane API, not in this bot.
