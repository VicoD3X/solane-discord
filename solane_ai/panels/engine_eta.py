from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import discord

PANEL_ENGINE_ETA_GREEN = 0x17C079
PANEL_ENGINE_ETA_RED = 0xFF1A1A
FOOTER_TEXT = "Data from Solane Engine - status.eveonline.com"

EMOJI_ANTENNA = "\U0001F4E1"
EMOJI_BRAIN = "\U0001F9E0"
EMOJI_CYCLONE = "\U0001F300"
EMOJI_GLOBE = "\U0001F310"
EMOJI_RECEIPT = "\U0001F9FE"
EMOJI_SOURCE = "\U0001F50E"
EMOJI_TIMER = "\u23F1\ufe0f"
EMOJI_TRUCK = "\U0001F69A"
EMOJI_SIGNAL = "\U0001F4F6"
EMOJI_UPTIME = "\u23F2\ufe0f"
EMOJI_SHIELD = "\U0001F6E1\ufe0f"


def build_engine_eta_embed(snapshot: dict[str, Any]) -> discord.Embed:
    health = snapshot.get("health") or {}
    eve = _eve_status(snapshot)
    overview = _overview(snapshot)
    bot_summary = _bot_summary(snapshot)
    service = bot_summary.get("service") if isinstance(bot_summary.get("service"), dict) else {}
    errors = _errors(snapshot)

    api_state = "Operational" if health and not errors else "Partial" if health else "Unavailable"
    players = eve.get("players")
    vip = eve.get("vip")
    if vip:
        tranquility = "VIP / Maintenance"
    elif isinstance(players, int):
        tranquility = f"{players:,} pilots"
    else:
        tranquility = "Syncing"
    server_version = str(eve.get("server_version") or "Unavailable")
    esi_sync = _format_utc_time(eve.get("fetched_at"))
    solane_status = str(service.get("label") or "Open")

    embed = discord.Embed(
        title=f"{EMOJI_ANTENNA} SOLANE ENGINE ETA",
        description="Public service status for Solane Engine and EVE Online telemetry.",
        color=_eta_color(snapshot),
        timestamp=datetime.now(UTC),
    )
    embed.add_field(name=f"{EMOJI_BRAIN} API LINK", value=_service_value(api_state), inline=True)
    embed.add_field(
        name=f"{EMOJI_GLOBE} EVE CLUSTER",
        value=_service_value(tranquility),
        inline=True,
    )
    embed.add_field(name=f"{EMOJI_TIMER} ESI SYNC", value=_service_value(esi_sync), inline=True)
    embed.add_field(name=f"{EMOJI_TRUCK} SERVICE", value=_service_value(solane_status), inline=True)
    embed.add_field(name=f"{EMOJI_RECEIPT} BUILD", value=_service_value(server_version), inline=True)
    embed.add_field(
        name=f"{EMOJI_CYCLONE} CORRUPTION",
        value=_service_value(_count_label(overview, "corruption")),
        inline=True,
    )
    embed.add_field(
        name=f"{EMOJI_SHIELD} CLUSTER MODE",
        value=_service_value(_cluster_mode(snapshot)),
        inline=True,
    )
    embed.add_field(
        name=f"{EMOJI_UPTIME} CLUSTER UPTIME",
        value=_service_value(_cluster_uptime(eve)),
        inline=True,
    )
    embed.add_field(name=f"{EMOJI_SIGNAL} ESI FEED", value=_service_value(_esi_feed(snapshot)), inline=True)
    _append_eta_source_field(embed, snapshot)
    embed.set_footer(text=FOOTER_TEXT)
    return embed


def _eta_color(snapshot: dict[str, Any]) -> int:
    eve = _eve_status(snapshot)
    if not eve or "eve_status" in _errors(snapshot) or eve.get("vip") is True:
        return PANEL_ENGINE_ETA_RED
    return PANEL_ENGINE_ETA_GREEN


def _cluster_mode(snapshot: dict[str, Any]) -> str:
    eve = _eve_status(snapshot)
    if not eve or "eve_status" in _errors(snapshot):
        return "Unavailable"
    return "VIP / Maintenance" if eve.get("vip") is True else "Online"


def _cluster_uptime(eve: dict[str, Any]) -> str:
    start_time = _parse_time(eve.get("start_time"))
    if start_time is None:
        return "Unavailable"

    minutes = max(int((datetime.now(UTC) - start_time).total_seconds() // 60), 0)
    days, day_remainder = divmod(minutes, 1440)
    hours, minute_remainder = divmod(day_remainder, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minute_remainder}m"
    return f"{minute_remainder}m"


def _esi_feed(snapshot: dict[str, Any]) -> str:
    eve = _eve_status(snapshot)
    if not eve or "eve_status" in _errors(snapshot):
        return "Unavailable"

    fetched_at = _parse_time(eve.get("fetched_at"))
    if fetched_at is None:
        return "Unavailable"
    age_seconds = (datetime.now(UTC) - fetched_at).total_seconds()
    return "Fresh" if age_seconds <= 600 else "Delayed"


def _append_eta_source_field(embed: discord.Embed, snapshot: dict[str, Any]) -> None:
    update_time = _format_utc_time(_api_updated_at(snapshot))
    embed.add_field(name=f"{EMOJI_SOURCE} SOURCE", value=f"Last API update: `{update_time}`", inline=False)


def _api_updated_at(snapshot: dict[str, Any]) -> Any:
    bot_summary = _bot_summary(snapshot)
    return bot_summary.get("generatedAt") or snapshot.get("generatedAt")


def _overview(snapshot: dict[str, Any]) -> dict[str, Any]:
    overview = snapshot.get("routeIntel")
    return overview if isinstance(overview, dict) else {}


def _bot_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    summary = snapshot.get("botSummary")
    return summary if isinstance(summary, dict) else {}


def _eve_status(snapshot: dict[str, Any]) -> dict[str, Any]:
    eve = snapshot.get("eveStatus")
    return eve if isinstance(eve, dict) else {}


def _errors(snapshot: dict[str, Any]) -> list[str]:
    errors = snapshot.get("errors")
    return [str(error) for error in errors] if isinstance(errors, list) else []


def _service_value(value: str) -> str:
    return f"`{value}`"


def _count_label(overview: dict[str, Any], key: str) -> str:
    section = overview.get(key) if overview else None
    if not isinstance(section, dict):
        return "Unavailable"
    label = section.get("label")
    if label:
        return str(label)
    items = section.get("items")
    return f"{len(items)} items" if isinstance(items, list) else "Unavailable"


def _format_utc_time(value: Any) -> str:
    parsed = _parse_time(value)
    if parsed is None:
        return "Unavailable" if not value else str(value)
    return parsed.strftime("%H:%M EVE")


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
