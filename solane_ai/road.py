from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import discord
from discord import app_commands

from .solane_api import SolaneApi
from .state import BotState, RecentRoadRecord

ROAD_COLOR = 0x4B9DFF
FOCUS_COLOR = 0x7E5BEF
WATCH_COLOR = 0x1A1953
SEARCH_TIMEOUT_SECONDS = 180
WATCH_REFRESH_SECONDS = 300
WATCH_MAX_MINUTES = 240


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
    mode: str = "road"
    pickup: RoadSystemChoice | None = None
    destination: RoadSystemChoice | None = None
    watch_minutes: int = 60


def create_road_command(api: SolaneApi, state: BotState, state_path: Path) -> app_commands.Command:
    async def callback(interaction: discord.Interaction) -> None:
        session = RoadSession(mode="road")
        await interaction.response.send_message(
            embed=_step_embed(session, "pickup"),
            view=RoadSearchView(api, state, state_path, session, "pickup"),
            ephemeral=True,
        )

    return app_commands.Command(
        name="create-road",
        description="Create a private Solane Road route intel scan.",
        callback=callback,
    )


def create_road_refresh_command(api: SolaneApi, state: BotState, state_path: Path) -> app_commands.Command:
    async def callback(interaction: discord.Interaction) -> None:
        routes = state.routes_for_user(interaction.user.id)
        if not routes:
            await interaction.response.send_message(
                embed=_error_embed("No recent route found. Use /create-road first."),
                ephemeral=True,
            )
            return
        if len(routes) == 1:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await _send_refreshed_route(interaction, api, state, state_path, routes[0])
            return
        await interaction.response.send_message(
            embed=discord.Embed(
                title="SOLANE ROAD / REFRESH",
                description="Select the route to refresh.",
                color=ROAD_COLOR,
            ),
            view=RecentRouteSelectView(api, state, state_path, routes),
            ephemeral=True,
        )

    return app_commands.Command(
        name="road-refresh",
        description="Refresh one of your recent Solane Road routes.",
        callback=callback,
    )


def create_road_compare_command(api: SolaneApi, state: BotState, state_path: Path) -> app_commands.Command:
    async def callback(interaction: discord.Interaction) -> None:
        session = RoadSession(mode="compare")
        await interaction.response.send_message(
            embed=_step_embed(session, "pickup"),
            view=RoadSearchView(api, state, state_path, session, "pickup"),
            ephemeral=True,
        )

    return app_commands.Command(
        name="road-compare",
        description="Compare secure, shortest and insecure Solane Road options.",
        callback=callback,
    )


def create_road_watch_command(api: SolaneApi, state: BotState, state_path: Path) -> app_commands.Command:
    async def callback(interaction: discord.Interaction, minutes: int = 60) -> None:
        watch_minutes = min(max(int(minutes), 5), WATCH_MAX_MINUTES)
        session = RoadSession(mode="watch", watch_minutes=watch_minutes)
        await interaction.response.send_message(
            embed=_step_embed(session, "pickup", f"Select the route to watch for {watch_minutes} min."),
            view=RoadSearchView(api, state, state_path, session, "pickup"),
            ephemeral=True,
        )

    return app_commands.Command(
        name="road-watch",
        description="Watch a Solane Road route in the current channel.",
        callback=callback,
    )


def create_focus_system_command(api: SolaneApi) -> app_commands.Command:
    async def callback(interaction: discord.Interaction, system: str) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        await _focus_from_query(interaction, api, system)

    return app_commands.Command(
        name="focus-system",
        description="Run a fast Solane Focus scan on one system.",
        callback=callback,
    )


