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
class BotState:
    messages: dict[str, MessageRecord] = field(default_factory=dict)

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
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
