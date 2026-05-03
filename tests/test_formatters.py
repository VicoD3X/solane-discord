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
                "highSecControlSystems": [
                    {
                        "id": 30002768,
                        "name": "Uedama",
                        "serviceType": "HighSec",
                        "securityDisplay": "0.5",
                        "level": "critical",
                        "label": "Critical",
                        "shipKillsLastHour": 19,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {
                            "id": 500000,
                            "name": "Tama",
                            "destinationSystemId": 30002813,
                            "destinationSystemName": "Tama",
                            "killsLastHour": 2,
                        },
                    },
                    {
                        "id": 30002770,
                        "name": "Sivala",
                        "serviceType": "HighSec",
                        "securityDisplay": "0.6",
                        "level": "flashpoint",
                        "label": "Flashpoint",
                        "shipKillsLastHour": 12,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {"name": "Clear", "killsLastHour": 0},
                    },
                    {
                        "id": 30002771,
                        "name": "Ikao",
                        "serviceType": "HighSec",
                        "securityDisplay": "0.6",
                        "level": "watched",
                        "label": "Watched",
                        "shipKillsLastHour": 8,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {"name": "Clear", "killsLastHour": 0},
                    },
                ],
                "pipesControlSystems": [
                    {
                        "id": 30002768,
                        "name": "Uedama",
                        "serviceType": "HighSec",
                        "securityDisplay": "0.5",
                        "level": "critical",
                        "label": "Critical",
                        "shipKillsLastHour": 19,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {
                            "id": 500000,
                            "name": "Tama",
                            "destinationSystemId": 30002813,
                            "destinationSystemName": "Tama",
                            "killsLastHour": 2,
                        },
                    },
                    {
                        "id": 30002770,
                        "name": "Sivala",
                        "serviceType": "HighSec",
                        "securityDisplay": "0.6",
                        "level": "watched",
                        "label": "Watched",
                        "shipKillsLastHour": 8,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {"name": "Clear", "killsLastHour": 0},
                    },
                    {
                        "id": 30000144,
                        "name": "Perimeter",
                        "serviceType": "HighSec",
                        "securityDisplay": "1.0",
                        "level": "safe",
                        "label": "Safe",
                        "shipKillsLastHour": 0,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {"name": "Clear", "killsLastHour": 0},
                    },
                ],
                "pochvenControlSystems": [
                    {
                        "id": 30003504,
                        "name": "Niarja",
                        "serviceType": "Pochven",
                        "securityDisplay": "-1.0",
                        "level": "critical",
                        "label": "Critical",
                        "shipKillsLastHour": 10,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {
                            "id": 500000,
                            "name": "Komo",
                            "destinationSystemId": 30031392,
                            "destinationSystemName": "Komo",
                            "killsLastHour": 2,
                        },
                    },
                    {
                        "id": 30045328,
                        "name": "Ahtila",
                        "serviceType": "Pochven",
                        "securityDisplay": "-1.0",
                        "level": "watched",
                        "label": "Watched",
                        "shipKillsLastHour": 2,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {"name": "Clear", "killsLastHour": 0},
                    },
                    {
                        "id": 30002652,
                        "name": "Ala",
                        "serviceType": "Pochven",
                        "securityDisplay": "-1.0",
                        "level": "safe",
                        "label": "Safe",
                        "shipKillsLastHour": 1,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {"name": "Clear", "killsLastHour": 0},
                    },
                ],
                "lowSecControlSystems": [
                    {
                        "id": 30002813,
                        "name": "Tama",
                        "serviceType": "LowSec",
                        "securityDisplay": "0.3",
                        "level": "critical",
                        "label": "Critical",
                        "shipKillsLastHour": 20,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {
                            "id": 500000,
                            "name": "Nourvukaiken",
                            "destinationSystemId": 30001379,
                            "destinationSystemName": "Nourvukaiken",
                            "killsLastHour": 3,
                        },
                    },
                    {
                        "id": 30005196,
                        "name": "Ahbazon",
                        "serviceType": "LowSec",
                        "securityDisplay": "0.4",
                        "level": "flashpoint",
                        "label": "Flashpoint",
                        "shipKillsLastHour": 16,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {"name": "Clear", "killsLastHour": 0},
                    },
                    {
                        "id": 30003787,
                        "name": "Agoze",
                        "serviceType": "LowSec",
                        "securityDisplay": "0.2",
                        "level": "flashpoint",
                        "label": "Flashpoint",
                        "shipKillsLastHour": 12,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {"name": "Clear", "killsLastHour": 0},
                    },
                    {
                        "id": 30004984,
                        "name": "Abune",
                        "serviceType": "LowSec",
                        "securityDisplay": "0.3",
                        "level": "watched",
                        "label": "Watched",
                        "shipKillsLastHour": 6,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {"name": "Clear", "killsLastHour": 0},
                    },
                ],
                "npcNullSecControlSystems": [
                    {
                        "id": 30000995,
                        "name": "0-3VW8",
                        "serviceType": "NpcNullSec",
                        "securityDisplay": "-0.0",
                        "level": "critical",
                        "label": "Critical",
                        "shipKillsLastHour": 10,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {
                            "id": 500000,
                            "name": "Tama",
                            "destinationSystemId": 30002813,
                            "destinationSystemName": "Tama",
                            "killsLastHour": 2,
                        },
                    },
                    {
                        "id": 30004510,
                        "name": "0-9UHT",
                        "serviceType": "NpcNullSec",
                        "securityDisplay": "-0.0",
                        "level": "flashpoint",
                        "label": "Flashpoint",
                        "shipKillsLastHour": 4,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {"name": "Clear", "killsLastHour": 0},
                    },
                    {
                        "id": 30001287,
                        "name": "0-BFTQ",
                        "serviceType": "NpcNullSec",
                        "securityDisplay": "-0.2",
                        "level": "watched",
                        "label": "Watched",
                        "shipKillsLastHour": 2,
                        "lastSyncedAt": "2026-04-29T08:00:00+00:00",
                        "topGate": {"name": "Clear", "killsLastHour": 0},
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
    by_key = {panel.key: panel for panel in panels}

    assert [panel.key for panel in panels] == [
        "risk",
        "highsec",
        "pipes",
        "pochven",
        "lowsec",
        "nsnpc",
        "corruption",
        "service",
    ]

    risk = by_key["risk"]
    assert risk.title == "SOLANE RISK / GLOBAL WATCH"
    assert risk.embed.title == "SOLANE RISK / GLOBAL WATCH"
    assert risk.embed.color.value == 0x7AAACE
    assert "HIGHSEC CRITICAL" in risk.embed.fields[0].name
    assert "Uedama" in risk.embed.fields[0].value
    assert "19 kills/h" in risk.embed.fields[0].value
    assert " | " in risk.embed.fields[0].value
    assert "flagged" in risk.embed.fields[0].value
    assert "critical" not in risk.embed.fields[0].value
    assert "LOW-SEC CRITICAL" in risk.embed.fields[1].name
    assert "Tama" in risk.embed.fields[1].value
    assert "20 kills/h" in risk.embed.fields[1].value
    assert " | " in risk.embed.fields[1].value
    assert "flagged" in risk.embed.fields[1].value
    assert "closed" not in risk.embed.fields[1].value
    assert "POCHVEN CRITICAL" in risk.embed.fields[2].name
    assert "Niarja" in risk.embed.fields[2].value
    assert "PERMA" not in risk.embed.fields[2].name
    assert "NS NPC CRITICAL" in risk.embed.fields[3].name
    assert risk.embed.fields[3].name.startswith("\U0001F536")
    assert "0-3VW8" in risk.embed.fields[3].value
    assert "NS NPC" in risk.embed.fields[3].value
    assert "7 kills/h" in risk.embed.fields[3].value
    assert "CORRUPTION CRITICAL" not in risk.embed.fields[3].name
    assert "THERA STATUS" in risk.embed.fields[4].name
    assert "Thera" in risk.embed.fields[4].value
    assert "4 kills/h" in risk.embed.fields[4].value
    assert "RECENTLY SAFER" in risk.embed.fields[5].name
    assert "Old Man Star" in risk.embed.fields[5].value
    assert "cooled" in risk.embed.fields[5].value
    assert "safer" not in risk.embed.fields[5].value
    assert "SOURCE" in risk.embed.fields[6].name
    assert "Last API update: `08:00 EVE`" in risk.embed.fields[6].value
    assert "Check our source" not in risk.embed.fields[6].value
    assert "https://solane-run.app/route-intel" not in risk.embed.fields[6].value
    assert "RESTRICTED" not in " ".join(field.name for field in risk.embed.fields)

    highsec = by_key["highsec"]
    assert highsec.title == "SOLANE RISK / HIGHSEC CONTROL"
    assert highsec.embed.title == "SOLANE RISK / HIGHSEC CONTROL"
    assert highsec.embed.color.value == 0x2FA084
    assert highsec.embed.fields[0].name == "\U0001F534 CRITICAL"
    assert "SYSTEM" in highsec.embed.fields[0].value
    assert "Uedama" in highsec.embed.fields[0].value
    assert "CRIT" in highsec.embed.fields[0].value
    assert "Tama (2)" in highsec.embed.fields[0].value
    assert highsec.embed.fields[1].name == "\U0001F7E0 FLASHPOINT"
    assert "Sivala" in highsec.embed.fields[1].value
    assert "FLASH" in highsec.embed.fields[1].value
    assert highsec.embed.fields[2].name == "\U0001F7E1 WATCHED"
    assert "Ikao" in highsec.embed.fields[2].value
    assert "WATCH" in highsec.embed.fields[2].value
    assert "SOURCE" in highsec.embed.fields[3].name
    assert "STABLE" not in " ".join(field.name for field in highsec.embed.fields)
    assert "SAFE" not in " ".join(field.value for field in highsec.embed.fields)
    assert "pod" not in _panel_text(highsec).lower()

    pipes = by_key["pipes"]
    assert pipes.title == "SOLANE RISK / PIPES CONTROL"
    assert pipes.embed.title == "SOLANE RISK / PIPES CONTROL"
    assert pipes.embed.color.value == 0x79AE6F
    assert pipes.embed.fields[0].name == "\U0001F534 CRITICAL"
    assert "PIPE" in pipes.embed.fields[0].value
    assert "STAT" in pipes.embed.fields[0].value
    assert "KILLS/H" in pipes.embed.fields[0].value
    assert "HOT GATE" in pipes.embed.fields[0].value
    assert "Uedama" in pipes.embed.fields[0].value
    assert "CRIT" in pipes.embed.fields[0].value
    assert "19" in pipes.embed.fields[0].value
    assert "Tama (2)" in pipes.embed.fields[0].value
    assert pipes.embed.fields[1].name == "\U0001F7E1 WATCHED"
    assert "Sivala" in pipes.embed.fields[1].value
    assert "WATCH" in pipes.embed.fields[1].value
    assert "Clear" in pipes.embed.fields[1].value
    assert pipes.embed.fields[2].name == "\U0001F7E2 STABLE"
    assert "Perimeter" in pipes.embed.fields[2].value
    assert "SAFE" in pipes.embed.fields[2].value
    assert "SOURCE" in pipes.embed.fields[3].name
    assert "Last API update: `08:00 EVE`" in pipes.embed.fields[3].value
    assert "pod" not in " ".join(
        [pipes.embed.title, pipes.embed.description or ""]
        + [field.name for field in pipes.embed.fields]
        + [field.value for field in pipes.embed.fields]
    ).lower()

    pochven = by_key["pochven"]
    assert pochven.title == "SOLANE RISK / POCHVEN CONTROL"
    assert pochven.embed.title == "SOLANE RISK / POCHVEN CONTROL"
    assert pochven.embed.color.value == 0xAE2448
    assert pochven.embed.fields[0].name == "\U0001F534 CRITICAL"
    assert "PIPE" in pochven.embed.fields[0].value
    assert "STAT" in pochven.embed.fields[0].value
    assert "KILLS/H" in pochven.embed.fields[0].value
    assert "HOT GATE" in pochven.embed.fields[0].value
    assert "Niarja" in pochven.embed.fields[0].value
    assert "CRIT" in pochven.embed.fields[0].value
    assert "10" in pochven.embed.fields[0].value
    assert "Komo (2)" in pochven.embed.fields[0].value
    assert pochven.embed.fields[1].name == "\U0001F7E1 WATCHED"
    assert "Ahtila" in pochven.embed.fields[1].value
    assert "WATCH" in pochven.embed.fields[1].value
    assert pochven.embed.fields[2].name == "\U0001F7E2 STABLE"
    assert "Ala" in pochven.embed.fields[2].value
    assert "SAFE" in pochven.embed.fields[2].value
    assert "SOURCE" in pochven.embed.fields[3].name
    assert "Last API update: `08:00 EVE`" in pochven.embed.fields[3].value
    assert "pod" not in " ".join(
        [pochven.embed.title, pochven.embed.description or ""]
        + [field.name for field in pochven.embed.fields]
        + [field.value for field in pochven.embed.fields]
    ).lower()
    lowsec = by_key["lowsec"]
    assert lowsec.title == "SOLANE RISK / LOW-SEC CONTROL"
    assert lowsec.embed.title == "SOLANE RISK / LOW-SEC CONTROL"
    assert lowsec.embed.color.value == 0xFF653F
    assert lowsec.embed.fields[0].name == "\U0001F534 CRITICAL"
    assert "SYSTEM" in lowsec.embed.fields[0].value
    assert "STAT" in lowsec.embed.fields[0].value
    assert "KILLS/H" in lowsec.embed.fields[0].value
    assert "HOT GATE" in lowsec.embed.fields[0].value
    assert "Tama" in lowsec.embed.fields[0].value
    assert "CRIT" in lowsec.embed.fields[0].value
    assert "20" in lowsec.embed.fields[0].value
    assert "Nourvukaiken (3)" in lowsec.embed.fields[0].value
    assert lowsec.embed.fields[1].name == "\U0001F7E0 FLASHPOINT"
    assert "Ahbazon" in lowsec.embed.fields[1].value
    assert "Agoze" in lowsec.embed.fields[1].value
    assert "FLASH" in lowsec.embed.fields[1].value
    assert lowsec.embed.fields[2].name == "\U0001F7E1 WATCHED"
    assert "Abune" in lowsec.embed.fields[2].value
    assert "WATCH" in lowsec.embed.fields[2].value
    assert "HOT" not in " ".join(field.name for field in lowsec.embed.fields)
    assert "SOURCE" in lowsec.embed.fields[3].name
    assert "Last API update: `08:00 EVE`" in lowsec.embed.fields[3].value
    assert "SAFE" not in " ".join(field.value for field in lowsec.embed.fields)
    assert "STABLE" not in " ".join(field.name for field in lowsec.embed.fields)
    assert "pod" not in " ".join(
        [lowsec.embed.title, lowsec.embed.description or ""]
        + [field.name for field in lowsec.embed.fields]
        + [field.value for field in lowsec.embed.fields]
    ).lower()
    nsnpc = by_key["nsnpc"]
    assert nsnpc.title == "SOLANE RISK / NS NPC CONTROL"
    assert nsnpc.embed.title == "SOLANE RISK / NS NPC CONTROL"
    assert nsnpc.embed.color.value == 0x8100D1
    assert nsnpc.embed.fields[0].name == "\U0001F534 CRITICAL"
    assert "SYSTEM" in nsnpc.embed.fields[0].value
    assert "STAT" in nsnpc.embed.fields[0].value
    assert "KILLS/H" in nsnpc.embed.fields[0].value
    assert "HOT GATE" in nsnpc.embed.fields[0].value
    assert "0-3VW8" in nsnpc.embed.fields[0].value
    assert "CRIT" in nsnpc.embed.fields[0].value
    assert "10" in nsnpc.embed.fields[0].value
    assert "Tama (2)" in nsnpc.embed.fields[0].value
    assert nsnpc.embed.fields[1].name == "\U0001F7E0 FLASHPOINT"
    assert "0-9UHT" in nsnpc.embed.fields[1].value
    assert "FLASH" in nsnpc.embed.fields[1].value
    assert nsnpc.embed.fields[2].name == "\U0001F7E1 WATCHED"
    assert "0-BFTQ" in nsnpc.embed.fields[2].value
    assert "WATCH" in nsnpc.embed.fields[2].value
    assert "HOT" not in " ".join(field.name for field in nsnpc.embed.fields)
    assert "SOURCE" in nsnpc.embed.fields[3].name
    assert "Last API update: `08:00 EVE`" in nsnpc.embed.fields[3].value
    assert "SAFE" not in " ".join(field.value for field in nsnpc.embed.fields)
    assert "STABLE" not in " ".join(field.name for field in nsnpc.embed.fields)
    assert "pod" not in " ".join(
        [nsnpc.embed.title, nsnpc.embed.description or ""]
        + [field.name for field in nsnpc.embed.fields]
        + [field.value for field in nsnpc.embed.fields]
    ).lower()
    corruption = by_key["corruption"]
    assert corruption.title == "SOLANE RISK / INSURGENCY WATCH"
    assert corruption.embed.title == "SOLANE RISK / INSURGENCY WATCH"
    assert corruption.embed.color.value == 0x1A2CA3
    assert "Siseide" in corruption.embed.fields[0].value
    assert "HS" in corruption.embed.fields[0].value
    assert "14 kills/h" in corruption.embed.fields[0].value
    assert "Angel vs Amarr" in corruption.embed.fields[0].value
    assert "Turnur" in corruption.embed.fields[1].value
    assert "8 kills/h" in corruption.embed.fields[1].value
    assert "RECENTLY RECOVER" in corruption.embed.fields[2].name
    assert "Auga" in corruption.embed.fields[2].value
    assert "LVL3" in corruption.embed.fields[2].value
    assert "Daily 2026-04-30: LVL3 / stable" in corruption.embed.fields[2].value
    assert "Quiet" in corruption.embed.fields[2].value
    assert "Empire Status" in corruption.embed.fields[2].value
    assert "SOURCE" in corruption.embed.fields[3].name
    assert "Check our source" not in corruption.embed.fields[3].value
    assert "https://solane-run.app/route-intel" not in corruption.embed.fields[3].value

    service = by_key["service"]
    assert service.embed.color.value == 0x17C079
    assert service.title == "SOLANE ENGINE ETA"
    assert service.embed.title == "SOLANE ENGINE ETA"
    assert service.embed.fields[1].name.startswith("\U0001F310")
    assert "18,000 pilots" in service.embed.fields[1].value
    assert "ESI SYNC" in service.embed.fields[2].name
    assert "CLUSTER MODE" in service.embed.fields[6].name
    assert service.embed.fields[6].value == "`Online`"
    assert "CLUSTER UPTIME" in service.embed.fields[7].name
    assert "ESI FEED" in service.embed.fields[8].name
    assert service.embed.fields[8].value == "`Fresh`"
    assert "SOURCE" in service.embed.fields[9].name
    assert "Last API update: `08:00 EVE`" in service.embed.fields[9].value
    assert "Check our source" not in service.embed.fields[9].value
    assert "https://solane-run.app/route-intel" not in service.embed.fields[9].value
    assert service.embed.footer.text == "Data from Solane Engine - status.eveonline.com"


def test_engine_eta_turns_red_during_eve_vip_mode() -> None:
    snapshot = deepcopy(_snapshot())
    snapshot["eveStatus"]["vip"] = True

    panel = next(panel for panel in build_panels(snapshot) if panel.key == "service")

    assert panel.key == "service"
    assert panel.embed.color.value == 0xFF1A1A
    assert "`VIP / Maintenance`" in panel.embed.fields[1].value
    assert panel.embed.fields[6].value == "`VIP / Maintenance`"


def test_engine_eta_turns_red_when_eve_status_is_unavailable() -> None:
    snapshot = deepcopy(_snapshot())
    snapshot["eveStatus"] = None

    panel = next(panel for panel in build_panels(snapshot) if panel.key == "service")

    assert panel.embed.color.value == 0xFF1A1A
    assert panel.embed.fields[6].value == "`Unavailable`"
    assert panel.embed.fields[8].value == "`Unavailable`"


def test_engine_eta_turns_red_when_eve_status_feed_errors() -> None:
    snapshot = deepcopy(_snapshot())
    snapshot["errors"] = ["eve_status"]

    panel = next(panel for panel in build_panels(snapshot) if panel.key == "service")

    assert panel.embed.color.value == 0xFF1A1A
    assert panel.embed.fields[6].value == "`Unavailable`"


def test_engine_eta_marks_esi_feed_delayed() -> None:
    snapshot = deepcopy(_snapshot())
    snapshot["eveStatus"]["fetched_at"] = (datetime.now(UTC) - timedelta(minutes=11)).isoformat()

    panel = next(panel for panel in build_panels(snapshot) if panel.key == "service")

    assert panel.embed.color.value == 0x17C079
    assert panel.embed.fields[8].value == "`Delayed`"


def test_build_panels_survives_empty_snapshot() -> None:
    panels = build_panels({})

    assert len(panels) == 8
    assert all(panel.content_hash for panel in panels)


def _panel_text(panel) -> str:
    return " ".join(
        [panel.embed.title or "", panel.embed.description or ""]
        + [field.name for field in panel.embed.fields]
        + [field.value for field in panel.embed.fields]
    )
