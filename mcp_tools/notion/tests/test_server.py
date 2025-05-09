"""Tests for the Notion MCP server implementation."""

import os
os.environ['PYTEST_CURRENT_TEST'] = 'test_mode'

import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from typing import Dict, Any

from notion_api_mcp.server import NotionServer, ServerConfig, ErrorCode, McpError
from mcp.server.fastmcp.exceptions import ToolError

@pytest_asyncio.fixture
async def mock_http_client():
    """Mock httpx client for testing."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.is_closed = False
    
    # Create a mock response
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"results": []})
    
    # Make client methods return the mock response
    client.post.return_value = mock_response
    client.patch.return_value = mock_response
    client.get.return_value = mock_response
    
    return client

@pytest_asyncio.fixture
async def mock_server(mock_http_client):
    """Create a test server instance with mocked components."""
    config = ServerConfig(
        NOTION_API_KEY="test-api-key",
        NOTION_DATABASE_ID="test-db-id",
        NOTION_PARENT_PAGE_ID="test-parent-id"
    )
    server = NotionServer(config)
    
    # Replace client with mock
    server.client = mock_http_client
    
    # Create mock APIs
    server.pages_api = AsyncMock()
    server.databases_api = AsyncMock()
    server.blocks_api = AsyncMock()
    
    return server

@pytest_asyncio.fixture
async def mock_search_response():
    """Mock search response data"""
    return {
        "results": [
            {
                "properties": {
                    "Task": {
                        "title": [{"text": {"content": "Test todo 1"}}]
                    },
                    "Status": {
                        "select": {"name": "In Progress"}
                    },
                    "Priority": {
                        "select": {"name": "high"}
                    }
                },
                "url": "https://notion.so/test-todo-1"
            },
            {
                "properties": {
                    "Task": {
                        "title": [{"text": {"content": "Test todo 2"}}]
                    },
                    "Status": {
                        "select": {"name": "Not Started"}
                    },
                    "Priority": {
                        "select": {"name": "medium"}
                    }
                },
                "url": "https://notion.so/test-todo-2"
            }
        ],
        "has_more": True,
        "next_cursor": "cursor123"
    }

@pytest.mark.asyncio
async def test_server_initialization():
    """Test server initialization with config"""
    config = ServerConfig(
        NOTION_API_KEY="test-api-key",
        NOTION_DATABASE_ID="test-db-id",
        NOTION_PARENT_PAGE_ID="test-parent-id"
    )
    server = NotionServer(config)
    
    assert server._config.api_key == "test-api-key"
    assert server._config.database_id == "test-db-id"
    assert server._config.parent_page_id == "test-parent-id"
    assert server.app is not None

@pytest.mark.asyncio
async def test_server_from_env(monkeypatch):
    """Test server initialization from environment"""
    monkeypatch.setenv("NOTION_API_KEY", "test-api-key")
    monkeypatch.setenv("NOTION_DATABASE_ID", "test-db-id")
    monkeypatch.setenv("NOTION_PARENT_PAGE_ID", "test-parent-id")
    
    config = ServerConfig.from_env()
    server = NotionServer(config)
    
    assert server._config.api_key == "test-api-key"
    assert server._config.database_id == "test-db-id"
    assert server._config.parent_page_id == "test-parent-id"

@pytest.mark.asyncio
async def test_add_todo_handler(mock_server):
    """Test adding a todo"""
    # Set up mock response
    mock_server.pages_api.create_todo_properties.return_value = {
        "Task": {"title": [{"text": {"content": "Test todo"}}]},
        "Status": {"select": {"name": "Not Started"}}
    }
    mock_server.pages_api.create_page.return_value = {
        "id": "test-page-id",
        "url": "https://notion.so/test-todo"
    }
    
    # Call the tool through FastMCP
    result = await mock_server.app.call_tool("add_todo", {
        "task": "Test todo",
        "description": "Test description",
        "priority": "high"
    })
    
    # Parse JSON response
    import json
    response = json.loads(result[0].text)
    
    # Verify response
    assert response["id"] == "test-page-id"
    assert response["url"] == "https://notion.so/test-todo"
    
    # Verify API calls
    mock_server.pages_api.create_todo_properties.assert_called_once()
    mock_server.pages_api.create_page.assert_called_once()

@pytest.mark.asyncio
async def test_search_todos_handler(mock_server, mock_search_response):
    """Test searching todos"""
    # Set up mock response
    mock_server.databases_api.query_database.return_value = mock_search_response
    mock_server.databases_api.create_search_filter.return_value = {
        "property": "description",
        "rich_text": {"contains": "test"}
    }
    mock_server.databases_api.create_sort.return_value = {
        "property": "due_date",
        "direction": "descending"
    }
    
    # Call the tool through FastMCP
    result = await mock_server.app.call_tool("search_todos", {
        "query": "test",
        "property_name": "description",
        "sort_by": "due_date",
        "sort_direction": "descending"
    })
    
    # Parse JSON response
    import json
    response = json.loads(result[0].text)
    
    # Verify response format
    assert len(response["results"]) == 2
    assert response["results"][0]["properties"]["Task"]["title"][0]["text"]["content"] == "Test todo 1"
    assert response["results"][1]["properties"]["Task"]["title"][0]["text"]["content"] == "Test todo 2"
    assert response["has_more"] is True
    assert response["next_cursor"] == "cursor123"
    
    # Verify API calls
    mock_server.databases_api.query_database.assert_called_once()
    mock_server.databases_api.create_search_filter.assert_called_once()

@pytest.mark.asyncio
async def test_search_todos_no_results_handler(mock_server):
    """Test search behavior when no results are found"""
    # Set up mock response
    mock_server.databases_api.query_database.return_value = {"results": []}
    
    # Call the tool through FastMCP
    result = await mock_server.app.call_tool("search_todos", {
        "query": "nonexistent"
    })
    
    # Parse JSON response
    import json
    response = json.loads(result[0].text)
    
    assert len(response["results"]) == 0

@pytest.mark.asyncio
async def test_search_todos_error_handler(mock_server):
    """Test error handling in search"""
    # Set up mock error
    mock_server.databases_api.query_database.side_effect = httpx.HTTPStatusError(
        "API Error",
        request=MagicMock(),
        response=MagicMock(status_code=401)
    )
    
    # Call the tool through FastMCP
    with pytest.raises(ToolError) as exc_info:
        await mock_server.app.call_tool("search_todos", {
            "query": "test"
        })
    assert "Invalid authentication token" in str(exc_info.value)

@pytest.mark.asyncio
async def test_invalid_date_format_handler(mock_server):
    """Test error handling for invalid date format"""
    with pytest.raises(ToolError) as exc_info:
        await mock_server.app.call_tool("add_todo", {
            "task": "Test todo",
            "due_date": "invalid-date"
        })
    assert "Invalid due date format" in str(exc_info.value)

@pytest.mark.asyncio
async def test_tool_registration(mock_server):
    """Test that tools are properly registered with FastMCP"""
    tools = await mock_server.app.list_tools()
    tool_names = [tool.name for tool in tools]
    
    assert "add_todo" in tool_names
    assert "search_todos" in tool_names