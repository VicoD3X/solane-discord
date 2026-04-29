from solane_ai.formatters import build_panels


def test_build_panels_from_route_intel_snapshot() -> None:
    panels = build_panels({
        "health": {"status": "ok"},
        "eveStatus": {"players": 18000, "vip": False},
        "botSummary": {
            "generatedAt": "2026-04-29T08:00:00+00:00",
            "routeRisk": {
                "restrictedSystems": [
                    {
                        "id": 30005196,
                        "name": "Ahbazon",
                        "serviceType": "LowSec",
                        "source": "static",
                        "reason": "Static Solane restricted system.",
                    },
                    {
                        "id": 30002797,
                        "name": "Niarja",
                        "serviceType": "Pochven",
                        "source": "static",
                        "reason": "Static Solane restricted system.",
                    },
                    {
                        "id": 30002813,
                        "name": "Tama",
                        "serviceType": "LowSec",
                        "source": "pvp",
                        "reason": "Severe LowSec PVP activity detected.",
                        "shipKillsLastHour": 20,
                    },
                ],
                "staticRestrictedSystems": [],
                "dynamicRestrictedSystems": [],
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
                        "system": {"name": "Siseide", "serviceType": "HighSec"},
                    },
                    {
                        "corruptionState": 4,
                        "corruptionPercentage": 55.5,
                        "suppressionPercentage": 5.0,
                        "system": {"name": "Turnur", "serviceType": "LowSec"},
                    },
                ],
            },
        },
        "errors": [],
        "recentlyOpenSystems": [
            {"systemId": 30002510, "name": "Old Man Star", "serviceType": "LowSec"},
        ],
        "activeRestrictedSystems": [
            {
                "systemId": 30002813,
                "name": "Tama",
                "serviceType": "LowSec",
                "shipKillsLastHour": 20,
                "closedAt": "2026-04-29T07:30:00+00:00",
            },
        ],
    })

    assert [panel.key for panel in panels] == ["risk", "corruption", "service"]
    assert "Uedama" in panels[0].embed.fields[0].value
    assert panels[0].embed.color.value == 0x7AAACE
    assert "TEMP CLOSURES" in panels[0].embed.fields[1].name
    assert "Tama" in panels[0].embed.fields[1].value
    assert "closed" in panels[0].embed.fields[1].value
    assert "RECENTLY OPEN" in panels[0].embed.fields[2].name
    assert panels[0].embed.fields[3].name.endswith("PERMA RESTRICTED")
    assert "Ahbazon" in panels[0].embed.fields[3].value
    assert "Niarja" in panels[0].embed.fields[3].value
    assert "PERMA RESTRICTED Pochven" not in panels[0].embed.fields[3].name
    assert "SOURCE" in panels[0].embed.fields[4].name
    assert "Last API update: `08:00 EVE`" in panels[0].embed.fields[4].value
    assert "https://solane-run.app/route-intel" in panels[0].embed.fields[4].value
    assert panels[1].embed.color.value == 0x1A2CA3
    assert "Siseide" in panels[1].embed.fields[0].value
    assert "HS" in panels[1].embed.fields[0].value
    assert panels[2].embed.color.value == 0x17C079
    assert "18,000 pilots" in panels[2].embed.fields[1].value
    assert "ESI SYNC" in panels[2].embed.fields[2].name


def test_build_panels_survives_empty_snapshot() -> None:
    panels = build_panels({})

    assert len(panels) == 3
    assert all(panel.content_hash for panel in panels)
