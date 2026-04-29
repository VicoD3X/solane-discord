from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class MessageRecord:
    channel_id: int
    message_id: int
    content_hash: str | None = None


@dataclass
class TrackedSystemRecord:
    system_id: int
    name: str
    service_type: str | None = None
    reason: str | None = None
    ship_kills_last_hour: int | None = None
    closed_at: str | None = None
    last_seen_at: str | None = None
    opened_at: str | None = None

    @classmethod
    def from_api(cls, payload: dict, timestamp: str | None) -> TrackedSystemRecord:
        return cls(
            system_id=int(payload["id"]),
            name=str(payload.get("name") or payload["id"]),
            service_type=payload.get("serviceType"),
            reason=payload.get("reason"),
            ship_kills_last_hour=payload.get("shipKillsLastHour"),
            closed_at=payload.get("closedAt") or timestamp,
            last_seen_at=payload.get("lastSyncedAt") or timestamp,
        )

    @classmethod
    def from_payload(cls, payload: dict) -> TrackedSystemRecord:
        return cls(
            system_id=int(payload["systemId"]),
            name=str(payload["name"]),
            service_type=payload.get("serviceType"),
            reason=payload.get("reason"),
            ship_kills_last_hour=payload.get("shipKillsLastHour"),
            closed_at=payload.get("closedAt"),
            last_seen_at=payload.get("lastSeenAt"),
            opened_at=payload.get("openedAt"),
        )

    def to_payload(self) -> dict:
        return {
            "systemId": self.system_id,
            "name": self.name,
            "serviceType": self.service_type,
            "reason": self.reason,
            "shipKillsLastHour": self.ship_kills_last_hour,
            "closedAt": self.closed_at,
            "lastSeenAt": self.last_seen_at,
            "openedAt": self.opened_at,
        }


@dataclass
class BotState:
    messages: dict[str, MessageRecord] = field(default_factory=dict)
    dynamic_restricted_systems: dict[str, TrackedSystemRecord] = field(default_factory=dict)
    recently_open_systems: dict[str, TrackedSystemRecord] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> BotState:
        if not path.exists():
            return cls()
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        return cls(
            messages={
                key: MessageRecord(
                    channel_id=int(record["channelId"]),
                    message_id=int(record["messageId"]),
                    content_hash=record.get("contentHash"),
                )
                for key, record in payload.get("messages", {}).items()
            },
            dynamic_restricted_systems={
                key: TrackedSystemRecord.from_payload(record)
                for key, record in payload.get("dynamicRestrictedSystems", {}).items()
            },
            recently_open_systems={
                key: TrackedSystemRecord.from_payload(record)
                for key, record in payload.get("recentlyOpenSystems", {}).items()
            },
        )

    def update_dynamic_restrictions(
        self,
        systems: list[dict],
        timestamp: str | None,
    ) -> list[TrackedSystemRecord]:
        current: dict[str, TrackedSystemRecord] = {}
        for system in systems:
            if system.get("id") is None:
                continue
            key = str(system["id"])
            record = TrackedSystemRecord.from_api(system, timestamp)
            previous = self.dynamic_restricted_systems.get(key)
            if previous is not None:
                record.closed_at = previous.closed_at or previous.last_seen_at or timestamp
            current[key] = record
        opened_keys = set(self.dynamic_restricted_systems) - set(current)
        for key in opened_keys:
            record = self.dynamic_restricted_systems[key]
            record.opened_at = timestamp
            self.recently_open_systems[key] = record

        self.dynamic_restricted_systems = current
        self.recently_open_systems = dict(
            sorted(
                self.recently_open_systems.items(),
                key=lambda item: item[1].opened_at or "",
                reverse=True,
            )[:10]
        )
        return list(self.recently_open_systems.values())

    def active_restrictions(self) -> list[TrackedSystemRecord]:
        return sorted(
            self.dynamic_restricted_systems.values(),
            key=lambda record: _parse_timestamp(record.closed_at),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "messages": {
                key: {
                    "channelId": record.channel_id,
                    "messageId": record.message_id,
                    "contentHash": record.content_hash,
                }
                for key, record in self.messages.items()
            },
            "dynamicRestrictedSystems": {
                key: record.to_payload()
                for key, record in self.dynamic_restricted_systems.items()
            },
            "recentlyOpenSystems": {
                key: record.to_payload()
                for key, record in self.recently_open_systems.items()
            },
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _parse_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime.max.replace(tzinfo=UTC)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.max.replace(tzinfo=UTC)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
