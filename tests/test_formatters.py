from copy import deepcopy
from datetime import UTC, datetime, timedelta

from solane_ai.formatters import build_panels


def _snapshot() -> dict:
    return {
        "health": {"status": "ok"},
        "eveStatus": {
            "players": 18000,
            "server_version": "2938421",
            "start_time": (datetime.now(UTC) - timedelta(hours=3, minutes=12)).isoformat(),
            "vip": False,
            "fetched_at": datetime.now(UTC).isoformat(),
        },
        "botSummary": {
            "generatedAt": "2026-04-29T08:00:00+00:00",
            "routeRisk": {
                "highSecCriticalSystems": [
                    {
                        "id": 30002768,
                        "name": "Uedama",
                        "serviceType": "HighSec",
                        "reason": "Severe HighSec ship loss activity detected.",
                        "level": "critical",
                        "label": "Critical",
                        "shipKillsLastHour": 19,
                        "criticalAt": "2026-04-29T07:10:00+00:00",
                    },
                ],
                "lowSecCriticalSystems": [
                    {
                        "id": 30002813,
                        "name": "Tama",
                        "serviceType": "LowSec",
                        "reason": "Severe LowSec PVP activity detected.",
                        "level": "critical",
                        "label": "Critical",
                        "shipKillsLastHour": 20,
                        "criticalAt": "2026-04-29T07:30:00+00:00",
                    },
                ],
                "pochvenCriticalSystems": [
                    {
                        "id": 30003504,
                        "name": "Niarja",
                        "serviceType": "Pochven",
                        "reason": "Severe Pochven PVP activity detected.",
                        "level": "critical",
                        "label": "Critical",
                        "shipKillsLastHour": 9,
                        "criticalAt": "2026-04-29T07:00:00+00:00",
                    },
                ],
                "npcNullSecCriticalSystems": [
                    {
                        "id": 30000995,
                        "name": "0-3VW8",
                        "serviceType": "NpcNullSec",
                        "reason": "Severe NPC nullsec PVP activity detected.",
                        "level": "critical",
                        "label": "Critical",
                        "shipKillsLastHour": 7,
                        "criticalAt": "2026-04-29T07:20:00+00:00",
                    },
                ],
                "theraStatus": {
                    "id": 31000005,
                    "name": "Thera",
                    "serviceType": "Thera",
                    "status": "Watched",
                    "level": "watched",
                    "label": "Watched",
                    "shipKillsLastHour": 4,
                    "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                },
                "recentlySaferSystems": [
                    {
                        "id": 30002510,
                        "name": "Old Man Star",
                        "serviceType": "LowSec",
                        "shipKillsLastHour": 3,
                        "saferAt": "2026-04-29T07:55:00+00:00",
                    },
                ],
            },
            "service": {"status": "open", "label": "Open"},
        },
        "routeIntel": {
            "crossroads": {
                "label": "16 systems",
                "items": [
                    {
                        "label": "Danger",
                        "shipKillsLastHour": 19,
                        "system": {"name": "Uedama"},
                    },
                    {
                        "label": "Watched",
                        "shipKillsLastHour": 8,
                        "system": {"name": "Sivala"},
                    },
                ],
            },
            "gold": {"label": "31 routes", "items": []},
            "corruption": {
                "label": "1 LVL4 / 1 LVL5",
                "items": [
                    {
                        "corruptionState": 5,
                        "corruptionPercentage": 88.4,
                        "suppressionPercentage": 12.0,
                        "shipKillsLastHour": 14,
                        "fwStatus": "Angel vs Amarr",
                        "system": {"name": "Siseide", "serviceType": "HighSec"},
                    },
                    {
                        "corruptionState": 4,
                        "corruptionPercentage": 55.5,
                        "suppressionPercentage": 5.0,
                        "shipKillsLastHour": 8,
                        "fwStatus": "Angel vs Amarr",
                        "system": {"name": "Turnur", "serviceType": "LowSec"},
                    },
                ],
                "recentlyRecoveredSystems": [
                    {
                        "system": {"name": "Auga", "serviceType": "LowSec"},
                        "previousCorruptionState": 5,
                        "currentCorruptionState": 3,
                        "currentStatus": "LVL3",
                        "shipKillsLastHour": 2,
                        "fwStatus": "Angel vs Amarr",
                        "recoveredAt": "2026-04-29T07:30:00+00:00",
                        "dailyChecks": [
                            {
                                "date": "2026-04-30",
                                "currentStatus": "LVL3",
                                "trend": "stable",
                            }
                        ],
                    },
                    {
                        "system": {"name": "Quiet", "serviceType": "LowSec"},
                        "previousCorruptionState": 4,
                        "currentStatus": "Empire Status",
                        "shipKillsLastHour": None,
                        "fwStatus": "Angel vs Empire",
                        "recoveredAt": "2026-04-29T07:40:00+00:00",
                    },
                ],
            },
        },
        "errors": [],
    }


def test_build_panels_from_route_intel_snapshot() -> None:
    panels = build_panels(_snapshot())

    assert [panel.key for panel in panels] == ["risk", "corruption", "service"]
    assert panels[0].title == "SOLANE RISK / GLOBAL WATCH"
    assert panels[0].embed.title == "SOLANE RISK / GLOBAL WATCH"
    assert panels[0].embed.color.value == 0x7AAACE
    assert "HIGHSEC CRITICAL" in panels[0].embed.fields[0].name
    assert "Uedama" in panels[0].embed.fields[0].value
    assert "19 kills/h" in panels[0].embed.fields[0].value
    assert " | " in panels[0].embed.fields[0].value
    assert "flagged" in panels[0].embed.fields[0].value
    assert "critical" not in panels[0].embed.fields[0].value
    assert "LOW-SEC CRITICAL" in panels[0].embed.fields[1].name
    assert "Tama" in panels[0].embed.fields[1].value
    assert "20 kills/h" in panels[0].embed.fields[1].value
    assert " | " in panels[0].embed.fields[1].value
    assert "flagged" in panels[0].embed.fields[1].value
    assert "closed" not in panels[0].embed.fields[1].value
    assert "POCHVEN CRITICAL" in panels[0].embed.fields[2].name
    assert "Niarja" in panels[0].embed.fields[2].value
    assert "PERMA" not in panels[0].embed.fields[2].name
    assert "NS NPC CRITICAL" in panels[0].embed.fields[3].name
    assert "0-3VW8" in panels[0].embed.fields[3].value
    assert "NS NPC" in panels[0].embed.fields[3].value
    assert "7 kills/h" in panels[0].embed.fields[3].value
    assert "CORRUPTION CRITICAL" not in panels[0].embed.fields[3].name
    assert "THERA STATUS" in panels[0].embed.fields[4].name
    assert "Thera" in panels[0].embed.fields[4].value
    assert "4 kills/h" in panels[0].embed.fields[4].value
    assert "RECENTLY SAFER" in panels[0].embed.fields[5].name
    assert "Old Man Star" in panels[0].embed.fields[5].value
    assert "cooled" in panels[0].embed.fields[5].value
    assert "safer" not in panels[0].embed.fields[5].value
    assert "SOURCE" in panels[0].embed.fields[6].name
    assert "Last API update: `08:00 EVE`" in panels[0].embed.fields[6].value
    assert "Check our source" not in panels[0].embed.fields[6].value
    assert "https://solane-run.app/route-intel" not in panels[0].embed.fields[6].value
    assert "RESTRICTED" not in " ".join(field.name for field in panels[0].embed.fields)
    assert panels[1].title == "SOLANE RISK / INSURGENCY WATCH"
    assert "SOLANE RISK / INSURGENCY WATCH" in panels[1].embed.title
    assert panels[1].embed.color.value == 0x1A2CA3
    assert "Siseide" in panels[1].embed.fields[0].value
    assert "HS" in panels[1].embed.fields[0].value
    assert "14 kills/h" in panels[1].embed.fields[0].value
    assert "Angel vs Amarr" in panels[1].embed.fields[0].value
    assert "Turnur" in panels[1].embed.fields[1].value
    assert "8 kills/h" in panels[1].embed.fields[1].value
    assert "RECENTLY RECOVER" in panels[1].embed.fields[2].name
    assert "Auga" in panels[1].embed.fields[2].value
    assert "LVL3" in panels[1].embed.fields[2].value
    assert "Daily 2026-04-30: LVL3 / stable" in panels[1].embed.fields[2].value
    assert "Quiet" in panels[1].embed.fields[2].value
    assert "Empire Status" in panels[1].embed.fields[2].value
    assert "SOURCE" in panels[1].embed.fields[3].name
    assert "Check our source" not in panels[1].embed.fields[3].value
    assert "https://solane-run.app/route-intel" not in panels[1].embed.fields[3].value
    assert panels[2].embed.color.value == 0x17C079
    assert panels[2].title == "SOLANE ENGINE ETA"
    assert "SOLANE ENGINE ETA" in panels[2].embed.title
    assert panels[2].embed.fields[1].name.startswith("\U0001F310")
    assert "18,000 pilots" in panels[2].embed.fields[1].value
    assert "ESI SYNC" in panels[2].embed.fields[2].name
    assert "CLUSTER MODE" in panels[2].embed.fields[6].name
    assert panels[2].embed.fields[6].value == "`Online`"
    assert "CLUSTER UPTIME" in panels[2].embed.fields[7].name
    assert "ESI FEED" in panels[2].embed.fields[8].name
    assert panels[2].embed.fields[8].value == "`Fresh`"
    assert "SOURCE" in panels[2].embed.fields[9].name
    assert "Last API update: `08:00 EVE`" in panels[2].embed.fields[9].value
    assert "Check our source" not in panels[2].embed.fields[9].value
    assert "https://solane-run.app/route-intel" not in panels[2].embed.fields[9].value
    assert panels[2].embed.footer.text == "Data from Solane Engine - status.eveonline.com"


def test_engine_eta_turns_red_during_eve_vip_mode() -> None:
    snapshot = deepcopy(_snapshot())
    snapshot["eveStatus"]["vip"] = True

    panel = build_panels(snapshot)[2]

    assert panel.key == "service"
    assert panel.embed.color.value == 0xFF1A1A
    assert "`VIP / Maintenance`" in panel.embed.fields[1].value
    assert panel.embed.fields[6].value == "`VIP / Maintenance`"


def test_engine_eta_turns_red_when_eve_status_is_unavailable() -> None:
    snapshot = deepcopy(_snapshot())
    snapshot["eveStatus"] = None

    panel = build_panels(snapshot)[2]

    assert panel.embed.color.value == 0xFF1A1A
    assert panel.embed.fields[6].value == "`Unavailable`"
    assert panel.embed.fields[8].value == "`Unavailable`"


def test_engine_eta_turns_red_when_eve_status_feed_errors() -> None:
    snapshot = deepcopy(_snapshot())
    snapshot["errors"] = ["eve_status"]

    panel = build_panels(snapshot)[2]

    assert panel.embed.color.value == 0xFF1A1A
    assert panel.embed.fields[6].value == "`Unavailable`"


def test_engine_eta_marks_esi_feed_delayed() -> None:
    snapshot = deepcopy(_snapshot())
    snapshot["eveStatus"]["fetched_at"] = (datetime.now(UTC) - timedelta(minutes=11)).isoformat()

    panel = build_panels(snapshot)[2]

    assert panel.embed.color.value == 0x17C079
    assert panel.embed.fields[8].value == "`Delayed`"


def test_build_panels_survives_empty_snapshot() -> None:
    panels = build_panels({})

    assert len(panels) == 3
    assert all(panel.content_hash for panel in panels)
