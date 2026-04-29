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
        PanelMessage("risk", "Solane AI - Route Risk", build_route_risk_embed(snapshot)),
        PanelMessage("corruption", "Solane AI - Corruption Watch", build_corruption_embed(snapshot)),
        PanelMessage("service", "Solane AI - Service Intel", build_service_embed(snapshot)),
    ]


def build_route_risk_embed(snapshot: dict[str, Any]) -> discord.Embed:
    overview = _overview(snapshot)
    bot_summary = _bot_summary(snapshot)
    route_risk = bot_summary.get("routeRisk") if isinstance(bot_summary.get("routeRisk"), dict) else {}
    crossroads = ((overview.get("crossroads") or {}).get("items") or []) if overview else []
    danger = [item for item in crossroads if _lower(item.get("label")) == "danger"]
    restricted = route_risk.get("restrictedSystems") or []
    recently_open = snapshot.get("recentlyOpenSystems") or []

    embed = _base_embed(
        title="🛰️ SOLANE AI / ROUTE RISK",
        description="HighSec danger pipes, Solane restrictions and reopening signals.",
        color=PANEL_ROUTE_RISK,
    )
    embed.add_field(
        name="🔴 HIGHSEC DANGER",
        value=_system_lines(danger, empty="No HighSec pipe in Danger."),
        inline=True,
    )
    embed.add_field(
        name="⛔ RESTRICTED SYSTEM",
        value=_restricted_system_lines(restricted, empty="No restricted system."),
        inline=False,
    )
    embed.add_field(
        name="🟢 RECENTLY OPEN SYSTEM",
        value=_recently_open_lines(recently_open, empty="No recent reopening feed yet."),
        inline=False,
    )
    embed.set_footer(
        text="Solane AI - ETA is monitoring until Solane API exposes route-level recovery windows."
    )
    return embed


def build_corruption_embed(snapshot: dict[str, Any]) -> discord.Embed:
    overview = _overview(snapshot)
    items = ((overview.get("corruption") or {}).get("items") or []) if overview else []
    lvl5 = [item for item in items if int(item.get("corruptionState") or 0) >= 5]
    lvl4 = [item for item in items if int(item.get("corruptionState") or 0) == 4]

    embed = _base_embed(
        title="🌀 SOLANE AI / CORRUPTION WATCH",
        description="Insurgency corruption level 4 and 5 systems.",
        color=PANEL_CORRUPTION,
    )
    embed.add_field(
        name="🔵 LVL5 CRITICAL",
        value=_corruption_lines(lvl5, empty="No LVL5 corruption detected."),
        inline=True,
    )
    embed.add_field(
        name="🟣 LVL4 WATCH",
        value=_corruption_lines(lvl4, empty="No LVL4 corruption detected."),
        inline=True,
    )
    embed.set_footer(text="Solane AI - Corruption source remains CCP web via Solane API.")
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
        title="🟢 SOLANE AI / SERVICE INTEL",
        description="Public service status for Solane Run operations.",
        color=PANEL_SERVICE,
    )
    embed.add_field(name="🧠 API LINK", value=_service_value(api_state), inline=True)
    embed.add_field(name="📡 EVE CLUSTER", value=_service_value(tranquility), inline=True)
    embed.add_field(name="⏱️ ESI SYNC", value=_service_value(esi_sync), inline=True)
    embed.add_field(name="🚚 SERVICE", value=_service_value(solane_status), inline=True)
    embed.add_field(name="🧾 BUILD", value=_service_value(server_version), inline=True)
    embed.add_field(
        name="🌀 CORRUPTION",
        value=_service_value(_count_label(overview, "corruption")),
        inline=True,
    )
    embed.set_footer(text="Solane AI - Persistent Discord intel from Solane Run.")
    return embed


def _base_embed(title: str, description: str, color: int) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(UTC),
    )
    return embed


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
    for item in items[:10]:
        system = item.get("system") or {}
        name = system.get("name", "Unknown")
        kills = item.get("shipKillsLastHour")
        kills_text = kills if kills is not None else "?"
        lines.append(f"**{name}**\n{kills_text} kills/h - monitored")
    return "\n".join(lines)


def _restricted_system_lines(items: list[dict[str, Any]], empty: str) -> str:
    if not items:
        return empty
    static = [item for item in items if item.get("source") == "static"]
    dynamic = [item for item in items if item.get("source") != "static"]
    lines: list[str] = []
    if dynamic:
        lines.append("**⏳ Temporary closures**")
        lines.extend(_restricted_item_label(item) for item in dynamic[:8])
    if static:
        if lines:
            lines.append("")
        static_items = (
            _restricted_item_label(item, include_kills=False)
            for item in static[:12]
        )
        lines.append("**🧱 Static watchlist**")
        lines.append(", ".join(static_items))
    return "\n".join(lines)


def _restricted_item_label(item: dict[str, Any], include_kills: bool = True) -> str:
    service = _short_service(item.get("serviceType"))
    suffix = f" ({service})" if service else ""
    kills = item.get("shipKillsLastHour")
    if include_kills and kills is not None:
        suffix = f"{suffix} {kills}/h"
    return f"**{item.get('name', 'Unknown')}**{suffix}"


def _recently_open_lines(items: list[dict[str, Any]], empty: str) -> str:
    if not items:
        return empty
    lines = []
    for item in items[:8]:
        service = _short_service(item.get("serviceType"))
        service_suffix = f" - {service}" if service else ""
        lines.append(f"**{item.get('name', 'Unknown')}**{service_suffix}\nReopened")
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
        lines.append(f"**{name}**\n{service_prefix}LVL{level} - {corruption}% / {suppression}%")
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
