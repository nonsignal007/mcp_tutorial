"""Test blocks API module initialization and sync methods."""
import httpx
import pytest
from notion_api_mcp.api.blocks import BlocksAPI

def test_blocks_api_init():
    """Test BlocksAPI initialization."""
    client = httpx.AsyncClient()
    api = BlocksAPI(client=client)
    assert api._client == client

def test_create_rich_text_block():
    """Test creating rich text block objects."""
    api = BlocksAPI(client=httpx.AsyncClient())
    
    # Basic paragraph
    block = api.create_rich_text_block("Test content")
    assert block["paragraph"]["rich_text"][0]["text"]["content"] == "Test content"
    
    # With annotations
    block = api.create_rich_text_block(
        "Test content",
        annotations={"bold": True}
    )
    assert block["paragraph"]["rich_text"][0]["annotations"]["bold"] is True
    
    # With link
    block = api.create_rich_text_block(
        "Test content",
        link="https://example.com"
    )
    assert block["paragraph"]["rich_text"][0]["text"]["link"]["url"] == "https://example.com"

def test_create_todo_block():
    """Test creating todo block objects."""
    api = BlocksAPI(client=httpx.AsyncClient())
    
    # Unchecked todo
    block = api.create_todo_block("Test todo")
    assert block["to_do"]["rich_text"][0]["text"]["content"] == "Test todo"
    assert block["to_do"]["checked"] is False
    
    # Checked todo with annotations
    block = api.create_todo_block(
        "Test todo",
        checked=True,
        annotations={"italic": True}
    )
    assert block["to_do"]["checked"] is True
    assert block["to_do"]["rich_text"][0]["annotations"]["italic"] is True