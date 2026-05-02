# Security Policy

SOLANE API is a public-facing Discord client for Solane Run. The repository is
safe to publish because it does not contain Discord tokens, API secrets, private
ESI credentials or pricing formulas.

The bot is only a publisher. Operational intelligence must come from Solane
Engine through `SOLANE_API_BASE_URL`; this repository must not add direct ESI,
CCP web, zKillboard or private ESI integrations.

Report security issues privately to the project owner. Do not open public issues
with secrets, exploit details or live infrastructure information.
