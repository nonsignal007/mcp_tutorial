"""Test authentication utilities."""
import os
import pytest
from pathlib import Path
from notion_api_mcp.utils.auth import (
    load_env_file,
    get_auth_headers,
    validate_config
)

@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file."""
    env_file = tmp_path / ".env"
    env_content = """
    NOTION_API_KEY=test_api_key
    NOTION_DATABASE_ID=test_database_id
    """
    env_file.write_text(env_content)
    return env_file

@pytest.fixture
def temp_env_file_missing_vars(tmp_path):
    """Create a temporary .env file with missing variables."""
    env_file = tmp_path / ".env"
    env_content = """
    NOTION_API_KEY=test_api_key
    # Missing NOTION_DATABASE_ID
    """
    env_file.write_text(env_content)
    return env_file

@pytest.fixture
def clean_env():
    """Remove relevant environment variables temporarily."""
    # Store original values
    orig_api_key = os.environ.get("NOTION_API_KEY")
    orig_db_id = os.environ.get("NOTION_DATABASE_ID")
    
    # Remove variables
    if "NOTION_API_KEY" in os.environ:
        del os.environ["NOTION_API_KEY"]
    if "NOTION_DATABASE_ID" in os.environ:
        del os.environ["NOTION_DATABASE_ID"]
    
    yield
    
    # Restore original values
    if orig_api_key is not None:
        os.environ["NOTION_API_KEY"] = orig_api_key
    if orig_db_id is not None:
        os.environ["NOTION_DATABASE_ID"] = orig_db_id

def test_load_env_file(temp_env_file, clean_env):
    """Test loading environment variables from file."""
    load_env_file(temp_env_file)
    assert os.getenv("NOTION_API_KEY") == "test_api_key"
    assert os.getenv("NOTION_DATABASE_ID") == "test_database_id"

def test_load_env_file_missing_vars(temp_env_file_missing_vars, clean_env):
    """Test loading environment file with missing variables."""
    with pytest.raises(ValueError) as exc:
        load_env_file(temp_env_file_missing_vars)
    assert "Missing required environment variables" in str(exc.value)
    assert "NOTION_DATABASE_ID" in str(exc.value)

def test_load_env_file_not_found():
    """Test loading non-existent environment file."""
    with pytest.raises(FileNotFoundError) as exc:
        load_env_file(Path("/nonexistent/.env"))
    assert "No .env file found" in str(exc.value)

def test_get_auth_headers_with_env(clean_env):
    """Test getting auth headers using environment variable."""
    os.environ["NOTION_API_KEY"] = "test_api_key"
    headers = get_auth_headers()
    assert headers["Authorization"] == "Bearer test_api_key"
    assert headers["Content-Type"] == "application/json"
    assert headers["Notion-Version"] == "2022-06-28"

def test_get_auth_headers_with_param():
    """Test getting auth headers using parameter."""
    headers = get_auth_headers(api_key="custom_api_key")
    assert headers["Authorization"] == "Bearer custom_api_key"
    assert headers["Content-Type"] == "application/json"
    assert headers["Notion-Version"] == "2022-06-28"

def test_get_auth_headers_missing_key(clean_env):
    """Test getting auth headers with no API key available."""
    with pytest.raises(ValueError) as exc:
        get_auth_headers()
    assert "No API key provided" in str(exc.value)

def test_validate_config_valid():
    """Test configuration validation with valid config."""
    os.environ["NOTION_API_KEY"] = "test_api_key"
    os.environ["NOTION_DATABASE_ID"] = "test_database_id"
    validate_config()  # Should not raise

def test_validate_config_missing(clean_env):
    """Test configuration validation with missing config."""
    with pytest.raises(ValueError) as exc:
        validate_config()
    assert "Missing required configuration" in str(exc.value)
    assert "NOTION_API_KEY" in str(exc.value)
    assert "NOTION_DATABASE_ID" in str(exc.value)

def test_validate_config_partial(clean_env):
    """Test configuration validation with partial config."""
    os.environ["NOTION_API_KEY"] = "test_api_key"
    with pytest.raises(ValueError) as exc:
        validate_config()
    assert "Missing required configuration" in str(exc.value)
    assert "NOTION_DATABASE_ID" in str(exc.value)
    assert "NOTION_API_KEY" not in str(exc.value)