def create_road_avoid_group(api: SolaneApi) -> app_commands.Group:
    group = app_commands.Group(name="road-avoid", description="Manage global Solane Road avoids.")

    @group.command(name="list", description="List global Solane Road avoids.")
    async def list_avoids(interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            payload = await api.road_avoids()
        except Exception as exc:  # noqa: BLE001 - Discord should receive explicit API failures.
            await interaction.followup.send(embed=_error_embed(f"Avoid list failed: {exc}"), ephemeral=True)
            return
        await interaction.followup.send(embed=build_avoids_embed(payload), ephemeral=True)

    @group.command(name="add", description="Add a global Solane Road avoid.")
    async def add_avoid(interaction: discord.Interaction, system: str) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        await _avoid_from_query(interaction, api, system, "add")

    @group.command(name="remove", description="Remove a global Solane Road avoid.")
    async def remove_avoid(interaction: discord.Interaction, system: str) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        await _avoid_from_query(interaction, api, system, "remove")

    return group


class RoadSearchView(discord.ui.View):
    def __init__(
        self,
        api: SolaneApi,
        state: BotState,
        state_path: Path,
        session: RoadSession,
        step: str,
    ) -> None:
        super().__init__(timeout=SEARCH_TIMEOUT_SECONDS)
        self.api = api
        self.state = state
        self.state_path = state_path
        self.session = session
        self.step = step
        button = discord.ui.Button(label=f"Search {_step_label(step)}", style=discord.ButtonStyle.primary)
        button.callback = self._open_modal
        self.add_item(button)

    async def _open_modal(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            SystemSearchModal(self.api, self.state, self.state_path, self.session, self.step)
        )


class SystemSearchModal(discord.ui.Modal):
    def __init__(
        self,
        api: SolaneApi,
        state: BotState,
        state_path: Path,
        session: RoadSession,
        step: str,
    ) -> None:
        super().__init__(title=f"Solane Road / {_step_label(step)}")
        self.api = api
        self.state = state
        self.state_path = state_path
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
                embed=_error_embed(f"System search failed: {exc}"), ephemeral=True
            )
            return
        if not systems:
            await interaction.followup.send(
                embed=_step_embed(self.session, self.step, f"No system found for `{query}`."),
                view=RoadSearchView(self.api, self.state, self.state_path, self.session, self.step),
                ephemeral=True,
            )
            return
        if len(systems) == 1:
            await _apply_choice(
                interaction,
                self.api,
                self.state,
                self.state_path,
                self.session,
                self.step,
                RoadSystemChoice.from_payload(systems[0]),
            )
            return
        await interaction.followup.send(
            embed=_select_embed(self.session, self.step, query),
            view=SystemSelectView(self.api, self.state, self.state_path, self.session, self.step, systems),
            ephemeral=True,
        )


class SystemSelectView(discord.ui.View):
    def __init__(
        self,
        api: SolaneApi,
        state: BotState,
        state_path: Path,
        session: RoadSession,
        step: str,
        systems: list[dict[str, Any]],
    ) -> None:
        super().__init__(timeout=SEARCH_TIMEOUT_SECONDS)
        self.api = api
        self.state = state
        self.state_path = state_path
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
                embed=_error_embed("Selected system expired."), ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        await _apply_choice(
            interaction, self.api, self.state, self.state_path, self.session, self.step, choice
        )


