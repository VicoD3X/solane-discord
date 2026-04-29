from solane_ai.formatters import build_panels


def test_build_panels_from_route_intel_snapshot() -> None:
    panels = build_panels({
        "health": {"status": "ok"},
        "eveStatus": {"players": 18000, "vip": False},
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
                        "system": {"name": "Siseide"},
                    },
                    {
                        "corruptionState": 4,
                        "corruptionPercentage": 55.5,
                        "suppressionPercentage": 5.0,
                        "system": {"name": "Turnur"},
                    },
                ],
            },
        },
        "errors": [],
    })

    assert [panel.key for panel in panels] == ["risk", "corruption", "service"]
    assert "Uedama" in panels[0].embed.fields[0].value
    assert "Siseide" in panels[1].embed.fields[0].value
    assert "18,000 pilots" in panels[2].embed.fields[1].value


def test_build_panels_survives_empty_snapshot() -> None:
    panels = build_panels({})

    assert len(panels) == 3
    assert all(panel.content_hash for panel in panels)

