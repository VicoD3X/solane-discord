from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MessageRecord:
    channel_id: int
    message_id: int
    content_hash: str | None = None


@dataclass
class RecentRoadRecord:
    origin_id: int
    origin_name: str
    destination_id: int
    destination_name: str
    flag: str | None = None
    updated_at: str | None = None


@dataclass
class BotState:
    messages: dict[str, MessageRecord] = field(default_factory=dict)
    recent_routes: dict[str, list[RecentRoadRecord]] = field(default_factory=dict)

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
            recent_routes={
                str(user_id): [
                    RecentRoadRecord(
                        origin_id=int(record["originId"]),
                        origin_name=str(record.get("originName") or record["originId"]),
                        destination_id=int(record["destinationId"]),
                        destination_name=str(record.get("destinationName") or record["destinationId"]),
                        flag=record.get("flag"),
                        updated_at=record.get("updatedAt"),
                    )
                    for record in records[:5]
                    if isinstance(record, dict)
                ]
                for user_id, records in payload.get("recentRoutes", {}).items()
                if isinstance(records, list)
            },
        )

    def remember_route(self, user_id: int, payload: dict) -> None:
        origin = payload.get("origin") if isinstance(payload.get("origin"), dict) else {}
        destination = payload.get("destination") if isinstance(payload.get("destination"), dict) else {}
        if "id" not in origin or "id" not in destination:
            return
        key = str(user_id)
        record = RecentRoadRecord(
            origin_id=int(origin["id"]),
            origin_name=str(origin.get("name") or origin["id"]),
            destination_id=int(destination["id"]),
            destination_name=str(destination.get("name") or destination["id"]),
            flag=payload.get("flag"),
            updated_at=payload.get("generatedAt"),
        )
        existing = [
            item
            for item in self.recent_routes.get(key, [])
            if not (
                item.origin_id == record.origin_id
                and item.destination_id == record.destination_id
                and item.flag == record.flag
            )
        ]
        self.recent_routes[key] = [record, *existing][:5]

    def routes_for_user(self, user_id: int) -> list[RecentRoadRecord]:
        return list(self.recent_routes.get(str(user_id), []))

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
            "recentRoutes": {
                user_id: [
                    {
                        "originId": record.origin_id,
                        "originName": record.origin_name,
                        "destinationId": record.destination_id,
                        "destinationName": record.destination_name,
                        "flag": record.flag,
                        "updatedAt": record.updated_at,
                    }
                    for record in records[:5]
                ]
                for user_id, records in self.recent_routes.items()
            },
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
