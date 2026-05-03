from __future__ import annotations

import asyncio
import logging

import discord
from discord import app_commands

from .config import Settings
from .formatters import PanelMessage, build_panels
from .road import (
    create_focus_system_command,
    create_road_avoid_group,
    create_road_command,
    create_road_compare_command,
    create_road_refresh_command,
    create_road_watch_command,
)
from .solane_api import SolaneApi
from .state import BotState, MessageRecord

LOGGER = logging.getLogger(__name__)


class SolaneAIBot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.none()
        intents.guilds = True
        super().__init__(intents=intents)
        self.settings = settings
        self.state = BotState.load(settings.state_path)
        self.api = SolaneApi(settings.solane_api_base_url, settings.solane_bot_api_key)
        self.tree = app_commands.CommandTree(self)
        self.tree.add_command(create_road_command(self.api, self.state, self.settings.state_path))
        self.tree.add_command(create_road_refresh_command(self.api, self.state, self.settings.state_path))
        self.tree.add_command(create_road_compare_command(self.api, self.state, self.settings.state_path))
        self.tree.add_command(create_road_watch_command(self.api, self.state, self.settings.state_path))
        self.tree.add_command(create_focus_system_command(self.api))
        self.tree.add_command(create_road_avoid_group(self.api))
        self._worker: asyncio.Task[None] | None = None
        self._commands_synced = False

    async def setup_hook(self) -> None:
        self._worker = asyncio.create_task(self._poll_forever(), name="solane-ai-poller")

    async def close(self) -> None:
        if self._worker:
            self._worker.cancel()
        await self.api.close()
        await super().close()

    async def on_ready(self) -> None:
        LOGGER.info("SOLANE API connected as %s (%s)", self.user, self.user.id if self.user else "unknown")
        if not self._commands_synced:
            await self._sync_commands()
            self._commands_synced = True

    async def _sync_commands(self) -> None:
        if not self.guilds:
            synced = await self.tree.sync()
            LOGGER.info("Synced %s SOLANE API global commands", len(synced))
            return
        for guild in self.guilds:
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            LOGGER.info("Synced %s SOLANE API commands for guild %s", len(synced), guild.id)

    async def _poll_forever(self) -> None:
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                await self.publish_once()
            except Exception:
                LOGGER.exception("SOLANE API publish cycle failed")
            await asyncio.sleep(self.settings.poll_seconds)

    async def publish_once(self) -> None:
        snapshot = await self.api.snapshot()
        panels = build_panels(snapshot)
        for panel in panels:
            channel_id = self.settings.configured_channels.get(panel.key)
            if not channel_id:
                LOGGER.info("Panel %s skipped: channel not configured", panel.key)
                continue
            await self._upsert_panel(panel, channel_id)
        self.state.save(self.settings.state_path)

    async def _upsert_panel(self, panel: PanelMessage, channel_id: int) -> None:
        record = self.state.messages.get(panel.key)
        if record and record.channel_id == channel_id and record.content_hash == panel.content_hash:
            return

        channel = self.get_channel(channel_id) or await self.fetch_channel(channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            raise RuntimeError(f"Discord channel {channel_id} is not messageable")

        message: discord.Message | None = None
        if record and record.channel_id == channel_id:
            try:
                message = await channel.fetch_message(record.message_id)  # type: ignore[attr-defined]
            except (discord.NotFound, discord.Forbidden):
                message = None

        if message is None:
            message = await channel.send(embed=panel.embed)
            LOGGER.info("Created SOLANE API panel %s in channel %s", panel.key, channel_id)
        else:
            await message.edit(embed=panel.embed)
            LOGGER.info("Updated SOLANE API panel %s", panel.key)

        self.state.messages[panel.key] = MessageRecord(
            channel_id=channel_id,
            message_id=message.id,
            content_hash=panel.content_hash,
        )


def main() -> None:
    settings = Settings.from_env()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    if not settings.configured_channels:
        raise RuntimeError("At least one Discord channel ID must be configured.")
    bot = SolaneAIBot(settings)
    bot.run(settings.discord_token, log_handler=None)
