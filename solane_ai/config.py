from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    discord_token: str
    solane_api_base_url: str
    solane_bot_api_key: str | None
    risk_channel_id: int | None
    pipes_channel_id: int | None
    pochven_channel_id: int | None
    lowsec_channel_id: int | None
    corruption_channel_id: int | None
    service_channel_id: int | None
    poll_seconds: int
    state_path: Path
    log_level: int

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            discord_token=_required("DISCORD_TOKEN"),
            solane_api_base_url=os.getenv("SOLANE_API_BASE_URL", "http://127.0.0.1:8001").rstrip("/"),
            solane_bot_api_key=_optional("SOLANE_BOT_API_KEY"),
            risk_channel_id=_optional_int("DISCORD_RISK_CHANNEL_ID"),
            pipes_channel_id=_optional_int("DISCORD_PIPES_CHANNEL_ID"),
            pochven_channel_id=_optional_int("DISCORD_POCHVEN_CHANNEL_ID"),
            lowsec_channel_id=_optional_int("DISCORD_LOWSEC_CHANNEL_ID"),
            corruption_channel_id=_optional_int("DISCORD_CORRUPTION_CHANNEL_ID"),
            service_channel_id=_optional_int("DISCORD_SERVICE_CHANNEL_ID"),
            poll_seconds=max(_optional_int("BOT_POLL_SECONDS") or 300, 60),
            state_path=Path(os.getenv("BOT_STATE_PATH", "data/solane-ai-state.json")),
            log_level=getattr(logging, os.getenv("BOT_LOG_LEVEL", "INFO").upper(), logging.INFO),
        )

    @property
    def configured_channels(self) -> dict[str, int]:
        channels: dict[str, int] = {}
        if self.risk_channel_id:
            channels["risk"] = self.risk_channel_id
        if self.pipes_channel_id:
            channels["pipes"] = self.pipes_channel_id
        if self.pochven_channel_id:
            channels["pochven"] = self.pochven_channel_id
        if self.lowsec_channel_id:
            channels["lowsec"] = self.lowsec_channel_id
        if self.corruption_channel_id:
            channels["corruption"] = self.corruption_channel_id
        if self.service_channel_id:
            channels["service"] = self.service_channel_id
        return channels


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _optional(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def _optional_int(name: str) -> int | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
