"""
Tests for Notion block formatting and specialized block types.
Tests rich text formatting, lists, and todo blocks.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import httpx
import structlog

from notion_api_mcp.api.blocks import BlocksAPI

# Import common fixtures
from ..common.conftest import (
    full_access_client,
    readonly_client,
    strip_hyphens,
)

logger = structlog.get_logger()

# Test data constants
RICH_TEXT_BLOCKS = {
    "paragraph": "Basic paragraph text",
    "heading_1": "Main heading",
    "heading_2": "Sub heading",
    "heading_3": "Sub-sub heading",
}

TEXT_ANNOTATIONS = {
    "bold": True,
    "italic": True,
    "strikethrough": False,
    "underline": False,
    "code": False,
    "color": "blue"
}

@pytest_asyncio.fixture
async def mock_client():
    """Mock httpx client for testing."""
    client = AsyncMock(spec=httpx.AsyncClient)
    
    # Create a mock response
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"object": "block"})
    
    # Make client methods return the mock response
    client.post.return_value = mock_response
    client.patch.return_value = mock_response
    client.get.return_value = mock_response
    
    return client

@pytest_asyncio.fixture
async def blocks_api(mock_client):
    """BlocksAPI instance with mocked client."""
    return BlocksAPI(mock_client)

class TestRichTextBlocks:
    """Test rich text block creation and formatting."""
    
    def test_create_basic_paragraph(self, blocks_api):
        """Test creating a basic paragraph block."""
        block = blocks_api.create_rich_text_block("Test paragraph")
        
        assert "paragraph" in block
        assert block["paragraph"]["rich_text"][0]["text"]["content"] == "Test paragraph"
        assert block["paragraph"]["rich_text"][0]["type"] == "text"
    
    def test_create_heading_blocks(self, blocks_api):
        """Test creating different heading blocks."""
        for block_type, content in RICH_TEXT_BLOCKS.items():
            block = blocks_api.create_rich_text_block(content, block_type=block_type)
            
            assert block_type in block
            assert block[block_type]["rich_text"][0]["text"]["content"] == content
    
    def test_create_formatted_text(self, blocks_api):
        """Test creating text with formatting annotations."""
        block = blocks_api.create_rich_text_block(
            "Formatted text",
            annotations=TEXT_ANNOTATIONS
        )
        
        rich_text = block["paragraph"]["rich_text"][0]
        assert rich_text["annotations"]["bold"] is True
        assert rich_text["annotations"]["italic"] is True
        assert rich_text["annotations"]["color"] == "blue"
    
    def test_create_linked_text(self, blocks_api):
        """Test creating text with a link."""
        block = blocks_api.create_rich_text_block(
            "Link text",
            link="https://example.com"
        )
        
        rich_text = block["paragraph"]["rich_text"][0]
        assert rich_text["text"]["link"]["url"] == "https://example.com"

class TestListBlocks:
    """Test list block creation and formatting."""
    
    def test_create_basic_list(self, blocks_api):
        """Test creating a basic bulleted list item."""
        block = blocks_api.create_bulleted_list_block("List item")
        
        assert "bulleted_list_item" in block
        assert block["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "List item"
    
    def test_create_formatted_list(self, blocks_api):
        """Test creating a formatted list item."""
        block = blocks_api.create_bulleted_list_block(
            "Formatted item",
            annotations=TEXT_ANNOTATIONS
        )
        
        rich_text = block["bulleted_list_item"]["rich_text"][0]
        assert rich_text["annotations"]["bold"] is True
        assert rich_text["annotations"]["italic"] is True
        assert rich_text["annotations"]["color"] == "blue"

    @pytest.mark.asyncio
    async def test_nested_list(self, blocks_api):
        """Test creating nested list items."""
        parent = blocks_api.create_bulleted_list_block("Parent item")
        child = blocks_api.create_bulleted_list_block("Child item")
        
        result = await blocks_api.append_children(
            "test-block-id",
            [parent, child]
        )
        
        assert result == {"object": "block"}
        blocks_api._client.patch.assert_called_once_with(
            "blocks/test-block-id/children",
            json={"children": [parent, child]}
        )

class TestTodoBlocks:
    """Test todo block creation and formatting."""
    
    def test_create_basic_todo(self, blocks_api):
        """Test creating a basic todo block."""
        block = blocks_api.create_todo_block("Todo item")
        
        assert "to_do" in block
        assert block["to_do"]["rich_text"][0]["text"]["content"] == "Todo item"
        assert block["to_do"]["checked"] is False
    
    def test_create_checked_todo(self, blocks_api):
        """Test creating a completed todo block."""
        block = blocks_api.create_todo_block("Done item", checked=True)
        
        assert block["to_do"]["checked"] is True
    
    def test_create_formatted_todo(self, blocks_api):
        """Test creating a formatted todo block."""
        block = blocks_api.create_todo_block(
            "Important todo",
            annotations=TEXT_ANNOTATIONS
        )
        
        rich_text = block["to_do"]["rich_text"][0]
        assert rich_text["annotations"]["bold"] is True
        assert rich_text["annotations"]["italic"] is True
        assert rich_text["annotations"]["color"] == "blue"

@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in block formatting operations."""
    
    async def test_invalid_block_type(self, blocks_api):
        """Test error handling with invalid block type."""
        block = blocks_api.create_rich_text_block(
            "Test",
            block_type="invalid_type"
        )
        blocks_api._client.patch.side_effect = httpx.HTTPError("Invalid block type")
        
        with pytest.raises(httpx.HTTPError):
            await blocks_api.append_children("test-id", [block])
    
    async def test_invalid_annotations(self, blocks_api):
        """Test error handling with invalid annotations."""
        block = blocks_api.create_rich_text_block(
            "Test",
            annotations={"invalid": "annotation"}
        )
        blocks_api._client.patch.side_effect = httpx.HTTPError("Invalid annotations")
        
        with pytest.raises(httpx.HTTPError):
            await blocks_api.append_children("test-id", [block])
    
    async def test_invalid_color(self, blocks_api):
        """Test error handling with invalid color."""
        block = blocks_api.create_rich_text_block(
            "Test",
            annotations={"color": "invalid_color"}
        )
        blocks_api._client.patch.side_effect = httpx.HTTPError("Invalid color")
        
        with pytest.raises(httpx.HTTPError):
            await blocks_api.append_children("test-id", [block])