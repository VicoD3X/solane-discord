from __future__ import annotations

import logging
from typing import Any

import httpx

LOGGER = logging.getLogger(__name__)


class SolaneApi:
    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        headers = {
            "Accept": "application/json",
            "User-Agent": "SolaneAI/0.1 Discord bot",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(base_url=self._base_url, headers=headers, timeout=12.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def health(self) -> dict[str, Any]:
        try:
            return await self._get("/health")
        except (httpx.HTTPError, ValueError):
            status = await self.eve_status()
            return {
                "status": "ok",
                "source": "/api/eve/status",
                "eveStatusAvailable": bool(status),
            }

    async def eve_status(self) -> dict[str, Any]:
        return await self._get("/api/eve/status")

    async def route_intel_overview(self) -> dict[str, Any]:
        return await self._get("/api/route-intel/overview")

    async def search_systems(self, query: str, limit: int = 12) -> list[dict[str, Any]]:
        response = await self._client.get("/api/eve/systems", params={"q": query, "limit": limit})
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("Unexpected payload for /api/eve/systems")
        return [item for item in payload if isinstance(item, dict)]

    async def road_overview(
        self,
        origin_id: int,
        destination_id: int,
        flag: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"originId": origin_id, "destinationId": destination_id}
        if flag:
            params["flag"] = flag
        response = await self._client.get("/api/engine/road/overview", params=params)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Unexpected payload for /api/engine/road/overview")
        return payload

    async def bot_intel_summary(self) -> dict[str, Any] | None:
        try:
            return await self._get("/api/bot/intel-summary")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise

    async def snapshot(self) -> dict[str, Any]:
        health: dict[str, Any] | None = None
        status: dict[str, Any] | None = None
        overview: dict[str, Any] | None = None
        bot_summary: dict[str, Any] | None = None
        errors: list[str] = []

        for label, fetcher in (
            ("health", self.health),
            ("eve_status", self.eve_status),
            ("route_intel", self.route_intel_overview),
            ("bot_summary", self.bot_intel_summary),
        ):
            try:
                result = await fetcher()
            except Exception as exc:  # noqa: BLE001 - never let one feed kill the bot loop.
                LOGGER.warning("Solane API feed %s unavailable: %s", label, exc)
                errors.append(label)
                continue
            if label == "health":
                health = result
            elif label == "eve_status":
                status = result
            elif label == "route_intel":
                overview = result
            elif label == "bot_summary":
                bot_summary = result

        return {
            "health": health,
            "eveStatus": status,
            "routeIntel": overview,
            "botSummary": bot_summary,
            "errors": errors,
        }

    async def _get(self, path: str) -> dict[str, Any]:
        response = await self._client.get(path)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"Unexpected payload for {path}")
        return payload
