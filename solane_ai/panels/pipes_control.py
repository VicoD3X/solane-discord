from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import discord

PANEL_HIGHSEC_CONTROL = 0x79AE6F
PANEL_HIGHSEC_GLOBAL_CONTROL = 0x2FA084
PANEL_POCHVEN_CONTROL = 0xAE2448
PANEL_LOWSEC_CONTROL = 0xFF653F
PANEL_NSNPC_CONTROL = 0x8100D1
FOOTER_TEXT = "Data from Solane API - Proprietary license"

EMOJI_RED = "\U0001F534"
EMOJI_ORANGE = "\U0001F7E0"
EMOJI_YELLOW = "\U0001F7E1"
EMOJI_GREEN = "\U0001F7E2"
EMOJI_SOURCE = "\U0001F50E"

CONTROL_GROUPS = (
    (f"{EMOJI_RED} CRITICAL", "critical", "No Critical pipe."),
    (f"{EMOJI_YELLOW} WATCHED", "watched", "No Watched pipe."),
    (f"{EMOJI_GREEN} STABLE", "stable", "No Stable pipe."),
)

HIGHSEC_GLOBAL_GROUPS = (
    (f"{EMOJI_RED} CRITICAL", "critical", "No Critical HighSec system."),
    (f"{EMOJI_YELLOW} WATCHED", "watched", "No Watched HighSec system."),
    (f"{EMOJI_GREEN} STABLE", "stable", "No Stable HighSec signal listed."),
)

LOWSEC_GROUPS = (
    (f"{EMOJI_RED} CRITICAL", "critical", "No Critical Low-Sec system."),
    (f"{EMOJI_ORANGE} FLASHPOINT", "flashpoint", "No Flashpoint Low-Sec system."),
    (f"{EMOJI_YELLOW} WATCHED", "watched", "No Watched Low-Sec system."),
)

NSNPC_GROUPS = (
    (f"{EMOJI_RED} CRITICAL", "critical", "No Critical NS NPC system."),
    (f"{EMOJI_ORANGE} FLASHPOINT", "flashpoint", "No Flashpoint NS NPC system."),
    (f"{EMOJI_YELLOW} WATCHED", "watched", "No Watched NS NPC system."),
)


def build_pipes_control_embed(snapshot: dict[str, Any]) -> discord.Embed:
    return _build_control_embed(
        snapshot,
        title="SOLANE RISK / PIPES CONTROL",
        description="HighSec pipe control board from Solane Engine.",
        feed_key="pipesControlSystems",
        color=PANEL_HIGHSEC_CONTROL,
        groups=CONTROL_GROUPS,
        first_column="PIPE",
    )


def build_highsec_control_embed(snapshot: dict[str, Any]) -> discord.Embed:
    return _build_control_embed(
        snapshot,
        title="SOLANE RISK / HIGHSEC CONTROL",
        description="Global active HighSec control board from Solane Engine.",
        feed_key="highSecControlSystems",
        color=PANEL_HIGHSEC_GLOBAL_CONTROL,
        groups=HIGHSEC_GLOBAL_GROUPS,
        first_column="SYSTEM",
    )


def build_pochven_control_embed(snapshot: dict[str, Any]) -> discord.Embed:
    return _build_control_embed(
        snapshot,
        title="SOLANE RISK / POCHVEN CONTROL",
        description="Pochven control board from Solane Engine.",
        feed_key="pochvenControlSystems",
        color=PANEL_POCHVEN_CONTROL,
        groups=CONTROL_GROUPS,
        first_column="PIPE",
    )


def build_lowsec_control_embed(snapshot: dict[str, Any]) -> discord.Embed:
    return _build_control_embed(
        snapshot,
        title="SOLANE RISK / LOW-SEC CONTROL",
        description="Low-Sec control board from Solane Engine.",
        feed_key="lowSecControlSystems",
        color=PANEL_LOWSEC_CONTROL,
        groups=LOWSEC_GROUPS,
        first_column="SYSTEM",
    )


