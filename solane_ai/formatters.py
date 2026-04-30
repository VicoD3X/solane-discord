from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import discord

SOLANE_PURPLE = 0xA855F7
SOLANE_BLUE = 0x19A8FF
SOLANE_GOLD = 0xFFD66A
SOLANE_RED = 0xDB1A1A
SOLANE_ORANGE = 0xFFC81E
SOLANE_GREEN = 0x67C090
PANEL_ROUTE_RISK = 0x7AAACE
PANEL_CORRUPTION = 0x1A2CA3
PANEL_SERVICE = 0x17C079
SOURCE_URL = "https://solane-run.app/route-intel"
FOOTER_TEXT = "Data from Solane API - Proprietary license"

EMOJI_SATELLITE = "\U0001F6F0\ufe0f"
EMOJI_RED = "\U0001F534"
EMOJI_HOURGLASS = "\u23F3"
EMOJI_BRICKS = "\U0001F9F1"
EMOJI_GREEN = "\U0001F7E2"
EMOJI_SOURCE = "\U0001F50E"
EMOJI_CYCLONE = "\U0001F300"
EMOJI_BLUE = "\U0001F535"
EMOJI_PURPLE = "\U0001F7E3"
EMOJI_BRAIN = "\U0001F9E0"
EMOJI_SATELLITE_DISH = "\U0001F4E1"
EMOJI_TIMER = "\u23F1\ufe0f"
EMOJI_TRUCK = "\U0001F69A"
EMOJI_RECEIPT = "\U0001F9FE"


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
        PanelMessage("risk", "SOLANE API - Route Risk", build_route_risk_embed(snapshot)),
        PanelMessage("corruption", "SOLANE API - Corruption Watch", build_corruption_embed(snapshot)),
        PanelMessage("service", "SOLANE API - Service Intel", build_service_embed(snapshot)),
    ]


def build_route_risk_embed(snapshot: dict[str, Any]) -> discord.Embed:
    overview = _overview(snapshot)
    bot_summary = _bot_summary(snapshot)
    route_risk = bot_summary.get("routeRisk") if isinstance(bot_summary.get("routeRisk"), dict) else {}
    crossroads = ((overview.get("crossroads") or {}).get("items") or []) if overview else []
    danger = [item for item in crossroads if _lower(item.get("label")) == "danger"]
    restricted = route_risk.get("restrictedSystems") or []
    static_restricted = [item for item in restricted if item.get("source") == "static"]
    dynamic_restricted = snapshot.get("activeRestrictedSystems") or [
        item for item in restricted if item.get("source") != "static"
    ]
    recently_open = snapshot.get("recentlyOpenSystems") or []

    embed = _base_embed(
        title=f"{EMOJI_SATELLITE} SOLANE API / ROUTE RISK",
        description="Operational route watch for active pipe danger and Solane restrictions.",
        color=PANEL_ROUTE_RISK,
    )
    embed.add_field(
        name=f"{EMOJI_RED} HIGHSEC DANGER",
        value=_system_lines(danger, empty="No HighSec pipe in Danger."),
        inline=True,
    )
    embed.add_field(
        name=f"{EMOJI_HOURGLASS} TEMP RESTRICTED",
        value=_dynamic_restricted_lines(dynamic_restricted, empty="No temporary closure."),
        inline=False,
    )
    embed.add_field(
        name=f"{EMOJI_GREEN} RECENTLY OPEN",
        value=_recently_open_lines(recently_open, empty="No recent reopening feed yet."),
        inline=False,
    )
    embed.add_field(
        name=f"{EMOJI_BRICKS} PERMA RESTRICTED",
        value=_static_watchlist_lines(static_restricted),
        inline=False,
    )
    _append_source_field(embed, snapshot)
    embed.set_footer(text=FOOTER_TEXT)
    return embed


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


def build_service_embed(snapshot: dict[str, Any]) -> discord.Embed:
    health = snapshot.get("health") or {}
    eve = snapshot.get("eveStatus") or {}
    overview = _overview(snapshot)
    bot_summary = _bot_summary(snapshot)
    service = bot_summary.get("service") if isinstance(bot_summary.get("service"), dict) else {}
    errors = snapshot.get("errors") or []

    api_state = "Operational" if health and not errors else "Partial" if health else "Unavailable"
    players = eve.get("players")
    vip = eve.get("vip")
    tranquility = "VIP mode" if vip else f"{players:,} pilots" if isinstance(players, int) else "Syncing"
    server_version = str(eve.get("server_version") or "Unavailable")
    esi_sync = _format_utc_time(eve.get("fetched_at"))
    solane_status = str(service.get("label") or "Open")

    embed = _base_embed(
        title=f"{EMOJI_GREEN} SOLANE API / SERVICE INTEL",
        description="Public service status for Solane Run operations.",
        color=PANEL_SERVICE,
    )
    embed.add_field(name=f"{EMOJI_BRAIN} API LINK", value=_service_value(api_state), inline=True)
    embed.add_field(
        name=f"{EMOJI_SATELLITE_DISH} EVE CLUSTER",
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


def _system_lines(items: list[dict[str, Any]], empty: str) -> str:
    if not items:
        return empty
    lines = []
    for item in items[:6]:
        system = item.get("system") or {}
        name = system.get("name", "Unknown")
        kills = item.get("shipKillsLastHour")
        kills_text = kills if kills is not None else "?"
        lines.append(f"**{name}** `{kills_text}/h`")
    return "\n".join(lines)


def _dynamic_restricted_lines(items: list[dict[str, Any]], empty: str) -> str:
    if not items:
        return empty
    latest_possible = datetime.max.replace(tzinfo=UTC)
    ordered = sorted(
        items,
        key=lambda item: _parse_time(item.get("closedAt")) or latest_possible,
    )
    return "\n".join(_dynamic_restricted_item_label(item) for item in ordered[:12])


def _dynamic_restricted_item_label(item: dict[str, Any]) -> str:
    service = _short_service(item.get("serviceType")) or "Unknown"
    duration = _closed_duration_label(item.get("closedAt"))
    return f"**{item.get('name', 'Unknown')}** {service} `{duration}`"


def _static_watchlist_lines(items: list[dict[str, Any]]) -> str:
    if not items:
        return "No permanent restriction."

    names = sorted(str(item.get("name", "Unknown")) for item in items)
    return " • ".join(f"**{name}**" for name in names)


def _recently_open_lines(items: list[dict[str, Any]], empty: str) -> str:
    if not items:
        return empty
    lines = []
    for item in items[:4]:
        service = _short_service(item.get("serviceType"))
        service_suffix = f" {service}" if service else ""
        lines.append(f"**{item.get('name', 'Unknown')}**{service_suffix} `Open`")
    return "\n".join(lines)


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


def _closed_duration_label(value: Any) -> str:
    parsed = _parse_time(value)
    if parsed is None:
        return "closed"

    minutes = max(int((datetime.now(UTC) - parsed).total_seconds() // 60), 0)
    if minutes < 60:
        return f"closed {minutes} min"

    hours, remainder = divmod(minutes, 60)
    if remainder == 0:
        return f"closed {hours}h"
    return f"closed {hours}h {remainder}m"


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
