# SOLANE API

![CI](https://github.com/VicoD3X/solane-discord/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.13-3776AB?logo=python&logoColor=white)
![Discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?logo=discord&logoColor=white)
![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-a855f7)

**SOLANE API** is the Discord intel companion for **Solane Run**. The public
calculator is closed; the bot is now the main visible product surface and acts
as a daily EVE hauling intel copilot.

It publishes clean, persistent Discord embeds for route risk, control boards,
corruption watch and service status.

SOLANE API is intentionally a thin public client. The private Solane Engine
service remains the source of truth for ESI, zKillboard, route risk, corruption
intel and all operational rules. Its technical service/repository name remains
`solane-api` for deployment compatibility.

```text
EVE ESI / zKillboard / CCP web
              |
       Solane Engine
        (solane-api)
              |
          SOLANE API
              |
       Discord channels
```

## Features

- Persistent Discord panels: post once, then edit.
- Route risk global watch for HighSec, LowSec, Pochven, NPC nullsec and Thera.
- Control boards for selected HighSec pipes, Pochven systems, active LowSec / NPC nullsec systems and top gatekill pressure.
- Insurgency LVL4/LVL5 watch.
- Service board for Solane Engine and Tranquility status.
- Public-safe implementation with no Discord token, private ESI credentials, or route-risk engine.
- Docker-ready deployment for the Solane Run VPS network.

## Source of Truth

The Discord bot is the only active public publishing surface, but it is not the
data engine. It must only consume Solane Engine HTTP payloads, format Discord
embeds, and edit persistent Discord messages.

The bot must not call ESI, CCP web, zKillboard or private ESI directly, and it
must not duplicate risk, corruption, gate-kill, pricing or restriction logic.

## Beta Panels

| Panel | Purpose |
| --- | --- |
| `Solane Risk / Global Watch` | Critical route-risk systems and recently cooled signals. |
| `Solane Risk / Pipes Control` | Selected HighSec pipes with kills/h and hot gate intel. |
| `Solane Risk / Pochven Control` | Pochven systems with kills/h and hot gate intel. |
| `Solane Risk / Low-Sec Control` | Active LowSec systems from watched status upward, with kills/h and hot gate intel. |
| `Solane Risk / NS NPC Control` | Active NPC nullsec systems from watched status upward, with kills/h and hot gate intel. |
| `Solane Risk / Insurgency Watch` | LVL5 and LVL4 corruption systems from Solane Engine. |
| `Solane Engine ETA` | Solane Engine state, Tranquility status and ESI feed indicators. |

## Repository Boundary

This repository is safe to keep public because it does **not** contain:

- Discord bot tokens.
- Solane API secrets.
- Private ESI credentials.
- Risk formulas.
- Pricing formulas or legacy calculator logic.

All sensitive logic belongs in the private `solane-api` service.

## Discord Install

SOLANE API uses the Discord Gateway through `discord.py`; it does not need an HTTP
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

For the full local workspace with frontend + API, use the cockpit from the
sibling frontend repo:

```powershell
cd "D:\PROJECT\Solane Run"
npm run local:start:bot
npm run local:doctor
```

The cockpit starts the private API first, points the frontend at the active API
port, and injects the same local API URL into the bot process.

Standalone bot setup remains available:

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
DISCORD_PIPES_CHANNEL_ID=
DISCORD_POCHVEN_CHANNEL_ID=
DISCORD_LOWSEC_CHANNEL_ID=
DISCORD_NSNPC_CHANNEL_ID=
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

## VPS Deploy

Deploy the bot to the Solane Run VPS:

```powershell
.\scripts\deploy-vps.ps1
```

The deploy script reads the local `.env`, uploads a private
`/srv/solane-run/shared/solane-bot.env` with strict permissions, rebuilds the
Docker container, and starts it on the shared `solane-run` network.

The frontend and API are not redeployed by this bot script.

## Checks

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall -q solane_ai tests
docker compose config
docker compose build
```

## Runtime State

SOLANE API stores Discord message IDs in `data/solane-ai-state.json` so it can
edit existing panels instead of posting duplicates. The `data/` directory is
ignored by Git.

## Suggested GitHub Topics

`eve-online`, `discord-bot`, `discord-py`, `freight`, `logistics`, `route-intel`,
`python`, `docker`, `solane-run`, `new-eden`

## Legal

SOLANE API is an independent tool for EVE Online logistics. It is not affiliated
with CCP Games. EVE Online and related marks belong to their respective owners.

This repository is proprietary. See [LICENSE](LICENSE).
