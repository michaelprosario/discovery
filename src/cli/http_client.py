"""HTTP client helpers for communicating with the Discovery API."""

from __future__ import annotations

import json
from contextlib import AbstractContextManager
from typing import Any, Dict

import httpx

from .config_store import ConfigStore, DiscoveryProfile
from .exceptions import ApiRequestError, DiscoveryCLIError


class DiscoveryApiClient(AbstractContextManager["DiscoveryApiClient"]):
    """Thin wrapper around httpx for Discovery API calls."""

    def __init__(
        self,
        profile: DiscoveryProfile,
        *,
        timeout: float = 30.0,
        verbose: bool = False,
        config_store: ConfigStore | None = None,
    ) -> None:
        self.profile = profile
        self.config_store = config_store or ConfigStore()
        
        headers: Dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "discovery-cli/0.2",
        }
        
        # Add API key if present
        if profile.api_key:
            headers["X-API-Key"] = profile.api_key
        
        self._client = httpx.Client(
            base_url=profile.base_url,
            timeout=timeout,
            follow_redirects=True,
            headers=headers,
        )
        self.verbose = verbose

    # Context manager ---------------------------------------------------------------
    def __enter__(self) -> "DiscoveryApiClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    def close(self) -> None:
        self._client.close()

    # Requests ----------------------------------------------------------------------
    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.RequestError as exc:  # pragma: no cover - network failures
            raise ApiRequestError(f"Failed to reach API: {exc}") from exc
        if response.status_code >= 400:
            raise ApiRequestError(self._extract_error(response), response.status_code)
        return response

    def get_json(self, path: str, **kwargs) -> Any:
        response = self.request("GET", path, **kwargs)
        return self._parse_json(response)

    def post_json(self, path: str, **kwargs) -> Any:
        response = self.request("POST", path, **kwargs)
        return self._parse_json(response)

    def put_json(self, path: str, **kwargs) -> Any:
        response = self.request("PUT", path, **kwargs)
        return self._parse_json(response)

    def patch_json(self, path: str, **kwargs) -> Any:
        response = self.request("PATCH", path, **kwargs)
        return self._parse_json(response)

    def delete(self, path: str, **kwargs) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)

    # Internal ----------------------------------------------------------------------
    def _parse_json(self, response: httpx.Response) -> Any:
        if not response.content:
            return None
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise ApiRequestError("API returned invalid JSON", response.status_code) from exc

    def _extract_error(self, response: httpx.Response) -> str:
        try:
            payload = response.json()
        except json.JSONDecodeError:
            return f"HTTP {response.status_code}: {response.text.strip()}"
        if isinstance(payload, dict):
            if "detail" in payload:
                return f"HTTP {response.status_code}: {payload['detail']}"
            if "error" in payload:
                return f"HTTP {response.status_code}: {payload['error']}"
        return f"HTTP {response.status_code}: {payload}"


__all__ = ["DiscoveryApiClient"]
