from pathlib import Path


def test_bot_runtime_has_no_direct_external_intel_sources() -> None:
    package_root = Path(__file__).resolve().parents[1] / "solane_ai"
    forbidden = (
        "esi.evetech.net",
        "zkillboard.com",
        "/universe/system_kills",
        "/universe/system_jumps",
    )
    forbidden_runtime_snippets = (
        "httpx.AsyncClient(base_url=\"https://www.eveonline.com",
        "httpx.get(\"https://www.eveonline.com",
        "requests.get(\"https://www.eveonline.com",
    )

    scanned = ""
    for path in package_root.rglob("*.py"):
        scanned += path.read_text(encoding="utf-8")

    for marker in forbidden:
        assert marker not in scanned

    for marker in forbidden_runtime_snippets:
        assert marker not in scanned
