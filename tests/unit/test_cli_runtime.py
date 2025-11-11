"""Unit tests for CLI runtime context."""

from __future__ import annotations

import tempfile
from pathlib import Path

from src.cli.config_store import CLIState, ConfigStore, DiscoveryConfig, DiscoveryProfile
from src.cli.runtime import RuntimeContext


class TestRuntimeContext:
    """Test RuntimeContext functionality."""

    def test_fallback_notebook_returns_recent_when_available(self):
        """Test that fallback_notebook returns recent notebook when available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ConfigStore(config_home=Path(tmpdir))
            
            # Create profile with default notebook
            profile = DiscoveryProfile(
                name="test",
                url="http://localhost:8000",
                default_notebook="default-notebook-123",
            )
            config = DiscoveryConfig(active_profile="test", profiles={"test": profile})
            store.save(config)
            
            # Create state with recent notebook
            state = CLIState()
            state.set_recent_notebook("test", "recent-notebook-456")
            
            # Create runtime context
            runtime = RuntimeContext(
                store=store,
                config=config,
                profile=profile,
                state=state,
            )
            
            # fallback_notebook should return recent, not default
            assert runtime.fallback_notebook() == "recent-notebook-456"

    def test_fallback_notebook_returns_default_when_no_recent(self):
        """Test that fallback_notebook returns default notebook when no recent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ConfigStore(config_home=Path(tmpdir))
            
            # Create profile with default notebook
            profile = DiscoveryProfile(
                name="test",
                url="http://localhost:8000",
                default_notebook="default-notebook-123",
            )
            config = DiscoveryConfig(active_profile="test", profiles={"test": profile})
            store.save(config)
            
            # Create state without recent notebook
            state = CLIState()
            
            # Create runtime context
            runtime = RuntimeContext(
                store=store,
                config=config,
                profile=profile,
                state=state,
            )
            
            # fallback_notebook should return default
            assert runtime.fallback_notebook() == "default-notebook-123"

    def test_fallback_notebook_returns_none_when_none_available(self):
        """Test that fallback_notebook returns None when no notebooks are set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ConfigStore(config_home=Path(tmpdir))
            
            # Create profile without default notebook
            profile = DiscoveryProfile(
                name="test",
                url="http://localhost:8000",
                default_notebook=None,
            )
            config = DiscoveryConfig(active_profile="test", profiles={"test": profile})
            store.save(config)
            
            # Create state without recent notebook
            state = CLIState()
            
            # Create runtime context
            runtime = RuntimeContext(
                store=store,
                config=config,
                profile=profile,
                state=state,
            )
            
            # fallback_notebook should return None
            assert runtime.fallback_notebook() is None

    def test_remember_notebook_saves_state(self):
        """Test that remember_notebook saves state to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ConfigStore(config_home=Path(tmpdir))
            
            # Create profile
            profile = DiscoveryProfile(
                name="test",
                url="http://localhost:8000",
            )
            config = DiscoveryConfig(active_profile="test", profiles={"test": profile})
            store.save(config)
            
            # Create state
            state = CLIState()
            
            # Create runtime context
            runtime = RuntimeContext(
                store=store,
                config=config,
                profile=profile,
                state=state,
            )
            
            # Remember a notebook
            runtime.remember_notebook("test-notebook-789")
            
            # Verify it was saved by loading fresh state
            loaded_state = store.load_state()
            assert loaded_state.get_recent_notebook("test") == "test-notebook-789"
