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

        # Prefer the JWT bearer token; fall back to a legacy API key if present.
        if profile.access_token:
            headers["Authorization"] = f"Bearer {profile.access_token}"
        elif profile.api_key:
            headers["X-API-Key"] = profile.api_key

        self._client = httpx.Client(
            base_url=profile.base_url,
            timeout=timeout,
            follow_redirects=True,
            headers=headers,
        )
        self.verbose = verbose
        self._refreshed = False

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

        # On expiry, transparently refresh the access token once and retry.
        if response.status_code == 401 and not self._refreshed and self.profile.refresh_token:
            if self._try_refresh():
                try:
                    response = self._client.request(method, path, **kwargs)
                except httpx.RequestError as exc:  # pragma: no cover - network failures
                    raise ApiRequestError(f"Failed to reach API: {exc}") from exc

        if response.status_code >= 400:
            raise ApiRequestError(self._extract_error(response), response.status_code)
        return response

    def _try_refresh(self) -> bool:
        """Exchange the stored refresh token for a new access token. Returns success."""
        self._refreshed = True
        try:
            resp = self._client.post("/api/auth/refresh", json={"refresh_token": self.profile.refresh_token})
        except httpx.RequestError:  # pragma: no cover - network failures
            return False
        if resp.status_code >= 400:
            return False
        try:
            tokens = resp.json()
        except json.JSONDecodeError:  # pragma: no cover
            return False

        access = tokens.get("access_token")
        refresh = tokens.get("refresh_token")
        if not access:
            return False

        # Update in-memory client + persist the rotated tokens to the profile.
        self._client.headers["Authorization"] = f"Bearer {access}"
        self.profile.access_token = access
        if refresh:
            self.profile.refresh_token = refresh
        try:
            config = self.config_store.load()
            config.set_profile(self.profile)
            self.config_store.save(config)
        except DiscoveryCLIError:  # pragma: no cover - persistence best-effort
            pass
        return True

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
