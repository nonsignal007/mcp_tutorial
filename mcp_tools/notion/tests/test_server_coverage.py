import os
import sys
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from notion_api_mcp.api.databases import DatabasesAPI
from notion_api_mcp.api.blocks import BlocksAPI
from notion_api_mcp.api.pages import PagesAPI

# Set up test environment
os.environ['PYTEST_CURRENT_TEST'] = 'test_mode'
os.environ['NOTION_API_KEY'] = 'test_api_key'
os.environ['NOTION_DATABASE_ID'] = 'test_database_id'

@pytest.fixture(autouse=True)
def setup_environment(monkeypatch):
    """Set up test environment and patch imports"""
    monkeypatch.setattr('pathlib.Path.exists', lambda x: True)
    monkeypatch.setattr('dotenv.load_dotenv', lambda path: True)
    
    # Patch httpx.AsyncClient before importing server
    async def mock_aclose():
        pass
    
    mock_client = AsyncMock()
    mock_client.aclose = mock_aclose
    monkeypatch.setattr('httpx.AsyncClient', lambda **kwargs: mock_client)
    
    if 'notion_api_mcp.server' in sys.modules:
        del sys.modules['notion_api_mcp.server']

@pytest_asyncio.fixture
async def mock_response():
    """Create a mock response with proper async methods."""
    response = AsyncMock()
    response.status_code = 200
    response.raise_for_status = AsyncMock()
    response.json = AsyncMock(return_value={
        "id": "test-db-id",
        "url": "https://notion.so/test-db",
        "title": [{"text": {"content": "Test Database"}}],
        "properties": {"Name": {"title": {}}}
    })
    return response

@pytest_asyncio.fixture
async def mock_client(mock_response):
    """Mock httpx client for testing."""
    client = AsyncMock(spec=httpx.AsyncClient)
    
    # Create AsyncMock methods
    client.post = AsyncMock(return_value=mock_response)
    client.get = AsyncMock(return_value=mock_response)
    client.patch = AsyncMock(return_value=mock_response)
    client.delete = AsyncMock(return_value=mock_response)
    
    # Mock the client attributes
    client.base_url = "https://api.notion.com/v1"
    client.headers = {
        "Authorization": "Bearer test_api_key",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    return client

@pytest_asyncio.fixture
async def databases_api(mock_client):
    """DatabasesAPI instance with mocked client."""
    return DatabasesAPI(mock_client)

@pytest_asyncio.fixture
async def blocks_api(mock_client):
    """BlocksAPI instance with mocked client."""
    return BlocksAPI(mock_client)

@pytest_asyncio.fixture
async def pages_api(mock_client):
    """PagesAPI instance with mocked client."""
    return PagesAPI(mock_client)

@pytest_asyncio.fixture(autouse=True)
async def mock_apis(monkeypatch, mock_client, mock_response):
    """Set up mock APIs and patch them into server module."""
    # Create mock APIs
    mock_databases_api = AsyncMock()
    mock_databases_api.create_database = AsyncMock(return_value={
        "id": "test-db-id",
        "url": "https://notion.so/test-db",
        "title": [{"text": {"content": "Test Database"}}]
    })
    
    # Patch at method level
    monkeypatch.setattr(
        "notion_api_mcp.api.databases.DatabasesAPI.create_database",
        mock_databases_api.create_database
    )
    
    return mock_databases_api, None, None

@pytest.mark.asyncio
class TestDatabaseManagement:
    """Test database management functionality"""

    async def test_create_database(self, mock_apis):
        """Test database creation"""
        from notion_api_mcp.server import call_tool
        
        mock_databases_api, _, _ = mock_apis
        
        result = await call_tool("create_database", {
            "parent_page_id": "test-parent",
            "title": "Test Database",
            "properties": {"Name": {"title": {}}}
        })
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "✅" in result[0].text
        
        # Verify create_database was called with correct arguments
        mock_databases_api.create_database.assert_called_once_with(
            parent_page_id="test-parent",
            title="Test Database",
            properties={"Name": {"title": {}}}
        )