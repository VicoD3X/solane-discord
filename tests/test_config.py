from solane_ai.config import Settings


def test_configured_channels_include_pipes(monkeypatch) -> None:
    monkeypatch.setenv("DISCORD_TOKEN", "test-token")
    monkeypatch.setenv("DISCORD_RISK_CHANNEL_ID", "111")
    monkeypatch.setenv("DISCORD_PIPES_CHANNEL_ID", "1500249974334816296")
    monkeypatch.setenv("DISCORD_POCHVEN_CHANNEL_ID", "1500253870524465304")
    monkeypatch.setenv("DISCORD_LOWSEC_CHANNEL_ID", "1500258086416285748")
    monkeypatch.setenv("DISCORD_NSNPC_CHANNEL_ID", "1500262356310167573")
    monkeypatch.setenv("DISCORD_CORRUPTION_CHANNEL_ID", "222")
    monkeypatch.setenv("DISCORD_SERVICE_CHANNEL_ID", "333")

    settings = Settings.from_env()

    assert settings.configured_channels == {
        "risk": 111,
        "pipes": 1500249974334816296,
        "pochven": 1500253870524465304,
        "lowsec": 1500258086416285748,
        "nsnpc": 1500262356310167573,
        "corruption": 222,
        "service": 333,
    }
