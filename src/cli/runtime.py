"""Runtime helpers shared across Discovery CLI commands."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from .config_store import CLIState, ConfigStore, DiscoveryConfig, DiscoveryProfile
from .exceptions import ConfigNotInitializedError
from .http_client import DiscoveryApiClient


@dataclass
class RuntimeContext:
    """Aggregates configuration, state, and API access."""

    store: ConfigStore
    config: DiscoveryConfig
    profile: DiscoveryProfile
    state: CLIState

    def recent_notebook(self) -> str | None:
        return self.state.get_recent_notebook(self.profile.name)

    def remember_notebook(self, notebook_id: str) -> None:
        self.state.set_recent_notebook(self.profile.name, notebook_id)
        self.store.save_state(self.state)

    def fallback_notebook(self) -> str | None:
        """Get fallback notebook: recent notebook, then default notebook."""
        recent = self.recent_notebook()
        if recent:
            return recent
        return self.profile.default_notebook

    @contextmanager
    def api_client(self, *, timeout: float = 30.0, verbose: bool = False) -> Iterator[DiscoveryApiClient]:
        client = DiscoveryApiClient(self.profile, timeout=timeout, verbose=verbose)
        try:
            yield client
        finally:
            client.close()


def load_runtime(profile_override: str | None = None) -> RuntimeContext:
    store = ConfigStore()
    config = store.load()
    profile = config.get_profile(profile_override)
    state = store.load_state()
    return RuntimeContext(store=store, config=config, profile=profile, state=state)


def load_optional_config() -> ConfigStore:
    return ConfigStore()


__all__ = ["RuntimeContext", "load_runtime", "load_optional_config"]
