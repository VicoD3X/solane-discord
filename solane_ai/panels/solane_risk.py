from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import discord

PANEL_ROUTE_RISK = 0x7AAACE
FOOTER_TEXT = "Data from Solane API - Proprietary license"

EMOJI_WARNING = "\u26A0\ufe0f"
EMOJI_ALERT = "\U0001F6A8"
EMOJI_TRIANGLE = "\U0001F53B"
EMOJI_SAFE = "\u2705"
EMOJI_SOURCE = "\U0001F50E"
EMOJI_DIAMOND = "\U0001F536"
EMOJI_WORMHOLE = "\U0001F573\ufe0f"


def build_solane_risk_embed(snapshot: dict[str, Any]) -> discord.Embed:
    route_risk = _route_risk(snapshot)

    embed = discord.Embed(
        title="SOLANE RISK / GLOBAL WATCH",
        description="Operational route watch for active pipe danger and elevated EVE risk signals.",
        color=PANEL_ROUTE_RISK,
        timestamp=datetime.now(UTC),
    )
    embed.add_field(
        name=f"{EMOJI_WARNING} HIGHSEC CRITICAL",
        value=_critical_lines(
            route_risk.get("highSecCriticalSystems") or [],
            empty="No HighSec pipe flagged.",
        ),
        inline=True,
    )
    embed.add_field(
        name=f"{EMOJI_ALERT} LOW-SEC CRITICAL",
        value=_critical_lines(
            route_risk.get("lowSecCriticalSystems") or [],
            empty="No Low-Sec system flagged.",
        ),
        inline=False,
    )
    embed.add_field(
        name=f"{EMOJI_TRIANGLE} POCHVEN CRITICAL",
        value=_critical_lines(
            route_risk.get("pochvenCriticalSystems") or [],
            empty="No Pochven system flagged.",
        ),
        inline=False,
    )
    embed.add_field(
        name=f"{EMOJI_DIAMOND} NS NPC CRITICAL",
        value=_critical_lines(
            route_risk.get("npcNullSecCriticalSystems") or [],
            empty="No NPC nullsec system flagged.",
        ),
        inline=False,
    )
    embed.add_field(
        name=f"{EMOJI_WORMHOLE} THERA STATUS",
        value=_thera_status_line(route_risk.get("theraStatus")),
        inline=False,
    )
    embed.add_field(
        name=f"{EMOJI_SAFE} RECENTLY SAFER",
        value=_recently_safer_lines(
            route_risk.get("recentlySaferSystems") or [],
            empty="No recent safer feed yet.",
        ),
        inline=False,
    )
    _append_source_field(embed, snapshot)
    embed.set_footer(text=FOOTER_TEXT)
    return embed


def _route_risk(snapshot: dict[str, Any]) -> dict[str, Any]:
    summary = snapshot.get("botSummary")
    if not isinstance(summary, dict):
        return {}
    route_risk = summary.get("routeRisk")
    return route_risk if isinstance(route_risk, dict) else {}


def _append_source_field(embed: discord.Embed, snapshot: dict[str, Any]) -> None:
    update_time = _format_utc_time(_api_updated_at(snapshot))
    embed.add_field(
        name=f"{EMOJI_SOURCE} SOURCE",
        value=f"Last API update: `{update_time}`",
        inline=False,
    )


def _api_updated_at(snapshot: dict[str, Any]) -> Any:
    summary = snapshot.get("botSummary")
    if isinstance(summary, dict):
        return summary.get("generatedAt")
    return snapshot.get("generatedAt")


def _critical_lines(items: list[dict[str, Any]], empty: str) -> str:
    if not items:
        return empty
    ordered = sorted(
        items,
        key=lambda item: (
            -(int(item.get("shipKillsLastHour") or 0)),
            -(int(item.get("score") or 0)),
            str(item.get("name") or "Unknown"),
        ),
    )
    return "\n".join(_critical_item_line(item) for item in ordered[:8])


def _critical_item_line(item: dict[str, Any]) -> str:
    service = _short_service(item.get("serviceType"))
    service_suffix = f" {service}" if service else ""
    kills = _kills_label(item.get("shipKillsLastHour"))
    duration = _critical_duration_label(item.get("criticalAt"))
    return f"**{item.get('name', 'Unknown')}**{service_suffix} `{kills}` | `{duration}`"


def _thera_status_line(item: Any) -> str:
    if not isinstance(item, dict):
        return "**Thera** `Unavailable` `? kills/h`"
    status = item.get("label") or item.get("status") or "Unavailable"
    kills = _kills_label(item.get("shipKillsLastHour"))
    duration = ""
    if _lower(item.get("level")) == "critical":
        duration = f" | `{_critical_duration_label(item.get('criticalAt'))}`"
    return f"**{item.get('name') or 'Thera'}** `{status}` | `{kills}`{duration}"


def _recently_safer_lines(items: list[dict[str, Any]], empty: str) -> str:
    if not items:
        return empty
    lines = []
    for item in items[:6]:
        service = _short_service(item.get("serviceType"))
        service_suffix = f" {service}" if service else ""
        kills = _kills_label(item.get("shipKillsLastHour"))
        safer = _safer_duration_label(item.get("saferAt"))
        lines.append(f"**{item.get('name', 'Unknown')}**{service_suffix} `{kills}` | `{safer}`")
    return "\n".join(lines)


def _kills_label(value: Any) -> str:
    if value is None:
        return "? kills/h"
    return f"{value} kills/h"


def _critical_duration_label(value: Any) -> str:
    parsed = _parse_time(value)
    if parsed is None:
        return "flagged"

    minutes = max(int((datetime.now(UTC) - parsed).total_seconds() // 60), 0)
    if minutes < 60:
        return f"flagged {minutes} min"

    hours, remainder = divmod(minutes, 60)
    if remainder == 0:
        return f"flagged {hours}h"
    return f"flagged {hours}h {remainder}m"


def _safer_duration_label(value: Any) -> str:
    parsed = _parse_time(value)
    if parsed is None:
        return "cooled"

    minutes = max(int((datetime.now(UTC) - parsed).total_seconds() // 60), 0)
    if minutes < 60:
        return f"cooled {minutes} min"

    hours, remainder = divmod(minutes, 60)
    if remainder == 0:
        return f"cooled {hours}h"
    return f"cooled {hours}h {remainder}m"


def _short_service(value: Any) -> str:
    if value == "HighSec":
        return "HS"
    if value == "LowSec":
        return "LS"
    if value == "NpcNullSec":
        return "NS NPC"
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


def _lower(value: Any) -> str:
    return str(value or "").casefold()
