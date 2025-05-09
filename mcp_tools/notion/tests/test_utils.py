"""Unit tests for utility modules"""
import os
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
from notion_api_mcp.utils.auth import get_auth_headers, load_env_file, validate_config
from notion_api_mcp.utils.formatting import (
    create_rich_text,
    create_block,
    format_date,
    parse_markdown_to_blocks,
    blocks_to_markdown,
    format_rich_text_content,
    BlockType
)
from notion_api_mcp.models import RichTextObject
from notion_api_mcp.models.properties import RichTextContent

# Auth Tests
def test_get_auth_headers():
    """Test authentication header creation"""
    # Test with explicit API key
    headers = get_auth_headers("test-token")
    assert headers["Authorization"] == "Bearer test-token"
    assert headers["Content-Type"] == "application/json"
    assert headers["Notion-Version"] == "2022-06-28"
    
    # Test with env var
    with patch.dict(os.environ, {"NOTION_API_KEY": "env-token"}):
        headers = get_auth_headers()
        assert headers["Authorization"] == "Bearer env-token"
    
    # Test with missing token
    with pytest.raises(ValueError):
        get_auth_headers("")

def test_load_env_file(tmp_path):
    """Test environment file loading"""
    # Create test env file
    env_path = tmp_path / ".env"
    env_path.write_text(
        "NOTION_API_KEY=test-key\n"
        "NOTION_DATABASE_ID=test-db\n"
    )
    
    # Test successful load
    with patch.dict(os.environ, {}, clear=True):  # Clear env vars first
        load_env_file(env_path)
        assert os.getenv("NOTION_API_KEY") == "test-key"
        assert os.getenv("NOTION_DATABASE_ID") == "test-db"
    
    # Test missing file
    with pytest.raises(FileNotFoundError):
        load_env_file(tmp_path / "nonexistent.env")
    
    # Test missing required vars
    bad_env = tmp_path / "bad.env"
    bad_env.write_text("OTHER_VAR=value\n")
    with patch.dict(os.environ, {}, clear=True):  # Clear env vars first
        with pytest.raises(ValueError):
            load_env_file(bad_env)

def test_validate_config():
    """Test configuration validation"""
    # Test valid config
    with patch.dict(os.environ, {
        "NOTION_API_KEY": "test-key",
        "NOTION_DATABASE_ID": "test-db"
    }):
        validate_config()  # Should not raise
    
    # Test missing config
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError) as exc:
            validate_config()
        assert "Missing required configuration" in str(exc.value)
    
    # Test partial config
    with patch.dict(os.environ, {"NOTION_API_KEY": "test-key"}, clear=True):
        with pytest.raises(ValueError) as exc:
            validate_config()
        assert "Missing required configuration" in str(exc.value)

# Formatting Tests
def test_create_rich_text():
    """Test rich text creation"""
    # Basic text
    result = create_rich_text("Simple text")
    assert result == [{
        "type": "text",
        "text": {"content": "Simple text"}
    }]
    
    # Text with link
    result = create_rich_text(
        "Link text",
        link="https://example.com"
    )
    assert result == [{
        "type": "text",
        "text": {
            "content": "Link text",
            "link": {"url": "https://example.com"}
        }
    }]
    
    # Text with annotations
    result = create_rich_text(
        "Formatted text",
        annotations={
            "bold": True,
            "italic": True,
            "code": False
        }
    )
    assert result == [{
        "type": "text",
        "text": {"content": "Formatted text"},
        "annotations": {
            "bold": True,
            "italic": True,
            "code": False
        }
    }]

def test_create_block():
    """Test block creation"""
    # Paragraph block
    result = create_block("Test content", BlockType.PARAGRAPH)
    assert result == {
        "type": BlockType.PARAGRAPH,
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "Test content"}
            }]
        }
    }
    
    # Todo block with extra props
    result = create_block(
        "Todo item",
        BlockType.TO_DO,
        extra_props={"checked": True}
    )
    assert result == {
        "type": BlockType.TO_DO,
        "to_do": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "Todo item"}
            }],
            "checked": True
        }
    }

def test_format_date():
    """Test date formatting"""
    dt = datetime(2025, 1, 15, 14, 30)
    result = format_date(dt)
    assert result == "2025-01-15T14:30:00"

def test_parse_markdown_to_blocks():
    """Test markdown to blocks conversion"""
    markdown = """# Heading 1
## Heading 2
Regular paragraph
- Bullet point
1. Numbered item
[ ] Todo item
[x] Completed todo
```
Code block
```
> Quote"""

    blocks = parse_markdown_to_blocks(markdown)
    
    # Verify block types regardless of count
    block_types = [block["type"] for block in blocks]
    assert BlockType.HEADING_1 in block_types
    assert BlockType.HEADING_2 in block_types
    assert BlockType.PARAGRAPH in block_types
    assert BlockType.BULLETED_LIST in block_types
    assert BlockType.NUMBERED_LIST in block_types
    assert BlockType.TO_DO in block_types
    assert BlockType.QUOTE in block_types

def test_blocks_to_markdown():
    """Test blocks to markdown conversion"""
    blocks = [
        {
            "type": BlockType.HEADING_1,
            "heading_1": {
                "rich_text": [{
                    "text": {"content": "Title"}
                }]
            }
        },
        {
            "type": BlockType.PARAGRAPH,
            "paragraph": {
                "rich_text": [{
                    "text": {"content": "Content"}
                }]
            }
        }
    ]
    
    markdown = blocks_to_markdown(blocks)
    assert markdown == "# Title\n\nContent"

def test_format_rich_text_content():
    """Test rich text content formatting"""
    rich_text = [
        RichTextObject(
            text=RichTextContent(content="First"),
            type="text"
        ),
        RichTextObject(
            text=RichTextContent(content="Second"),
            type="text"
        )
    ]
    
    result = format_rich_text_content(rich_text)
    assert result == "First Second"