class RoadResultView(discord.ui.View):
    def __init__(
        self,
        api: SolaneApi,
        state: BotState,
        state_path: Path,
        origin_id: int,
        destination_id: int,
        flag: str | None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(timeout=SEARCH_TIMEOUT_SECONDS)
        self.api = api
        self.state = state
        self.state_path = state_path
        self.origin_id = origin_id
        self.destination_id = destination_id
        self.flag = flag
        critical = [item for item in (payload or {}).get("criticalSystems") or [] if isinstance(item, dict)]
        if critical:
            self.add_item(FocusCriticalSelect(api, critical))

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.secondary)
    async def refresh(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            payload = await self.api.road_overview(self.origin_id, self.destination_id, self.flag)
        except Exception as exc:  # noqa: BLE001 - report route refresh failures in Discord.
            await interaction.followup.send(embed=_error_embed(f"Refresh failed: {exc}"), ephemeral=True)
            return
        _remember_route(self.state, self.state_path, interaction.user.id, payload)
        await interaction.followup.send(
            embed=build_road_embed(payload),
            view=RoadResultView(
                self.api,
                self.state,
                self.state_path,
                self.origin_id,
                self.destination_id,
                payload.get("flag"),
                payload,
            ),
            ephemeral=True,
        )


class FocusCriticalSelect(discord.ui.Select):
    def __init__(self, api: SolaneApi, critical_systems: list[dict[str, Any]]) -> None:
        self.api = api
        options = []
        self.system_ids: dict[str, int] = {}
        for item in critical_systems[:25]:
            system = item.get("system") if isinstance(item.get("system"), dict) else {}
            system_id = system.get("id")
            if system_id is None:
                continue
            value = str(system_id)
            gate_label = _hot_gate_label(item.get("hotGate"))
            self.system_ids[value] = int(system_id)
            options.append(
                discord.SelectOption(
                    label=_clip(str(system.get("name") or system_id), 100),
                    value=value,
                    description=_clip(f"{item.get('shipKillsLastHour', 'n/a')} kills/h | {gate_label}", 100),
                )
            )
        super().__init__(placeholder="Focus Critical system", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        system_id = self.system_ids.get(self.values[0])
        if system_id is None:
            await interaction.followup.send(embed=_error_embed("Focus target expired."), ephemeral=True)
            return
        try:
            payload = await self.api.focus_system(system_id)
        except Exception as exc:  # noqa: BLE001
            await interaction.followup.send(embed=_error_embed(f"Focus failed: {exc}"), ephemeral=True)
            return
        await interaction.followup.send(embed=build_focus_embed(payload), ephemeral=True)


class RecentRouteSelectView(discord.ui.View):
    def __init__(
        self, api: SolaneApi, state: BotState, state_path: Path, routes: list[RecentRoadRecord]
    ) -> None:
        super().__init__(timeout=SEARCH_TIMEOUT_SECONDS)
        self.api = api
        self.state = state
        self.state_path = state_path
        self.routes = {str(index): route for index, route in enumerate(routes[:5])}
        select = discord.ui.Select(
            placeholder="Select route",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=_clip(f"{route.origin_name} -> {route.destination_name}", 100),
                    value=str(index),
                    description=_clip(
                        f"Flag {(route.flag or 'auto').upper()} | {_time_label(route.updated_at)}", 100
                    ),
                )
                for index, route in enumerate(routes[:5])
            ],
        )
        select.callback = self._select_route
        self.add_item(select)

    async def _select_route(self, interaction: discord.Interaction) -> None:
        select = self.children[0]
        if not isinstance(select, discord.ui.Select) or not select.values:
            await interaction.response.send_message(embed=_error_embed("No route selected."), ephemeral=True)
            return
        route = self.routes.get(select.values[0])
        if route is None:
            await interaction.response.send_message(
                embed=_error_embed("Selected route expired."), ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        await _send_refreshed_route(interaction, self.api, self.state, self.state_path, route)


class AvoidSystemSelectView(discord.ui.View):
    def __init__(self, api: SolaneApi, systems: list[dict[str, Any]], action: str) -> None:
        super().__init__(timeout=SEARCH_TIMEOUT_SECONDS)
        self.api = api
        self.action = action
        self.systems = {
            str(system["id"]): RoadSystemChoice.from_payload(system)
            for system in systems[:25]
            if "id" in system
        }
        select = discord.ui.Select(
            placeholder=f"Select system to {action}",
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
        await interaction.response.defer(ephemeral=True, thinking=True)
        choice = self.systems.get(select.values[0])
        if choice is None:
            await interaction.followup.send(embed=_error_embed("Selected system expired."), ephemeral=True)
            return
        await _apply_avoid_action(interaction, self.api, choice.id, self.action)


async def _apply_choice(
    interaction: discord.Interaction,
    api: SolaneApi,
    state: BotState,
    state_path: Path,
    session: RoadSession,
    step: str,
    choice: RoadSystemChoice,
) -> None:
    if step == "pickup":
        session.pickup = choice
        await interaction.followup.send(
            embed=_step_embed(session, "destination"),
            view=RoadSearchView(api, state, state_path, session, "destination"),
            ephemeral=True,
        )
        return

    session.destination = choice
    if session.pickup is None:
        await interaction.followup.send(
            embed=_step_embed(session, "pickup", "Pick up expired. Start again from pick up."),
            view=RoadSearchView(api, state, state_path, session, "pickup"),
            ephemeral=True,
        )
        return

    if session.mode == "compare":
        try:
            payload = await api.road_compare(session.pickup.id, session.destination.id)
        except Exception as exc:  # noqa: BLE001
            await interaction.followup.send(
                embed=_error_embed(f"Route compare failed: {exc}"), ephemeral=True
            )
            return
        await interaction.followup.send(embed=build_compare_embed(payload), ephemeral=True)
        return

    if session.mode == "watch":
        await _start_route_watch(interaction, api, session)
        return

    try:
        payload = await api.road_overview(session.pickup.id, session.destination.id)
    except Exception as exc:  # noqa: BLE001
        await interaction.followup.send(embed=_error_embed(f"Route intel failed: {exc}"), ephemeral=True)
        return

    _remember_route(state, state_path, interaction.user.id, payload)
    await interaction.followup.send(
        embed=build_road_embed(payload),
        view=RoadResultView(
            api, state, state_path, session.pickup.id, session.destination.id, payload.get("flag"), payload
        ),
        ephemeral=True,
    )


async def _send_refreshed_route(
    interaction: discord.Interaction,
    api: SolaneApi,
    state: BotState,
    state_path: Path,
    route: RecentRoadRecord,
) -> None:
    try:
        payload = await api.road_overview(route.origin_id, route.destination_id, route.flag)
    except Exception as exc:  # noqa: BLE001
        await interaction.followup.send(embed=_error_embed(f"Refresh failed: {exc}"), ephemeral=True)
        return
    _remember_route(state, state_path, interaction.user.id, payload)
    await interaction.followup.send(
        embed=build_road_embed(payload),
        view=RoadResultView(
            api, state, state_path, route.origin_id, route.destination_id, payload.get("flag"), payload
        ),
        ephemeral=True,
    )


async def _start_route_watch(interaction: discord.Interaction, api: SolaneApi, session: RoadSession) -> None:
    if session.pickup is None or session.destination is None:
        await interaction.followup.send(embed=_error_embed("Watch route expired."), ephemeral=True)
        return
    if interaction.channel is None or not isinstance(interaction.channel, discord.abc.Messageable):
        await interaction.followup.send(
            embed=_error_embed("Current channel is not messageable."), ephemeral=True
        )
        return
    try:
        payload = await api.road_overview(session.pickup.id, session.destination.id)
    except Exception as exc:  # noqa: BLE001
        await interaction.followup.send(embed=_error_embed(f"Route watch failed: {exc}"), ephemeral=True)
        return
    message = await interaction.channel.send(
        embed=build_watch_embed(payload, session.watch_minutes, "Active")
    )
    await interaction.followup.send(
        embed=discord.Embed(
            title="SOLANE ROAD / WATCH ARMED",
            description=(
                f"Watching {session.pickup.name} -> {session.destination.name} "
                f"for {session.watch_minutes} min."
            ),
            color=WATCH_COLOR,
        ),
        ephemeral=True,
    )
    asyncio.create_task(
        _watch_route(
            api,
            message,
            session.pickup.id,
            session.destination.id,
            payload.get("flag"),
            session.watch_minutes,
            _route_signature(payload),
        ),
        name=f"solane-road-watch-{message.id}",
    )


async def _watch_route(
    api: SolaneApi,
    message: discord.Message,
    origin_id: int,
    destination_id: int,
    flag: str | None,
    minutes: int,
    initial_signature: tuple[Any, ...],
) -> None:
    deadline = datetime.now(UTC) + timedelta(minutes=minutes)
    previous_signature: tuple[Any, ...] = initial_signature
    while datetime.now(UTC) < deadline:
        await asyncio.sleep(
            min(WATCH_REFRESH_SECONDS, max(1, int((deadline - datetime.now(UTC)).total_seconds())))
        )
        try:
            payload = await api.road_overview(origin_id, destination_id, flag)
        except Exception as exc:  # noqa: BLE001
            await message.channel.send(f"Solane Road watch update failed: `{_clip(str(exc), 120)}`")
            continue
        signature = _route_signature(payload)
        await message.edit(embed=build_watch_embed(payload, minutes, "Active"))
        if signature != previous_signature:
            await message.channel.send(embed=_watch_alert_embed(payload))
        previous_signature = signature
    await message.edit(embed=build_watch_embed(payload if "payload" in locals() else {}, minutes, "Ended"))


async def _focus_from_query(interaction: discord.Interaction, api: SolaneApi, query: str) -> None:
    try:
        systems = await api.search_systems(query)
    except Exception as exc:  # noqa: BLE001
        await interaction.followup.send(embed=_error_embed(f"System search failed: {exc}"), ephemeral=True)
        return
    if not systems:
        await interaction.followup.send(embed=_error_embed(f"No system found for `{query}`."), ephemeral=True)
        return
    if len(systems) > 1:
        await interaction.followup.send(
            embed=discord.Embed(
                title="SOLANE FOCUS / SELECT SYSTEM",
                description=f"Multiple systems found for `{query}`.",
                color=FOCUS_COLOR,
            ),
            view=FocusSystemSelectView(api, systems),
            ephemeral=True,
        )
        return
    await _send_focus(interaction, api, int(systems[0]["id"]))


class FocusSystemSelectView(discord.ui.View):
    def __init__(self, api: SolaneApi, systems: list[dict[str, Any]]) -> None:
        super().__init__(timeout=SEARCH_TIMEOUT_SECONDS)
        self.api = api
        self.systems = {
            str(system["id"]): RoadSystemChoice.from_payload(system)
            for system in systems[:25]
            if "id" in system
        }
        select = discord.ui.Select(
            placeholder="Select system",
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
                embed=_error_embed("Selected system expired."), ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        await _send_focus(interaction, self.api, choice.id)


async def _send_focus(interaction: discord.Interaction, api: SolaneApi, system_id: int) -> None:
    try:
        payload = await api.focus_system(system_id)
    except Exception as exc:  # noqa: BLE001
        await interaction.followup.send(embed=_error_embed(f"Focus failed: {exc}"), ephemeral=True)
        return
    await interaction.followup.send(embed=build_focus_embed(payload), ephemeral=True)


async def _avoid_from_query(
    interaction: discord.Interaction, api: SolaneApi, query: str, action: str
) -> None:
    try:
        systems = await api.search_systems(query)
    except Exception as exc:  # noqa: BLE001
        await interaction.followup.send(embed=_error_embed(f"System search failed: {exc}"), ephemeral=True)
        return
    if not systems:
        await interaction.followup.send(embed=_error_embed(f"No system found for `{query}`."), ephemeral=True)
        return
    if len(systems) > 1:
        await interaction.followup.send(
            embed=discord.Embed(
                title=f"SOLANE ROAD / AVOID {action.upper()}",
                description=f"Multiple systems found for `{query}`.",
                color=ROAD_COLOR,
            ),
            view=AvoidSystemSelectView(api, systems, action),
            ephemeral=True,
        )
        return
    await _apply_avoid_action(interaction, api, int(systems[0]["id"]), action)


async def _apply_avoid_action(
    interaction: discord.Interaction, api: SolaneApi, system_id: int, action: str
) -> None:
    try:
        payload = (
            await api.add_road_avoid(system_id) if action == "add" else await api.remove_road_avoid(system_id)
        )
    except Exception as exc:  # noqa: BLE001
        await interaction.followup.send(embed=_error_embed(f"Avoid {action} failed: {exc}"), ephemeral=True)
        return
    await interaction.followup.send(embed=build_avoids_embed(payload), ephemeral=True)


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
        value=f"Jumps: `{payload.get('jumps', 'n/a')}`\nFlag: `{str(payload.get('flag') or 'auto').upper()}`",
        inline=True,
    )
    embed.add_field(name="TRAFFIC FLOW", value=_traffic_value(payload.get("routeTraffic")), inline=True)
    embed.add_field(
        name="CRITICAL SYSTEMS", value=_critical_systems_value(payload.get("criticalSystems")), inline=False
    )
    embed.add_field(name="FRESHNESS", value=_freshness_value(payload), inline=False)
    generated = _time_label(payload.get("generatedAt"))
    embed.set_footer(text=f"Data from Solane Engine - generated {generated}")
    return embed


def build_compare_embed(payload: dict[str, Any]) -> discord.Embed:
    origin = _system_name(payload.get("origin"))
    destination = _system_name(payload.get("destination"))
    embed = discord.Embed(
        title="SOLANE ROAD / ROUTE COMPARE",
        description=f"{origin} -> {destination}",
        color=ROAD_COLOR,
    )
    for option in payload.get("options") or []:
        if not isinstance(option, dict):
            continue
        flag = str(option.get("flag") or "unknown").upper()
        overview = option.get("overview") if isinstance(option.get("overview"), dict) else None
        if overview is None:
            embed.add_field(
                name=flag, value=f"Unavailable: `{option.get('error', 'Route unavailable')}`", inline=False
            )
            continue
        risk = overview.get("routeRisk") if isinstance(overview.get("routeRisk"), dict) else {}
        critical = (
            overview.get("criticalSystems") if isinstance(overview.get("criticalSystems"), list) else []
        )
        embed.add_field(
            name=flag,
            value=(
                f"Jumps: `{overview.get('jumps', 'n/a')}` | Risk: `{risk.get('label', 'Unavailable')}`\n"
                f"Traffic: `{_traffic_label(overview.get('routeTraffic'))}` | Critical: `{len(critical)}`\n"
                f"Hot: `{_compare_hot_gate(critical)}`"
            ),
            inline=False,
        )
    embed.set_footer(text=f"Data from Solane Engine - generated {_time_label(payload.get('generatedAt'))}")
    return embed


def build_focus_embed(payload: dict[str, Any]) -> discord.Embed:
    system = payload.get("system") if isinstance(payload.get("system"), dict) else {}
    embed = discord.Embed(
        title="SOLANE FOCUS / SYSTEM SCAN",
        description=str(system.get("name") or "Unknown"),
        color=FOCUS_COLOR,
    )
    risk = payload.get("routeRisk") if isinstance(payload.get("routeRisk"), dict) else {}
    embed.add_field(
        name="SYSTEM",
        value=(
            f"Service: `{system.get('serviceType', 'n/a')}`\n"
            f"Security: `{system.get('securityDisplay', 'n/a')}`\n"
            f"Jumps/h: `{_count_value(payload.get('shipJumpsLastHour'))}`"
        ),
        inline=True,
    )
    embed.add_field(
        name="RISK",
        value=(
            f"Status: `{risk.get('label', 'Unavailable')}`\n"
            f"Kills/h: `{_count_value(payload.get('shipKillsLastHour'))}`\n"
            f"Source: `{risk.get('riskSource', 'n/a')}`"
        ),
        inline=True,
    )
    embed.add_field(name="HOT GATES", value=_focus_gates_value(payload.get("gates")), inline=False)
    embed.add_field(name="CORRUPTION / FW", value=_focus_corruption_value(payload), inline=True)
    embed.add_field(name="FRESHNESS", value=_focus_freshness_value(payload), inline=True)
    embed.set_footer(text=f"Data from Solane Engine - generated {_time_label(payload.get('generatedAt'))}")
    return embed


def build_avoids_embed(payload: dict[str, Any]) -> discord.Embed:
    embed = discord.Embed(
        title="SOLANE ROAD / AVOIDS",
        description="Global route avoids applied by Solane Engine.",
        color=ROAD_COLOR,
    )
    embed.add_field(name="ACTIVE", value=_avoid_list_value(payload.get("effectiveAvoids")), inline=False)
    embed.add_field(
        name="REMOVED DEFAULTS", value=_avoid_list_value(payload.get("removedDefaultAvoids")), inline=False
    )
    embed.set_footer(text=f"Data from Solane Engine - generated {_time_label(payload.get('generatedAt'))}")
    return embed


def build_watch_embed(payload: dict[str, Any], minutes: int, status: str) -> discord.Embed:
    embed = (
        build_road_embed(payload)
        if payload
        else discord.Embed(title="SOLANE ROAD / ROUTE WATCH", color=WATCH_COLOR)
    )
    embed.title = "SOLANE ROAD / ROUTE WATCH"
    embed.color = WATCH_COLOR
    embed.add_field(name="WATCH", value=f"Status: `{status}`\nWindow: `{minutes} min`", inline=True)
    return embed


def _step_embed(session: RoadSession, step: str, note: str | None = None) -> discord.Embed:
    embed = discord.Embed(
        title=f"SOLANE ROAD / {_step_label(step).upper()}",
        description=note or f"Select the {_step_label(step).lower()} system.",
        color=ROAD_COLOR,
    )
    embed.add_field(name="PICK UP", value=session.pickup.label if session.pickup else "Pending", inline=True)
    embed.add_field(
        name="DESTINATION", value=session.destination.label if session.destination else "Pending", inline=True
    )
    if session.mode == "watch":
        embed.add_field(name="WATCH", value=f"{session.watch_minutes} min", inline=True)
    return embed


def _select_embed(session: RoadSession, step: str, query: str) -> discord.Embed:
    embed = _step_embed(session, step, f"Multiple systems found for `{query}`.")
    embed.add_field(
        name="ACTION", value=f"Choose the correct {_step_label(step).lower()} below.", inline=False
    )
    return embed


def _error_embed(message: str) -> discord.Embed:
    return discord.Embed(title="SOLANE ROAD / ERROR", description=message, color=0xD7263D)


def _watch_alert_embed(payload: dict[str, Any]) -> discord.Embed:
    embed = discord.Embed(
        title="SOLANE ROAD / WATCH ALERT",
        description=f"{_system_name(payload.get('origin'))} -> {_system_name(payload.get('destination'))}",
        color=0xD7263D,
    )
    risk = payload.get("routeRisk") if isinstance(payload.get("routeRisk"), dict) else {}
    embed.add_field(name="RISK", value=f"`{risk.get('label', 'Unavailable')}`", inline=True)
    embed.add_field(
        name="CRITICAL", value=_critical_systems_value(payload.get("criticalSystems")), inline=False
    )
    return embed


def _traffic_value(traffic: Any) -> str:
    if not isinstance(traffic, dict):
        return "`Unavailable`"
    coverage = traffic.get("coverage")
    coverage_label = f"{float(coverage) * 100:.0f}%" if isinstance(coverage, int | float) else "n/a"
    return (
        f"Status: `{traffic.get('label', 'Unavailable')}`\n"
        f"Jumps/h: `{_count_value(traffic.get('totalShipJumpsLastHour'))}`\n"
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
        service = system.get("serviceType")
        service_suffix = f" {service}" if service else ""
        gate_label = _hot_gate_label(item.get("hotGate"))
        lines.append(
            f"**{system.get('name', 'Unknown')}**{service_suffix} "
            f"`{_count_value(item.get('shipKillsLastHour'))} kills/h` | `{gate_label}`"
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


def _focus_gates_value(items: Any) -> str:
    gates = [
        item for item in items or [] if isinstance(item, dict) and int(item.get("killsLastHour") or 0) > 0
    ]
    if not gates:
        return "No verified hot gate in the last hour."
    lines = []
    for gate in gates[:8]:
        gate_name = gate.get("destinationSystemName") or gate.get("name", "Unknown")
        lines.append(f"**{gate_name}** `{gate.get('killsLastHour', 0)}`")
    return "\n".join(lines)


def _focus_corruption_value(payload: dict[str, Any]) -> str:
    state = payload.get("corruptionState")
    if state is None:
        return "Empire Status"
    return (
        f"LVL: `{state}` | `{payload.get('corruptionPercentage', 'n/a')}%`\n"
        f"Suppression: `{payload.get('suppressionPercentage', 'n/a')}%`\n"
        f"FW: `{payload.get('fwStatus', 'n/a')}`"
    )


def _focus_freshness_value(payload: dict[str, Any]) -> str:
    policy = payload.get("refreshPolicy") if isinstance(payload.get("refreshPolicy"), dict) else {}
    esi_status = str(payload.get("esiStatus", "unavailable")).title()
    zkill_status = str(payload.get("zkillStatus", "unavailable")).title()
    return (
        f"ESI: `{esi_status}` | `{_time_label(payload.get('lastSyncedAt'))}`\n"
        f"zKill: `{zkill_status}` | `{_time_label(payload.get('zkillFetchedAt'))}`\n"
        f"Gate refresh: `{policy.get('zkillGateCacheSeconds', 'n/a')}s`"
    )


def _avoid_list_value(items: Any) -> str:
    if not isinstance(items, list) or not items:
        return "None"
    lines = []
    for item in items[:20]:
        if not isinstance(item, dict):
            continue
        system = item.get("system") if isinstance(item.get("system"), dict) else {}
        lines.append(f"`{system.get('name', system.get('id', 'Unknown'))}` {item.get('source', '')}")
    return "\n".join(lines)


def _hot_gate_label(gate: Any) -> str:
    if not isinstance(gate, dict) or int(gate.get("killsLastHour") or 0) < 1:
        return "Clear"
    name = gate.get("destinationSystemName") or gate.get("name") or "Unknown gate"
    return f"{name} ({int(gate.get('killsLastHour') or 0)})"


def _compare_hot_gate(critical: Any) -> str:
    if not isinstance(critical, list) or not critical:
        return "Clear"
    first = next((item for item in critical if isinstance(item, dict)), None)
    return _hot_gate_label(first.get("hotGate") if first else None)


def _traffic_label(traffic: Any) -> str:
    return str(traffic.get("label") or "Unavailable") if isinstance(traffic, dict) else "Unavailable"


def _route_signature(payload: dict[str, Any]) -> tuple[Any, ...]:
    risk = payload.get("routeRisk") if isinstance(payload.get("routeRisk"), dict) else {}
    critical = payload.get("criticalSystems") if isinstance(payload.get("criticalSystems"), list) else []
    critical_sig = tuple(
        (
            (item.get("system") or {}).get("id") if isinstance(item.get("system"), dict) else None,
            item.get("shipKillsLastHour"),
            _hot_gate_label(item.get("hotGate")),
        )
        for item in critical
        if isinstance(item, dict)
    )
    return (risk.get("level"), critical_sig)


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


def _remember_route(state: BotState, state_path: Path, user_id: int, payload: dict[str, Any]) -> None:
    state.remember_route(user_id, payload)
    state.save(state_path)


def _clip(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "."
