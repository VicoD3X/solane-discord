from solane_ai.road import build_road_embed, create_road_command


def _road_payload() -> dict:
    return {
        "generatedAt": "2026-05-02T22:51:56+00:00",
        "origin": {"id": 30000142, "name": "Jita", "serviceType": "HighSec"},
        "destination": {"id": 30002187, "name": "Amarr", "serviceType": "HighSec"},
        "flag": "secure",
        "jumps": 2,
        "routeTraffic": {
            "totalShipJumpsLastHour": 230,
            "knownSystems": 3,
            "totalSystems": 3,
            "coverage": 1.0,
            "level": "clear",
            "label": "Clear",
        },
        "routeRisk": {
            "level": "critical",
            "label": "Critical",
            "isBlocking": False,
            "reason": "Critical Solane Risk signal detected on route.",
            "affectedSystems": [{"id": 30000144, "name": "Perimeter"}],
            "confidence": "live",
        },
        "criticalSystems": [
            {
                "system": {"id": 30000144, "name": "Perimeter", "serviceType": "HighSec"},
                "level": "critical",
                "label": "Critical",
                "shipKillsLastHour": 18,
                "lastSyncedAt": "2026-05-02T22:50:00+00:00",
                "esiStatus": "fresh",
                "hotGate": {
                    "id": 500000,
                    "name": "Stargate (Tama)",
                    "destinationSystemName": "Tama",
                    "killsLastHour": 1,
                },
                "zkillStatus": "delayed",
                "zkillFetchedAt": "2026-05-02T22:42:00+00:00",
            },
        ],
    }


def test_create_road_command_metadata() -> None:
    command = create_road_command(object())  # type: ignore[arg-type]

    assert command.name == "create-road"
    assert "route intel" in command.description


def test_build_road_embed_contains_route_intel() -> None:
    embed = build_road_embed(_road_payload())

    assert embed.title == "SOLANE ROAD / ROUTE INTEL"
    assert "Jita -> Amarr" in embed.description
    fields = {field.name: field.value for field in embed.fields}
    assert "Jumps: `2`" in fields["ROUTE"]
    assert "Status: `Clear`" in fields["TRAFFIC FLOW"]
    assert "**Perimeter** HighSec `18 kills/h` | `Tama (1)`" in fields["CRITICAL SYSTEMS"]
    assert "zKill gates: `Delayed`" in fields["FRESHNESS"]
    assert "Potential delayed intel" in fields["FRESHNESS"]
