"""
Tests for subtask functionality in Blocks API.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import httpx

from notion_api_mcp.api.blocks import BlocksAPI

@pytest_asyncio.fixture
async def mock_response():
    """Create a mock response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.raise_for_status = MagicMock()
    response.json = MagicMock(return_value={"object": "block"})
    return response

@pytest_asyncio.fixture
async def mock_client(mock_response):
    """Create mock HTTP client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(return_value=mock_response)
    client.post = AsyncMock(return_value=mock_response)
    client.patch = AsyncMock(return_value=mock_response)
    client.delete = AsyncMock(return_value=mock_response)
    return client

@pytest_asyncio.fixture
async def blocks_api(mock_client):
    """Create BlocksAPI instance with mocked client."""
    return BlocksAPI(mock_client)

@pytest.mark.asyncio
class TestSubtaskCreation:
    """Test subtask creation functionality."""
    
    async def test_create_subtask(self, blocks_api, mock_response):
        """Test creating a subtask under a parent todo."""
        mock_response.json.return_value = {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [{"text": {"content": "Test subtask"}}],
                "checked": False,
                "is_subtask": True
            }
        }
        
        result = await blocks_api.create_subtask(
            "parent-id",
            "Test subtask"
        )
        
        assert result["object"] == "block"
        assert result["type"] == "to_do"
        assert result["to_do"]["is_subtask"] is True
        blocks_api._client.patch.assert_called_once()
    
    async def test_create_subtask_with_formatting(self, blocks_api):
        """Test creating a formatted subtask."""
        annotations = {
            "bold": True,
            "italic": True
        }
        
        await blocks_api.create_subtask(
            "parent-id",
            "Formatted subtask",
            annotations=annotations
        )
        
        # Verify the request included formatting
        call_args = blocks_api._client.patch.call_args
        assert call_args is not None
        children = call_args[1]["json"]["children"]
        assert children[0]["to_do"]["rich_text"][0]["annotations"] == annotations

@pytest.mark.asyncio
class TestSubtaskRetrieval:
    """Test subtask retrieval functionality."""
    
    async def test_get_subtasks(self, blocks_api, mock_response):
        """Test retrieving subtasks of a todo."""
        mock_response.json.return_value = {
            "results": [
                {
                    "type": "to_do",
                    "to_do": {"is_subtask": True, "checked": False}
                },
                {
                    "type": "to_do",
                    "to_do": {"is_subtask": True, "checked": True}
                },
                {
                    "type": "paragraph"  # Should be filtered out
                }
            ]
        }
        
        subtasks = await blocks_api.get_subtasks("parent-id")
        
        assert len(subtasks) == 2
        assert all(t["type"] == "to_do" for t in subtasks)
        assert all(t["to_do"]["is_subtask"] for t in subtasks)
    
    async def test_get_subtasks_empty(self, blocks_api, mock_response):
        """Test retrieving subtasks when none exist."""
        mock_response.json.return_value = {"results": []}
        
        subtasks = await blocks_api.get_subtasks("parent-id")
        
        assert len(subtasks) == 0

@pytest.mark.asyncio
class TestSubtaskStatus:
    """Test subtask status management."""
    
    async def test_update_subtask_status(self, blocks_api):
        """Test updating subtask completion status."""
        await blocks_api.update_subtask_status(
            "subtask-id",
            checked=True
        )
        
        blocks_api._client.patch.assert_called_with(
            "blocks/subtask-id",
            json={"to_do": {"checked": True}}
        )
    
    async def test_update_subtask_updates_parent(self, blocks_api, mock_response):
        """Test parent todo is updated when all subtasks complete."""
        # Mock responses for each API call
        responses = [
            # First call - update subtask
            {"object": "block", "type": "to_do"},
            # Second call - get subtask
            {
                "object": "block",
                "type": "to_do",
                "parent": {"block_id": "parent-id"}
            },
            # Third call - get children
            {
                "object": "list",
                "results": [
                    {
                        "type": "to_do",
                        "to_do": {"checked": True, "is_subtask": True}
                    },
                    {
                        "type": "to_do",
                        "to_do": {"checked": True, "is_subtask": True}
                    }
                ]
            },
            # Fourth call - update parent
            {"object": "block", "type": "to_do"},
            # Fifth call - get updated subtask
            {"object": "block", "type": "to_do"}
        ]
        
        # Create a new mock response for each call
        def get_response(*args, **kwargs):
            response = MagicMock(spec=httpx.Response)
            response.status_code = 200
            response.raise_for_status = MagicMock()
            response.json = MagicMock(side_effect=[responses.pop(0)])
            return response
        
        # Set up mock client calls
        mock_client = AsyncMock()
        mock_client.patch = AsyncMock(side_effect=get_response)
        mock_client.get = AsyncMock(side_effect=get_response)
        blocks_api._client = mock_client
        
        # Execute update
        await blocks_api.update_subtask_status(
            "subtask-id",
            checked=True,
            update_parent=True
        )
        
        # Verify the number and order of calls
        assert mock_client.patch.call_count == 2
        calls = mock_client.patch.call_args_list
        
        # First call should update subtask
        assert calls[0][0][0] == "blocks/subtask-id"
        assert calls[0][1]["json"] == {"to_do": {"checked": True}}
        
        # Second call should update parent
        assert calls[1][0][0] == "blocks/parent-id"
        assert calls[1][1]["json"] == {"to_do": {"checked": True}}
    
    async def test_update_subtask_error_handling(self, blocks_api):
        """Test error handling in status updates."""
        blocks_api._client.patch.side_effect = httpx.HTTPError("API Error")
        
        with pytest.raises(httpx.HTTPError):
            await blocks_api.update_subtask_status(
                "subtask-id",
                checked=True
            )