from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import discord
from discord import app_commands

from .solane_api import SolaneApi

ROAD_COLOR = 0x4B9DFF
SEARCH_TIMEOUT_SECONDS = 180


@dataclass
class RoadSystemChoice:
    id: int
    name: str
    security_display: str | None = None
    service_type: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> RoadSystemChoice:
        return cls(
            id=int(payload["id"]),
            name=str(payload.get("name") or payload["id"]),
            security_display=payload.get("securityDisplay"),
            service_type=payload.get("serviceType"),
        )

    @property
    def label(self) -> str:
        suffix = f" {self.service_type}" if self.service_type else ""
        return f"{self.name}{suffix}"


@dataclass
class RoadSession:
    pickup: RoadSystemChoice | None = None
    destination: RoadSystemChoice | None = None


def create_road_command(api: SolaneApi) -> app_commands.Command:
    async def callback(interaction: discord.Interaction) -> None:
        session = RoadSession()
        embed = _step_embed(session, "pickup")
        await interaction.response.send_message(
            embed=embed,
            view=RoadSearchView(api, session, "pickup"),
            ephemeral=True,
        )

    return app_commands.Command(
        name="create-road",
        description="Create a private Solane Road route intel scan.",
        callback=callback,
    )


class RoadSearchView(discord.ui.View):
    def __init__(self, api: SolaneApi, session: RoadSession, step: str) -> None:
        super().__init__(timeout=SEARCH_TIMEOUT_SECONDS)
        self.api = api
        self.session = session
        self.step = step
        button = discord.ui.Button(
            label=f"Search {_step_label(step)}",
            style=discord.ButtonStyle.primary,
        )
        button.callback = self._open_modal
        self.add_item(button)

    async def _open_modal(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(SystemSearchModal(self.api, self.session, self.step))


class SystemSearchModal(discord.ui.Modal):
    def __init__(self, api: SolaneApi, session: RoadSession, step: str) -> None:
        super().__init__(title=f"Solane Road / {_step_label(step)}")
        self.api = api
        self.session = session
        self.step = step
        self.query = discord.ui.TextInput(
            label="System name",
            placeholder="Jita, Amarr, Tama...",
            min_length=2,
            max_length=80,
        )
        self.add_item(self.query)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        query = str(self.query.value).strip()
        try:
            systems = await self.api.search_systems(query)
        except Exception as exc:  # noqa: BLE001 - keep the guided flow alive.
            await interaction.followup.send(
                embed=_error_embed(f"System search failed: {exc}"),
                ephemeral=True,
            )
            return

        if not systems:
            await interaction.followup.send(
                embed=_step_embed(self.session, self.step, f"No system found for `{query}`."),
                view=RoadSearchView(self.api, self.session, self.step),
                ephemeral=True,
            )
            return

        if len(systems) == 1:
            await _apply_choice(
                interaction,
                self.api,
                self.session,
                self.step,
                RoadSystemChoice.from_payload(systems[0]),
            )
            return

        await interaction.followup.send(
            embed=_select_embed(self.session, self.step, query),
            view=SystemSelectView(self.api, self.session, self.step, systems),
            ephemeral=True,
        )


class SystemSelectView(discord.ui.View):
    def __init__(
        self,
        api: SolaneApi,
        session: RoadSession,
        step: str,
        systems: list[dict[str, Any]],
    ) -> None:
        super().__init__(timeout=SEARCH_TIMEOUT_SECONDS)
        self.api = api
        self.session = session
        self.step = step
        self.systems = {
            str(system["id"]): RoadSystemChoice.from_payload(system)
            for system in systems[:25]
            if "id" in system
        }
        select = discord.ui.Select(
            placeholder=f"Select {_step_label(step)}",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=_clip(choice.name, 100),
                    value=str(choice.id),
                    description=_clip(_system_description(choice), 100),
                )
                for choice in self.systems.values()
            ],
        )
        select.callback = self._select_system
        self.add_item(select)

    async def _select_system(self, interaction: discord.Interaction) -> None:
        select = self.children[0]
        if not isinstance(select, discord.ui.Select) or not select.values:
            await interaction.response.send_message(embed=_error_embed("No system selected."), ephemeral=True)
            return
        choice = self.systems.get(select.values[0])
        if choice is None:
            await interaction.response.send_message(
                embed=_error_embed("Selected system expired."),
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        await _apply_choice(interaction, self.api, self.session, self.step, choice)


class RoadResultView(discord.ui.View):
    def __init__(self, api: SolaneApi, origin_id: int, destination_id: int, flag: str | None) -> None:
        super().__init__(timeout=SEARCH_TIMEOUT_SECONDS)
        self.api = api
        self.origin_id = origin_id
        self.destination_id = destination_id
        self.flag = flag

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.secondary)
    async def refresh(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            payload = await self.api.road_overview(self.origin_id, self.destination_id, self.flag)
        except Exception as exc:  # noqa: BLE001 - report route refresh failures in Discord.
            await interaction.followup.send(embed=_error_embed(f"Refresh failed: {exc}"), ephemeral=True)
            return
        await interaction.followup.send(
            embed=build_road_embed(payload),
            view=RoadResultView(self.api, self.origin_id, self.destination_id, payload.get("flag")),
            ephemeral=True,
        )


async def _apply_choice(
    interaction: discord.Interaction,
    api: SolaneApi,
    session: RoadSession,
    step: str,
    choice: RoadSystemChoice,
) -> None:
    if step == "pickup":
        session.pickup = choice
        await interaction.followup.send(
            embed=_step_embed(session, "destination"),
            view=RoadSearchView(api, session, "destination"),
            ephemeral=True,
        )
        return

    session.destination = choice
    if session.pickup is None:
        await interaction.followup.send(
            embed=_step_embed(session, "pickup", "Pick up expired. Start again from pick up."),
            view=RoadSearchView(api, session, "pickup"),
            ephemeral=True,
        )
        return

    try:
        payload = await api.road_overview(session.pickup.id, session.destination.id)
    except Exception as exc:  # noqa: BLE001 - keep the Discord interaction explicit.
        await interaction.followup.send(embed=_error_embed(f"Route intel failed: {exc}"), ephemeral=True)
        return

    await interaction.followup.send(
        embed=build_road_embed(payload),
        view=RoadResultView(api, session.pickup.id, session.destination.id, payload.get("flag")),
        ephemeral=True,
    )


def build_road_embed(payload: dict[str, Any]) -> discord.Embed:
    origin = _system_name(payload.get("origin"))
    destination = _system_name(payload.get("destination"))
    embed = discord.Embed(
        title="SOLANE ROAD / ROUTE INTEL",
        description=f"{origin} -> {destination}",
        color=ROAD_COLOR,
    )
    embed.add_field(
        name="ROUTE",
        value=(
            f"Jumps: `{payload.get('jumps', 'n/a')}`\n"
            f"Flag: `{str(payload.get('flag') or 'auto').upper()}`"
        ),
        inline=True,
    )
    embed.add_field(
        name="TRAFFIC FLOW",
        value=_traffic_value(payload.get("routeTraffic")),
        inline=True,
    )
    embed.add_field(
        name="CRITICAL SYSTEMS",
        value=_critical_systems_value(payload.get("criticalSystems")),
        inline=False,
    )
    embed.add_field(
        name="FRESHNESS",
        value=_freshness_value(payload),
        inline=False,
    )
    generated = _time_label(payload.get("generatedAt"))
    embed.set_footer(text=f"Data from Solane Engine - generated {generated}")
    return embed


def _step_embed(session: RoadSession, step: str, note: str | None = None) -> discord.Embed:
    embed = discord.Embed(
        title=f"SOLANE ROAD / {_step_label(step).upper()}",
        description=note or f"Select the {_step_label(step).lower()} system.",
        color=ROAD_COLOR,
    )
    embed.add_field(name="PICK UP", value=session.pickup.label if session.pickup else "Pending", inline=True)
    embed.add_field(
        name="DESTINATION",
        value=session.destination.label if session.destination else "Pending",
        inline=True,
    )
    return embed


def _select_embed(session: RoadSession, step: str, query: str) -> discord.Embed:
    embed = _step_embed(session, step, f"Multiple systems found for `{query}`.")
    embed.add_field(
        name="ACTION",
        value=f"Choose the correct {_step_label(step).lower()} below.",
        inline=False,
    )
    return embed


def _error_embed(message: str) -> discord.Embed:
    return discord.Embed(title="SOLANE ROAD / ERROR", description=message, color=0xD7263D)


def _traffic_value(traffic: Any) -> str:
    if not isinstance(traffic, dict):
        return "`Unavailable`"
    jumps = _count_value(traffic.get("totalShipJumpsLastHour"))
    coverage = traffic.get("coverage")
    coverage_label = f"{float(coverage) * 100:.0f}%" if isinstance(coverage, int | float) else "n/a"
    return (
        f"Status: `{traffic.get('label', 'Unavailable')}`\n"
        f"Jumps/h: `{jumps}`\n"
        f"Coverage: `{coverage_label}`"
    )


def _critical_systems_value(items: Any) -> str:
    if not isinstance(items, list) or not items:
        return "No Critical system on route."
    lines = []
    for item in items[:8]:
        if not isinstance(item, dict):
            continue
        system = item.get("system") if isinstance(item.get("system"), dict) else {}
        gate = item.get("hotGate") if isinstance(item.get("hotGate"), dict) else None
        hot_gate = _hot_gate_label(gate)
        service = system.get("serviceType")
        service_suffix = f" {service}" if service else ""
        lines.append(
            f"**{system.get('name', 'Unknown')}**{service_suffix} "
            f"`{_count_value(item.get('shipKillsLastHour'))} kills/h` | `{hot_gate}`"
        )
    return "\n".join(lines) if lines else "No Critical system on route."


def _freshness_value(payload: dict[str, Any]) -> str:
    critical = [item for item in payload.get("criticalSystems") or [] if isinstance(item, dict)]
    esi_statuses = [str(item.get("esiStatus") or "unavailable") for item in critical]
    zkill_statuses = [str(item.get("zkillStatus") or "unavailable") for item in critical]
    esi_status = _combined_status(esi_statuses)
    zkill_status = _combined_status(zkill_statuses)
    esi_time = _latest_time(item.get("lastSyncedAt") for item in critical)
    zkill_time = _latest_time(item.get("zkillFetchedAt") for item in critical)
    warning = ""
    if "delayed" in {esi_status, zkill_status}:
        warning = "\nPotential delayed intel: ESI or zKill cache is older than the fast refresh target."
    if "unavailable" in {esi_status, zkill_status} and critical:
        warning = "\nPartial intel: one source is unavailable."
    return (
        f"ESI kills: `{esi_status.title()}` | `{esi_time}`\n"
        f"zKill gates: `{zkill_status.title()}` | `{zkill_time}`"
        f"{warning}"
    )


def _hot_gate_label(gate: dict[str, Any] | None) -> str:
    if not gate or int(gate.get("killsLastHour") or 0) < 1:
        return "Clear"
    name = gate.get("destinationSystemName") or gate.get("name") or "Unknown gate"
    return f"{name} ({int(gate.get('killsLastHour') or 0)})"


def _combined_status(statuses: list[str]) -> str:
    if not statuses:
        return "fresh"
    if "unavailable" in statuses:
        return "unavailable"
    if "delayed" in statuses:
        return "delayed"
    return "fresh"


def _latest_time(values: Any) -> str:
    clean = sorted(str(value) for value in values if value)
    return _time_label(clean[-1]) if clean else "n/a"


def _time_label(value: Any) -> str:
    if not value:
        return "n/a"
    text = str(value)
    if "T" not in text:
        return text
    return text.split("T", 1)[1][:5] + " EVE"


def _count_value(value: Any) -> str:
    return str(value) if isinstance(value, int) else "n/a"


def _system_name(payload: Any) -> str:
    return str(payload.get("name") or "Unknown") if isinstance(payload, dict) else "Unknown"


def _step_label(step: str) -> str:
    return "Destination" if step == "destination" else "Pick up"


def _system_description(choice: RoadSystemChoice) -> str:
    parts = [part for part in (choice.service_type, choice.security_display) if part]
    return " | ".join(parts) if parts else "EVE system"


def _clip(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "."
