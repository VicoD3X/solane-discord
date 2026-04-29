# Contributing

SOLANE API is currently developed as part of the Solane Run beta. Public feedback
is welcome, but the project remains proprietary and roadmap-driven.

## Good Contributions

- Bug reports with clear reproduction steps.
- Documentation improvements.
- Public-safe UI or formatting suggestions.
- Reliability improvements that do not move private logic into the bot.

## Boundaries

Please do not submit changes that add:

- Discord tokens or secrets.
- Private ESI credentials.
- Solane pricing formulas.
- Risk formulas that belong in the private API.
- Aggressive polling against Discord, ESI or zKillboard.

## Local Checks

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall -q solane_ai tests
```

