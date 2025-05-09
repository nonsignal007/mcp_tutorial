"""
Basic CRUD operation tests for Notion Blocks API.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import httpx

from notion_api_mcp.api.blocks import BlocksAPI

@pytest_asyncio.fixture
async def mock_response():
    """Create a mock response with proper async methods."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.raise_for_status = MagicMock()  # Regular method
    response.json = MagicMock(return_value={"object": "block"})  # Regular method
    return response

@pytest_asyncio.fixture
async def mock_client(mock_response):
    """Mock httpx client for testing."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(return_value=mock_response)
    client.patch = AsyncMock(return_value=mock_response)
    client.delete = AsyncMock(return_value=mock_response)
    return client

@pytest_asyncio.fixture
async def blocks_api(mock_client):
    """BlocksAPI instance with mocked client."""
    return BlocksAPI(mock_client)

@pytest.mark.asyncio
class TestBlockOperations:
    """Test block manipulation operations."""

    async def test_get_block(self, blocks_api, mock_response):
        """Test retrieving a block."""
        result = await blocks_api.get_block("test-block-id")
        
        assert result == {"object": "block"}
        blocks_api._client.get.assert_called_once_with(
            "blocks/test-block-id"
        )

    async def test_update_block(self, blocks_api, mock_response):
        """Test updating a block."""
        content = {"paragraph": {"text": "Updated content"}}
        result = await blocks_api.update_block("test-block-id", content)
        
        assert result == {"object": "block"}
        blocks_api._client.patch.assert_called_once_with(
            "blocks/test-block-id",
            json=content
        )

    async def test_delete_block(self, blocks_api, mock_response):
        """Test deleting a block."""
        result = await blocks_api.delete_block("test-block-id")
        
        assert result == {"object": "block"}
        blocks_api._client.delete.assert_called_once_with(
            "blocks/test-block-id"
        )

    async def test_get_block_children(self, blocks_api, mock_response):
        """Test retrieving block children."""
        result = await blocks_api.get_block_children("test-block-id")
        
        assert result == {"object": "block"}
        blocks_api._client.get.assert_called_once_with(
            "blocks/test-block-id/children",
            params={"page_size": 100}
        )

    async def test_append_children(self, blocks_api, mock_response):
        """Test appending block children."""
        children = [
            {"paragraph": {"text": "Child block 1"}},
            {"paragraph": {"text": "Child block 2"}}
        ]
        result = await blocks_api.append_children("test-block-id", children)
        
        assert result == {"object": "block"}
        blocks_api._client.patch.assert_called_once_with(
            "blocks/test-block-id/children",
            json={"children": children}
        )

@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in block operations."""

    async def test_get_block_error(self, blocks_api):
        """Test error handling in get_block."""
        blocks_api._client.get.side_effect = httpx.HTTPError("API Error")
        
        with pytest.raises(httpx.HTTPError):
            await blocks_api.get_block("test-id")

    async def test_update_block_error(self, blocks_api):
        """Test error handling in update_block."""
        blocks_api._client.patch.side_effect = httpx.HTTPError("API Error")
        
        with pytest.raises(httpx.HTTPError):
            await blocks_api.update_block("test-id", {})

    async def test_delete_block_error(self, blocks_api):
        """Test error handling in delete_block."""
        blocks_api._client.delete.side_effect = httpx.HTTPError("API Error")
        
        with pytest.raises(httpx.HTTPError):
            await blocks_api.delete_block("test-id")

    async def test_get_block_children_error(self, blocks_api):
        """Test error handling in get_block_children."""
        blocks_api._client.get.side_effect = httpx.HTTPError("API Error")
        
        with pytest.raises(httpx.HTTPError):
            await blocks_api.get_block_children("test-id")

    async def test_append_children_error(self, blocks_api):
        """Test error handling in append_children."""
        blocks_api._client.patch.side_effect = httpx.HTTPError("API Error")
        
        with pytest.raises(httpx.HTTPError):
            await blocks_api.append_children("test-id", [])