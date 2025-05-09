"""Unit tests for MCP tool handlers"""
import os
os.environ['PYTEST_CURRENT_TEST'] = 'test_mode'

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from datetime import datetime

@pytest_asyncio.fixture
async def mock_http_client():
    """Mock httpx client for testing."""
    client = AsyncMock(spec=httpx.AsyncClient)
    
    # Create a mock response
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"object": "page"})
    
    # Make client methods return the mock response
    client.post.return_value = mock_response
    client.patch.return_value = mock_response
    client.get.return_value = mock_response
    
    return client

@pytest_asyncio.fixture(autouse=True)
async def setup_environment(monkeypatch, mock_http_client):
    """Set up test environment"""
    # Mock file operations
    monkeypatch.setattr('pathlib.Path.exists', lambda x: True)
    monkeypatch.setattr('dotenv.load_dotenv', lambda path: True)
    
    # Set test environment variables
    monkeypatch.setenv("NOTION_API_KEY", "test-api-key")
    monkeypatch.setenv("NOTION_DATABASE_ID", "test-db-id")
    monkeypatch.setenv("TEMPLATE_DATABASE_ID", "test-template-db-id")
    
    # Create mock APIs
    mock_pages_api = AsyncMock()
    mock_databases_api = AsyncMock()
    mock_blocks_api = AsyncMock()
    
    # Set up database API responses
    mock_databases_api.get_database = AsyncMock(return_value={
        "id": "test-template-db-id",
        "url": "https://notion.so/test-db",
        "title": [{"text": {"content": "Task Templates"}}],
        "properties": {
            "Name": {"title": {}},
            "Pattern": {"rich_text": {}},
            "Description": {"rich_text": {}}
        }
    })
    
    # Patch the server's global variables and init_clients
    with patch("notion_api_mcp.server.pages_api", mock_pages_api), \
         patch("notion_api_mcp.server.databases_api", mock_databases_api), \
         patch("notion_api_mcp.server.blocks_api", mock_blocks_api), \
         patch("notion_api_mcp.server.http_client", mock_http_client), \
         patch("notion_api_mcp.server.DATABASE_ID", "test-db-id"), \
         patch("notion_api_mcp.server.TEMPLATE_DATABASE_ID", "test-template-db-id"), \
         patch("notion_api_mcp.server.NOTION_API_KEY", "test-api-key"):
        yield

@pytest.mark.asyncio
async def test_create_task_template(monkeypatch):
    """Test task template creation"""
    # Import server after environment is set up
    from notion_api_mcp.server import call_tool, databases_api, pages_api, TEMPLATE_DATABASE_ID
    
    # Set up mock responses
    databases_api.get_database.return_value = {
        "id": TEMPLATE_DATABASE_ID,
        "url": "https://notion.so/test-db",
        "title": [{"text": {"content": "Task Templates"}}]
    }
    
    pages_api.create_page.return_value = {
        "id": "test-page-id",
        "url": "https://notion.so/test-page"
    }
    
    result = await call_tool("create_task_template", {
        "name": "Daily Task",
        "task_pattern": "Daily Task {number}",
        "description_template": "Task for day {number}",
        "default_priority": "medium",
        "default_tags": ["daily", "routine"]
    })
    
    # Verify template database retrieval
    databases_api.get_database.assert_called_once_with(TEMPLATE_DATABASE_ID)
    
    # Verify template page creation
    pages_api.create_page.assert_called_once()
    call_args = pages_api.create_page.call_args[1]
    assert call_args["properties"]["Name"]["title"][0]["text"]["content"] == "Daily Task"
    assert call_args["properties"]["Pattern"]["rich_text"][0]["text"]["content"] == "Daily Task {number}"
    assert call_args["properties"]["Priority"]["select"]["name"] == "medium"
    assert len(call_args["properties"]["Tags"]["multi_select"]) == 2
    
    # Verify MCP response format
    assert len(result) == 1
    assert result[0].type == "text"
    assert "Task template created" in result[0].text
    assert "https://notion.so/test-page" in result[0].text

@pytest.mark.asyncio
async def test_error_handling(monkeypatch):
    """Test error handling in tool calls"""
    from notion_api_mcp.server import call_tool, pages_api
    
    # Test with invalid tool name
    with pytest.raises(ValueError, match="Unknown tool"):
        await call_tool("invalid_tool", {})
    
    # Test with missing required argument
    result = await call_tool("add_todo", {})
    assert len(result) == 1
    assert "error" in result[0].text.lower()
    
    # Test with invalid date format
    result = await call_tool("add_todo", {
        "task": "Test",
        "due_date": "invalid"
    })
    assert len(result) == 1
    assert "Invalid due date format" in result[0].text
    
    # Test API error handling
    pages_api.create_page.side_effect = Exception("API Error")
    
    result = await call_tool("add_todo", {
        "task": "Test Task"
    })
    assert len(result) == 1
    assert "Unexpected error in add_todo" in result[0].text
    assert "API Error" in result[0].text