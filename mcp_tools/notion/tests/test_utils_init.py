"""Test utils package initialization and configuration."""
import pytest
from notion_api_mcp.utils import (
    # Auth utilities
    load_env_file,
    get_auth_headers,
    validate_config,
    
    # Formatting utilities
    create_rich_text,
    create_block,
    format_date,
    parse_markdown_to_blocks,
    blocks_to_markdown,
    format_rich_text_content,
    
    # Configuration
    RETRY_CONFIG,
    RATE_LIMITS,
    HTTP_CONFIG
)

def test_retry_config():
    """Test retry configuration values."""
    assert isinstance(RETRY_CONFIG, dict)
    assert RETRY_CONFIG["max_retries"] == 3
    assert RETRY_CONFIG["min_delay"] == 1
    assert RETRY_CONFIG["max_delay"] == 10
    assert RETRY_CONFIG["exponential_base"] == 2

def test_rate_limits():
    """Test rate limiting configuration."""
    assert isinstance(RATE_LIMITS, dict)
    assert RATE_LIMITS["max_requests_per_second"] == 3
    assert RATE_LIMITS["max_requests_per_minute"] == 90

def test_http_config():
    """Test HTTP client configuration."""
    assert isinstance(HTTP_CONFIG, dict)
    assert HTTP_CONFIG["timeout"] == 30.0
    assert HTTP_CONFIG["max_keepalive_connections"] == 5
    assert HTTP_CONFIG["max_connections"] == 10
    assert HTTP_CONFIG["retry_config"] == RETRY_CONFIG

def test_auth_exports():
    """Test auth utility exports."""
    assert callable(load_env_file)
    assert callable(get_auth_headers)
    assert callable(validate_config)

def test_formatting_exports():
    """Test formatting utility exports."""
    assert callable(create_rich_text)
    assert callable(create_block)
    assert callable(format_date)
    assert callable(parse_markdown_to_blocks)
    assert callable(blocks_to_markdown)
    assert callable(format_rich_text_content)

def test_config_relationships():
    """Test relationships between configurations."""
    # Verify retry config is properly nested in HTTP config
    assert HTTP_CONFIG["retry_config"] is RETRY_CONFIG
    
    # Verify rate limits are reasonable (per-minute >= per-second)
    assert RATE_LIMITS["max_requests_per_minute"] >= RATE_LIMITS["max_requests_per_second"]
    
    # Verify retry delays are properly ordered
    assert RETRY_CONFIG["min_delay"] <= RETRY_CONFIG["max_delay"]

def test_config_types():
    """Test configuration value types."""
    # Retry config
    assert isinstance(RETRY_CONFIG["max_retries"], int)
    assert isinstance(RETRY_CONFIG["min_delay"], (int, float))
    assert isinstance(RETRY_CONFIG["max_delay"], (int, float))
    assert isinstance(RETRY_CONFIG["exponential_base"], (int, float))
    
    # Rate limits
    assert isinstance(RATE_LIMITS["max_requests_per_second"], int)
    assert isinstance(RATE_LIMITS["max_requests_per_minute"], int)
    
    # HTTP config
    assert isinstance(HTTP_CONFIG["timeout"], float)
    assert isinstance(HTTP_CONFIG["max_keepalive_connections"], int)
    assert isinstance(HTTP_CONFIG["max_connections"], int)
    assert isinstance(HTTP_CONFIG["retry_config"], dict)