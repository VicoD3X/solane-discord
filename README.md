# Solane AI

![CI](https://github.com/VicoD3X/solane-discord/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.13-3776AB?logo=python&logoColor=white)
![Discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?logo=discord&logoColor=white)
![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-a855f7)

**Solane AI** is the Discord intel companion for **Solane Run**, a premium EVE
Online freight service. The bot publishes clean, persistent Discord embeds for
route risk, HighSec danger, corruption watch and service status.

Solane AI is intentionally a thin public client. The private Solane API remains
the source of truth for ESI, zKillboard, route risk, pricing policy and internal
freight logic.

```text
EVE ESI / zKillboard / CCP web
              |
          solane-api
              |
          Solane AI
              |
       Discord channels
```

## Features

- Persistent Discord panels: post once, then edit.
- Route risk feed for HighSec danger, restricted systems and reopened systems.
- Corruption LVL4/LVL5 watch.
- Service board for Solane API and Tranquility status.
- Public-safe implementation with no Discord token or private pricing logic.
- Docker-ready deployment for the Solane Run VPS network.

## Beta Panels

| Panel | Purpose |
| --- | --- |
| `Route Risk` | HighSec danger, restricted systems and recently reopened systems. |
| `Corruption Watch` | LVL5 and LVL4 corruption systems from Solane API. |
| `Service Intel` | Solane API state, Tranquility status and public service indicators. |

## Repository Boundary

This repository is safe to keep public because it does **not** contain:

- Discord bot tokens.
- Solane API secrets.
- Private ESI credentials.
- Pricing formulas.
- Risk formulas.

All sensitive logic belongs in the private `solane-api` service.

## Discord Install

Solane AI uses the Discord Gateway through `discord.py`; it does not need an HTTP
interactions endpoint for the beta.

Suggested minimal invite URL:

```text
https://discord.com/oauth2/authorize?client_id=1498868232386510948&scope=bot&permissions=84992
```

Permissions included:

- View Channels
- Send Messages
- Embed Links
- Read Message History

The value `1498868232386510948` is the public Discord application/client ID. The
real bot token is a separate secret from the Discord Developer Portal **Bot** tab
and must only live in `.env` or production secrets.

## Local Setup

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Fill `.env` with:

```env
DISCORD_TOKEN=
SOLANE_API_BASE_URL=https://solane-run.app
DISCORD_RISK_CHANNEL_ID=
DISCORD_CORRUPTION_CHANNEL_ID=
DISCORD_SERVICE_CHANNEL_ID=
```

Run the bot:

```powershell
.\.venv\Scripts\python.exe -m solane_ai
```

## Docker

```powershell
docker compose up --build -d
```

In production, `SOLANE_API_BASE_URL` should target the private Docker network
service, usually:

```env
SOLANE_API_BASE_URL=http://solane-api:8000
```

## Checks

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall -q solane_ai tests
docker compose config
docker compose build
```

## Runtime State

Solane AI stores Discord message IDs in `data/solane-ai-state.json` so it can
edit existing panels instead of posting duplicates. The `data/` directory is
ignored by Git.

## Suggested GitHub Topics

`eve-online`, `discord-bot`, `discord-py`, `freight`, `logistics`, `route-intel`,
`python`, `docker`, `solane-run`, `new-eden`

## Legal

Solane AI is an independent tool for EVE Online logistics. It is not affiliated
with CCP Games. EVE Online and related marks belong to their respective owners.

This repository is proprietary. See [LICENSE](LICENSE).
