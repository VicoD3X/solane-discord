from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import discord

from .panels.engine_eta import build_engine_eta_embed
from .panels.solane_risk import build_solane_risk_embed

SOLANE_PURPLE = 0xA855F7
SOLANE_BLUE = 0x19A8FF
SOLANE_GOLD = 0xFFD66A
SOLANE_RED = 0xDB1A1A
SOLANE_ORANGE = 0xFFC81E
SOLANE_GREEN = 0x67C090
PANEL_CORRUPTION = 0x1A2CA3
SOURCE_URL = "https://solane-run.app/route-intel"
FOOTER_TEXT = "Data from Solane API - Proprietary license"

EMOJI_SOURCE = "\U0001F50E"
EMOJI_CYCLONE = "\U0001F300"
EMOJI_BLUE = "\U0001F535"
EMOJI_PURPLE = "\U0001F7E3"


@dataclass(frozen=True)
class PanelMessage:
    key: str
    title: str
    embed: discord.Embed

    @property
    def content_hash(self) -> str:
        payload = self.embed.to_dict()
        return hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()


def build_panels(snapshot: dict[str, Any]) -> list[PanelMessage]:
    return [
        PanelMessage("risk", "SOLANE RISK / GLOBAL WATCH", build_solane_risk_embed(snapshot)),
        PanelMessage("corruption", "SOLANE API - Corruption Watch", build_corruption_embed(snapshot)),
        PanelMessage("service", "SOLANE ENGINE ETA", build_engine_eta_embed(snapshot)),
    ]


def build_corruption_embed(snapshot: dict[str, Any]) -> discord.Embed:
    overview = _overview(snapshot)
    items = ((overview.get("corruption") or {}).get("items") or []) if overview else []
    lvl5 = [item for item in items if int(item.get("corruptionState") or 0) >= 5]
    lvl4 = [item for item in items if int(item.get("corruptionState") or 0) == 4]

    embed = _base_embed(
        title=f"{EMOJI_CYCLONE} SOLANE API / CORRUPTION WATCH",
        description="Insurgency corruption level 4 and 5 systems.",
        color=PANEL_CORRUPTION,
    )
    embed.add_field(
        name=f"{EMOJI_BLUE} LVL5 CRITICAL",
        value=_corruption_lines(lvl5, empty="No LVL5 corruption detected."),
        inline=True,
    )
    embed.add_field(
        name=f"{EMOJI_PURPLE} LVL4 WATCH",
        value=_corruption_lines(lvl4, empty="No LVL4 corruption detected."),
        inline=True,
    )
    _append_source_field(embed, snapshot)
    embed.set_footer(text=FOOTER_TEXT)
    return embed


def _base_embed(title: str, description: str, color: int) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(UTC),
    )
    return embed


def _append_source_field(embed: discord.Embed, snapshot: dict[str, Any]) -> None:
    update_time = _format_utc_time(_api_updated_at(snapshot))
    embed.add_field(
        name=f"{EMOJI_SOURCE} SOURCE",
        value=f"Last API update: `{update_time}`\nCheck our source: {SOURCE_URL}",
        inline=False,
    )


def _api_updated_at(snapshot: dict[str, Any]) -> Any:
    bot_summary = _bot_summary(snapshot)
    return bot_summary.get("generatedAt") or snapshot.get("generatedAt")


def _overview(snapshot: dict[str, Any]) -> dict[str, Any]:
    overview = snapshot.get("routeIntel")
    return overview if isinstance(overview, dict) else {}


def _bot_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    summary = snapshot.get("botSummary")
    return summary if isinstance(summary, dict) else {}


def _corruption_lines(items: list[dict[str, Any]], empty: str) -> str:
    if not items:
        return empty
    lines = []
    for item in items[:10]:
        system = item.get("system") or {}
        name = system.get("name", "Unknown")
        service = _short_service(system.get("serviceType"))
        service_prefix = f"{service} - " if service else ""
        level = item.get("corruptionState", "?")
        corruption = round(float(item.get("corruptionPercentage") or 0))
        suppression = round(float(item.get("suppressionPercentage") or 0))
        lines.append(f"**{name}**\n`{service_prefix}LVL{level}` - `{corruption}% / {suppression}%`")
    return "\n".join(lines)


def _count_label(overview: dict[str, Any], key: str) -> str:
    section = overview.get(key) if overview else None
    if not isinstance(section, dict):
        return "Unavailable"
    label = section.get("label")
    if label:
        return str(label)
    items = section.get("items")
    return f"{len(items)} items" if isinstance(items, list) else "Unavailable"


def _lower(value: Any) -> str:
    return str(value or "").casefold()


def _short_service(value: Any) -> str:
    if value == "HighSec":
        return "HS"
    if value == "LowSec":
        return "LS"
    return str(value or "")


def _format_utc_time(value: Any) -> str:
    if not value:
        return "Unavailable"
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).strftime("%H:%M EVE")
    except ValueError:
        return str(value)


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
