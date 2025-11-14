"""Unit tests for CLI config store."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.cli.config_store import CLIState, ConfigStore, DiscoveryConfig, DiscoveryProfile
from src.cli.exceptions import ConfigNotInitializedError


class TestConfigStore:
    """Test ConfigStore functionality."""

    def test_set_default_notebook(self):
        """Test setting default notebook for a profile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ConfigStore(config_home=Path(tmpdir))
            
            # Create initial profile
            profile = DiscoveryProfile(
                name="test",
                url="http://localhost:8000",
                api_key="test-key",
                default_notebook=None,
            )
            store.upsert_profile(profile, make_active=True)
            
            # Set default notebook
            notebook_id = "test-notebook-123"
            config = store.set_default_notebook(notebook_id)
            
            # Verify it was set
            assert config.profiles["test"].default_notebook == notebook_id
            
            # Verify it persists
            config_reloaded = store.load()
            assert config_reloaded.profiles["test"].default_notebook == notebook_id

    def test_set_default_notebook_for_specific_profile(self):
        """Test setting default notebook for a specific profile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ConfigStore(config_home=Path(tmpdir))
            
            # Create two profiles
            profile1 = DiscoveryProfile(
                name="profile1",
                url="http://localhost:8000",
                api_key="key1",
            )
            profile2 = DiscoveryProfile(
                name="profile2",
                url="http://localhost:9000",
                api_key="key2",
            )
            store.upsert_profile(profile1, make_active=True)
            store.upsert_profile(profile2, make_active=False)
            
            # Set default notebook for profile2 (non-active)
            notebook_id = "notebook-456"
            config = store.set_default_notebook(notebook_id, profile_name="profile2")
            
            # Verify only profile2 was updated
            assert config.profiles["profile2"].default_notebook == notebook_id
            assert config.profiles["profile1"].default_notebook is None

    def test_set_default_notebook_profile_not_found(self):
        """Test setting default notebook for non-existent profile raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ConfigStore(config_home=Path(tmpdir))
            
            # Create a profile
            profile = DiscoveryProfile(
                name="test",
                url="http://localhost:8000",
            )
            store.upsert_profile(profile, make_active=True)
            
            # Try to set default notebook for non-existent profile
            with pytest.raises(ConfigNotInitializedError, match="Profile 'nonexistent' does not exist"):
                store.set_default_notebook("notebook-id", profile_name="nonexistent")


class TestCLIState:
    """Test CLIState functionality."""

    def test_recent_notebooks_per_profile(self):
        """Test that recent notebooks are tracked per profile."""
        state = CLIState()
        
        # Set recent notebooks for different profiles
        state.set_recent_notebook("profile1", "notebook-1")
        state.set_recent_notebook("profile2", "notebook-2")
        
        # Verify they're stored separately
        assert state.get_recent_notebook("profile1") == "notebook-1"
        assert state.get_recent_notebook("profile2") == "notebook-2"
        
    def test_get_recent_notebook_not_found(self):
        """Test getting recent notebook for profile with none set."""
        state = CLIState()
        assert state.get_recent_notebook("unknown-profile") is None