def build_nsnpc_control_embed(snapshot: dict[str, Any]) -> discord.Embed:
    return _build_control_embed(
        snapshot,
        title="SOLANE RISK / NS NPC CONTROL",
        description="NS NPC control board from Solane Engine.",
        feed_key="npcNullSecControlSystems",
        color=PANEL_NSNPC_CONTROL,
        groups=NSNPC_GROUPS,
        first_column="SYSTEM",
    )


def _build_control_embed(
    snapshot: dict[str, Any],
    *,
    title: str,
    description: str,
    feed_key: str,
    color: int,
    groups: tuple[tuple[str, str, str], ...],
    first_column: str,
) -> discord.Embed:
    pipes = _control_items(snapshot, feed_key)

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(UTC),
    )
    for name, level, empty in groups:
        grouped = _stable_group(pipes) if level == "stable" else _group(pipes, level)
        embed.add_field(
            name=name,
            value=_pipe_table(grouped, empty=empty, first_column=first_column),
            inline=False,
        )
    _append_source_field(embed, snapshot)
    embed.set_footer(text=FOOTER_TEXT)
    return embed


def _control_items(snapshot: dict[str, Any], feed_key: str) -> list[dict[str, Any]]:
    summary = snapshot.get("botSummary")
    if not isinstance(summary, dict):
        return []
    route_risk = summary.get("routeRisk")
    if not isinstance(route_risk, dict):
        return []
    pipes = route_risk.get(feed_key)
    return [item for item in pipes if isinstance(item, dict)] if isinstance(pipes, list) else []


def _group(pipes: list[dict[str, Any]], level: str) -> list[dict[str, Any]]:
    return _ordered([pipe for pipe in pipes if _level(pipe) == level])


def _stable_group(pipes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _ordered([pipe for pipe in pipes if _level(pipe) not in {"critical", "watched"}])


def _ordered(pipes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        pipes,
        key=lambda pipe: (
            -(int(pipe.get("shipKillsLastHour") or 0)),
            str(pipe.get("name") or "Unknown"),
        ),
    )


def _pipe_table(pipes: list[dict[str, Any]], empty: str, first_column: str) -> str:
    if not pipes:
        return empty
    lines = [f"{first_column:<10} {'STAT':<5} {'KILLS/H':>7}  HOT GATE"]
    for pipe in pipes:
        lines.append(
            f"{_clip(str(pipe.get('name') or 'Unknown'), 10):<10} "
            f"{_stat(pipe):<5} "
            f"{_kills(pipe.get('shipKillsLastHour')):>7}  "
            f"{_clip(_hot_gate(pipe.get('topGate')), 18)}"
        )
    return "```text\n" + "\n".join(lines) + "\n```"


def _level(pipe: dict[str, Any]) -> str:
    return str(pipe.get("level") or "").casefold()


def _stat(pipe: dict[str, Any]) -> str:
    return {
        "critical": "CRIT",
        "flashpoint": "FLASH",
        "hot": "HOT",
        "watched": "WATCH",
        "safe": "SAFE",
        "unavailable": "UNAV",
    }.get(_level(pipe), "UNAV")


def _kills(value: Any) -> str:
    if value is None:
        return "?"
    return str(value)


def _hot_gate(value: Any) -> str:
    if not isinstance(value, dict):
        return "Clear"
    kills = int(value.get("killsLastHour") or 0)
    if kills <= 0:
        return "Clear"
    name = value.get("destinationSystemName") or value.get("name") or "Unknown"
    return f"{name} ({kills})"


def _append_source_field(embed: discord.Embed, snapshot: dict[str, Any]) -> None:
    update_time = _format_utc_time(_api_updated_at(snapshot))
    embed.add_field(name=f"{EMOJI_SOURCE} SOURCE", value=f"Last API update: `{update_time}`", inline=False)


def _api_updated_at(snapshot: dict[str, Any]) -> Any:
    summary = snapshot.get("botSummary")
    if isinstance(summary, dict):
        return summary.get("generatedAt")
    return snapshot.get("generatedAt")


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


def _clip(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    if width <= 1:
        return value[:width]
    return value[: width - 1] + "."
