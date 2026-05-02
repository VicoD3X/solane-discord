from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import discord

PANEL_PIPES_CONTROL = 0x1A1953
FOOTER_TEXT = "Data from Solane API - Proprietary license"

EMOJI_RED = "\U0001F534"
EMOJI_YELLOW = "\U0001F7E1"
EMOJI_GREEN = "\U0001F7E2"
EMOJI_SOURCE = "\U0001F50E"


def build_pipes_control_embed(snapshot: dict[str, Any]) -> discord.Embed:
    pipes = _pipes(snapshot)

    embed = discord.Embed(
        title="SOLANE RISK / PIPES CONTROL",
        description="HighSec pipe control board from Solane Engine.",
        color=PANEL_PIPES_CONTROL,
        timestamp=datetime.now(UTC),
    )
    embed.add_field(
        name=f"{EMOJI_RED} CRITICAL",
        value=_pipe_table(_group(pipes, "critical"), empty="No Critical pipe."),
        inline=False,
    )
    embed.add_field(
        name=f"{EMOJI_YELLOW} WATCHED",
        value=_pipe_table(_group(pipes, "watched"), empty="No Watched pipe."),
        inline=False,
    )
    embed.add_field(
        name=f"{EMOJI_GREEN} STABLE",
        value=_pipe_table(_stable_group(pipes), empty="No Stable pipe."),
        inline=False,
    )
    _append_source_field(embed, snapshot)
    embed.set_footer(text=FOOTER_TEXT)
    return embed


def _pipes(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    summary = snapshot.get("botSummary")
    if not isinstance(summary, dict):
        return []
    route_risk = summary.get("routeRisk")
    if not isinstance(route_risk, dict):
        return []
    pipes = route_risk.get("pipesControlSystems")
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


def _pipe_table(pipes: list[dict[str, Any]], empty: str) -> str:
    if not pipes:
        return empty
    lines = [f"{'PIPE':<10} {'STAT':<5} {'KILLS/H':>7}  HOT GATE"]
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
