from solane_ai.state import BotState, MessageRecord


def test_bot_state_persists_only_discord_message_records(tmp_path) -> None:
    path = tmp_path / "state.json"
    state = BotState(
        messages={
            "risk": MessageRecord(channel_id=123, message_id=456, content_hash="abc"),
        },
    )

    state.save(path)
    restored = BotState.load(path)

    assert restored.messages["risk"].channel_id == 123
    assert restored.messages["risk"].message_id == 456
    assert restored.messages["risk"].content_hash == "abc"
