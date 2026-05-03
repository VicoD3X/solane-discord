from solane_ai.road import (
    build_avoids_embed,
    build_compare_embed,
    build_focus_embed,
    build_road_embed,
    create_focus_system_command,
    create_road_avoid_group,
    create_road_command,
    create_road_compare_command,
    create_road_refresh_command,
    create_road_watch_command,
)
from solane_ai.state import BotState


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
    state = BotState()
    command = create_road_command(object(), state, object())  # type: ignore[arg-type]

    assert command.name == "create-road"
    assert "route intel" in command.description


def test_road_v2_command_metadata() -> None:
    state = BotState()

    refresh = create_road_refresh_command(object(), state, object())  # type: ignore[arg-type]
    compare = create_road_compare_command(object(), state, object())  # type: ignore[arg-type]
    watch = create_road_watch_command(object(), state, object())  # type: ignore[arg-type]
    focus = create_focus_system_command(object())  # type: ignore[arg-type]
    avoid = create_road_avoid_group(object())  # type: ignore[arg-type]

    assert refresh.name == "road-refresh"
    assert compare.name == "road-compare"
    assert watch.name == "road-watch"
    assert focus.name == "focus-system"
    assert avoid.name == "road-avoid"
    assert {command.name for command in avoid.commands} == {"list", "add", "remove"}


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


def test_build_compare_embed_contains_flags() -> None:
    payload = {
        "generatedAt": "2026-05-02T22:51:56+00:00",
        "origin": {"id": 30000142, "name": "Jita"},
        "destination": {"id": 30002187, "name": "Amarr"},
        "options": [
            {"flag": "secure", "status": "ready", "overview": _road_payload()},
            {"flag": "shortest", "status": "unavailable", "error": "Route unavailable"},
        ],
    }

    embed = build_compare_embed(payload)

    assert embed.title == "SOLANE ROAD / ROUTE COMPARE"
    fields = {field.name: field.value for field in embed.fields}
    assert "Jumps: `2`" in fields["SECURE"]
    assert "Unavailable" in fields["SHORTEST"]


def test_build_focus_embed_contains_fast_intel() -> None:
    payload = {
        "generatedAt": "2026-05-02T22:51:56+00:00",
        "system": {
            "id": 30000144,
            "name": "Perimeter",
            "serviceType": "HighSec",
            "securityDisplay": "1.0",
        },
        "routeRisk": {"label": "Critical", "riskSource": "live_pvp"},
        "shipJumpsLastHour": 50,
        "shipKillsLastHour": 18,
        "lastSyncedAt": "2026-05-02T22:50:00+00:00",
        "esiStatus": "fresh",
        "gates": [{"destinationSystemName": "Tama", "killsLastHour": 2}],
        "zkillStatus": "fresh",
        "zkillFetchedAt": "2026-05-02T22:51:00+00:00",
        "refreshPolicy": {"zkillGateCacheSeconds": 60},
    }

    embed = build_focus_embed(payload)

    assert embed.title == "SOLANE FOCUS / SYSTEM SCAN"
    fields = {field.name: field.value for field in embed.fields}
    assert "Jumps/h: `50`" in fields["SYSTEM"]
    assert "Kills/h: `18`" in fields["RISK"]
    assert "**Tama** `2`" in fields["HOT GATES"]
    assert "Gate refresh: `60s`" in fields["FRESHNESS"]


def test_build_avoids_embed_lists_effective_avoids() -> None:
    embed = build_avoids_embed({
        "generatedAt": "2026-05-02T22:51:56+00:00",
        "effectiveAvoids": [
            {"system": {"id": 30002049, "name": "Uttindar"}, "source": "default"},
        ],
        "removedDefaultAvoids": [],
    })

    assert embed.title == "SOLANE ROAD / AVOIDS"
    fields = {field.name: field.value for field in embed.fields}
    assert "`Uttindar` default" in fields["ACTIVE"]
