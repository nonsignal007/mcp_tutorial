"""Test authentication utility functions."""
import pytest
from notion_api_mcp.utils.auth import (
    load_env_file,
    get_auth_headers,
    validate_config
)

def test_get_auth_headers():
    """Test auth header generation."""
    headers = get_auth_headers("test_token")
    assert headers["Authorization"] == "Bearer test_token"
    assert headers["Notion-Version"]
    assert headers["Content-Type"] == "application/json"

def test_validate_config(monkeypatch):
    """Test configuration validation."""
    # Valid config
    monkeypatch.setenv("NOTION_API_KEY", "test_key")
    monkeypatch.setenv("NOTION_DATABASE_ID", "test_db")
    validate_config()  # Should not raise
    
    # Missing API key
    monkeypatch.delenv("NOTION_API_KEY")
    with pytest.raises(ValueError, match="NOTION_API_KEY"):
        validate_config()
    
    # Missing database ID
    monkeypatch.setenv("NOTION_API_KEY", "test_key")
    monkeypatch.delenv("NOTION_DATABASE_ID")
    with pytest.raises(ValueError, match="NOTION_DATABASE_ID"):
        validate_config()