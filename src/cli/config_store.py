"""Persistent configuration handling for the Discovery CLI."""

from __future__ import annotations

import json
import os
import tomllib
from pathlib import Path
from typing import Dict

import tomli_w
from pydantic import AnyHttpUrl, BaseModel, Field, ValidationError, model_validator

from .exceptions import ConfigNotInitializedError, DiscoveryCLIError

CONFIG_ENV_VAR = "DISCOVERY_CONFIG_HOME"
CONFIG_FILENAME = "config.toml"
STATE_FILENAME = "state.json"


class DiscoveryProfile(BaseModel):
    """Connection details for a Discovery API profile."""

    name: str = Field(..., min_length=1)
    url: AnyHttpUrl
    api_key: str | None = None
    default_notebook: str | None = None

    @property
    def base_url(self) -> str:
        return str(self.url).rstrip("/")


class DiscoveryConfig(BaseModel):
    """CLI configuration with one or more profiles."""

    active_profile: str = Field(default="default")
    profiles: Dict[str, DiscoveryProfile] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _inject_profile_names(cls, data: dict) -> dict:
        profiles = data.get("profiles") or {}
        for key, value in profiles.items():
            if isinstance(value, dict) and "name" not in value:
                value["name"] = key
        return data

    def get_profile(self, name: str | None = None) -> DiscoveryProfile:
        target = name or self.active_profile
        try:
            return self.profiles[target]
        except KeyError as exc:
            raise ConfigNotInitializedError(f"Profile '{target}' is not defined.") from exc

    def set_profile(self, profile: DiscoveryProfile) -> None:
        self.profiles[profile.name] = profile

    def ensure_active(self) -> DiscoveryProfile:
        if not self.profiles:
            raise ConfigNotInitializedError("No profiles configured. Run 'discovery config init'.")
        if self.active_profile not in self.profiles:
            raise ConfigNotInitializedError(
                f"Active profile '{self.active_profile}' is undefined. Use 'discovery config use'."
            )
        return self.profiles[self.active_profile]


class CLIState(BaseModel):
    """Mutable local state tracked by the CLI."""

    recent_notebooks: Dict[str, str] = Field(default_factory=dict)

    def get_recent_notebook(self, profile: str) -> str | None:
        return self.recent_notebooks.get(profile)

    def set_recent_notebook(self, profile: str, notebook_id: str) -> None:
        self.recent_notebooks[profile] = notebook_id


class ConfigStore:
    """Load and persist CLI configuration and state."""

    def __init__(self, config_home: Path | None = None) -> None:
        self.config_home = (config_home or self._default_home()).expanduser()
        self.config_path = self.config_home / CONFIG_FILENAME
        self.state_path = self.config_home / STATE_FILENAME

    def _default_home(self) -> Path:
        env = os.environ.get(CONFIG_ENV_VAR)
        return Path(env).expanduser() if env else Path.home() / ".discovery"

    # Configuration -----------------------------------------------------------------
    def load(self) -> DiscoveryConfig:
        if not self.config_path.exists():
            raise ConfigNotInitializedError("Configuration not initialized. Run 'discovery config init'.")
        with self.config_path.open("rb") as handle:
            raw = tomllib.load(handle)
        try:
            return DiscoveryConfig.model_validate(raw)
        except ValidationError as exc:
            raise DiscoveryCLIError(f"Invalid configuration: {exc}") from exc

    def save(self, config: DiscoveryConfig) -> None:
        self.config_home.mkdir(parents=True, exist_ok=True)
        payload = json.loads(config.model_dump_json(exclude_none=True))
        with self.config_path.open("w", encoding="utf-8") as handle:
            handle.write(tomli_w.dumps(payload))

    def upsert_profile(self, profile: DiscoveryProfile, make_active: bool = False) -> DiscoveryConfig:
        try:
            config = self.load()
        except ConfigNotInitializedError:
            config = DiscoveryConfig(active_profile=profile.name, profiles={})
        config.set_profile(profile)
        if make_active or config.active_profile not in config.profiles:
            config.active_profile = profile.name
        self.save(config)
        return config

    def set_active_profile(self, profile_name: str) -> DiscoveryConfig:
        config = self.load()
        if profile_name not in config.profiles:
            raise ConfigNotInitializedError(f"Profile '{profile_name}' does not exist.")
        config.active_profile = profile_name
        self.save(config)
        return config

    # State -------------------------------------------------------------------------
    def load_state(self) -> CLIState:
        if not self.state_path.exists():
            return CLIState()
        with self.state_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        try:
            return CLIState.model_validate(raw)
        except ValidationError:
            return CLIState()

    def save_state(self, state: CLIState) -> None:
        self.config_home.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as handle:
            json.dump(state.model_dump(mode="python"), handle, indent=2)


__all__ = [
    "ConfigStore",
    "DiscoveryConfig",
    "DiscoveryProfile",
    "CLIState",
    "CONFIG_ENV_VAR",
    "CONFIG_FILENAME",
    "STATE_FILENAME",
]
