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


def test_bot_state_remembers_recent_routes(tmp_path) -> None:
    path = tmp_path / "state.json"
    state = BotState()
    for index in range(6):
        state.remember_route(
            42,
            {
                "generatedAt": f"2026-05-02T22:5{index}:00+00:00",
                "flag": "secure",
                "origin": {"id": 30000142 + index, "name": f"Origin {index}"},
                "destination": {"id": 30002187, "name": "Amarr"},
            },
        )

    assert len(state.routes_for_user(42)) == 5
    assert state.routes_for_user(42)[0].origin_name == "Origin 5"

    state.save(path)
    restored = BotState.load(path)

    assert len(restored.routes_for_user(42)) == 5
    assert restored.routes_for_user(42)[0].origin_id == 30000147
