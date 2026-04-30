from solane_ai.state import BotState, TrackedSystemRecord


def test_recently_open_system_is_removed_when_it_closes_again() -> None:
    state = BotState(
        recently_open_systems={
            "30002652": TrackedSystemRecord(
                system_id=30002652,
                name="Ala",
                service_type="Pochven",
                opened_at="2026-04-30T08:00:00+00:00",
            ),
        },
    )

    recently_open = state.update_dynamic_restrictions(
        [
            {
                "id": 30002652,
                "name": "Ala",
                "serviceType": "Pochven",
                "reason": "Severe Pochven PVP activity detected.",
                "shipKillsLastHour": 7,
            },
        ],
        "2026-04-30T09:00:00+00:00",
    )

    assert "30002652" in state.dynamic_restricted_systems
    assert "30002652" not in state.recently_open_systems
    assert all(record.system_id != 30002652 for record in recently_open)


def test_dynamic_restriction_reopening_is_tracked_once() -> None:
    state = BotState(
        dynamic_restricted_systems={
            "30002652": TrackedSystemRecord(
                system_id=30002652,
                name="Ala",
                service_type="Pochven",
                closed_at="2026-04-30T08:00:00+00:00",
                last_seen_at="2026-04-30T08:30:00+00:00",
            ),
        },
    )

    recently_open = state.update_dynamic_restrictions([], "2026-04-30T09:00:00+00:00")

    assert "30002652" not in state.dynamic_restricted_systems
    assert state.recently_open_systems["30002652"].opened_at == "2026-04-30T09:00:00+00:00"
    assert [record.system_id for record in recently_open] == [30002652]
