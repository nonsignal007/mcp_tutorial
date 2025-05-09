"""
Integration tests for Notion blocks API.
Tests block creation, formatting, and nesting with real API calls.
"""
import os
import pytest
import pytest_asyncio
import httpx
import structlog
from datetime import datetime

from notion_api_mcp.api.blocks import BlocksAPI
from notion_api_mcp.api.pages import PagesAPI

# Import common fixtures
from ..common.conftest import (
    full_access_client,
    readonly_client,
    strip_hyphens,
)

logger = structlog.get_logger()

@pytest_asyncio.fixture
async def test_page(full_access_client):
    """Create a test page for block operations."""
    parent_id = strip_hyphens(os.getenv("NOTION_PARENT_PAGE_ID"))
    pages_api = PagesAPI(full_access_client)
    
    # Create test page
    page = await pages_api.create_page(
        parent_id,
        properties={"title": {"title": [{"text": {"content": f"Test Page {os.urandom(4).hex()}"}}]}},
        is_database=False
    )
    
    page_id = page["id"]
    logger.info("test_page_created", page_id=page_id)
    
    yield page_id
    
    # Clean up
    try:
        await pages_api.archive_page(page_id)
    except Exception as e:
        logger.error("cleanup_error", page_id=page_id, error=str(e))

@pytest.mark.integration
class TestBlockFormatting:
    """Test block formatting with real API calls."""
    
    async def test_rich_text_blocks(self, full_access_client, test_page):
        """Test creating various rich text blocks."""
        blocks_api = BlocksAPI(full_access_client)
        
        # Create different types of text blocks
        blocks = [
            blocks_api.create_rich_text_block(
                "Heading 1 Test",
                block_type="heading_1"
            ),
            blocks_api.create_rich_text_block(
                "Heading 2 Test",
                block_type="heading_2"
            ),
            blocks_api.create_rich_text_block(
                "Regular paragraph",
                block_type="paragraph"
            )
        ]
        
        response = await blocks_api.append_children(test_page, blocks)
        assert response is not None
        assert "results" in response
        assert len(response["results"]) == 3
        
        # Verify block types
        results = response["results"]
        assert results[0]["type"] == "heading_1"
        assert results[1]["type"] == "heading_2"
        assert results[2]["type"] == "paragraph"

    async def test_formatted_text(self, full_access_client, test_page):
        """Test text with various formatting options."""
        blocks_api = BlocksAPI(full_access_client)
        
        block = blocks_api.create_rich_text_block(
            "Formatted Text",
            annotations={
                "bold": True,
                "italic": True,
                "color": "blue"
            }
        )
        
        response = await blocks_api.append_children(test_page, [block])
        assert response is not None
        assert "results" in response
        
        result = response["results"][0]
        annotations = result["paragraph"]["rich_text"][0]["annotations"]
        assert annotations["bold"] is True
        assert annotations["italic"] is True
        assert annotations["color"] == "blue"

    async def test_linked_text(self, full_access_client, test_page):
        """Test text with links."""
        blocks_api = BlocksAPI(full_access_client)
        
        # Test URLs with and without trailing slashes
        test_urls = [
            "https://example.com",
            "https://example.com/",
            "https://example.com/path",
            "https://example.com/path/"
        ]
        
        blocks = [
            blocks_api.create_rich_text_block(
                f"Link {i+1}",
                link=url
            )
            for i, url in enumerate(test_urls)
        ]
        
        response = await blocks_api.append_children(test_page, blocks)
        assert response is not None
        assert "results" in response
        assert len(response["results"]) == len(test_urls)
        
        # Verify all links are properly set
        for i, result in enumerate(response["results"]):
            link = result["paragraph"]["rich_text"][0]["text"]["link"]
            assert "url" in link
            # Verify URL is present, exact format handled by Notion API
            assert link["url"].startswith("https://example.com")

@pytest.mark.integration
class TestListOperations:
    """Test list creation and nesting."""
    
    async def test_bulleted_list(self, full_access_client, test_page):
        """Test creating bulleted lists."""
        blocks_api = BlocksAPI(full_access_client)
        
        blocks = [
            blocks_api.create_bulleted_list_block("Item 1"),
            blocks_api.create_bulleted_list_block("Item 2"),
            blocks_api.create_bulleted_list_block(
                "Item 3",
                annotations={"bold": True}
            )
        ]
        
        response = await blocks_api.append_children(test_page, blocks)
        assert response is not None
        assert "results" in response
        assert len(response["results"]) == 3
        
        # Verify list items
        results = response["results"]
        for result in results:
            assert result["type"] == "bulleted_list_item"
        
        # Verify formatted item
        assert results[2]["bulleted_list_item"]["rich_text"][0]["annotations"]["bold"] is True

    async def test_todo_list(self, full_access_client, test_page):
        """Test creating todo lists."""
        blocks_api = BlocksAPI(full_access_client)
        
        blocks = [
            blocks_api.create_todo_block("Task 1"),
            blocks_api.create_todo_block("Task 2", checked=True),
            blocks_api.create_todo_block(
                "Task 3",
                annotations={"color": "red"}
            )
        ]
        
        response = await blocks_api.append_children(test_page, blocks)
        assert response is not None
        assert "results" in response
        assert len(response["results"]) == 3
        
        results = response["results"]
        # Verify todo states
        assert results[0]["to_do"]["checked"] is False
        assert results[1]["to_do"]["checked"] is True
        # Verify formatting
        assert results[2]["to_do"]["rich_text"][0]["annotations"]["color"] == "red"

@pytest.mark.integration
class TestBlockOperations:
    """Test block manipulation operations."""
    
    async def test_block_children(self, full_access_client, test_page):
        """Test retrieving block children."""
        blocks_api = BlocksAPI(full_access_client)
        
        # Add some blocks
        blocks = [
            blocks_api.create_rich_text_block("Parent Block"),
            blocks_api.create_bulleted_list_block("Child 1"),
            blocks_api.create_bulleted_list_block("Child 2")
        ]
        
        await blocks_api.append_children(test_page, blocks)
        
        # Get children
        response = await blocks_api.get_block_children(test_page)
        assert response is not None
        assert "results" in response
        assert len(response["results"]) == 3

    async def test_update_block(self, full_access_client, test_page):
        """Test updating block content."""
        blocks_api = BlocksAPI(full_access_client)
        
        # Create initial block
        block = blocks_api.create_rich_text_block("Initial Text")
        response = await blocks_api.append_children(test_page, [block])
        block_id = response["results"][0]["id"]
        
        # Update block
        updated_content = {
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": "Updated Text"}
                }]
            }
        }
        
        response = await blocks_api.update_block(block_id, updated_content)
        assert response is not None
        assert response["paragraph"]["rich_text"][0]["text"]["content"] == "Updated Text"

@pytest.mark.integration
class TestErrorHandling:
    """Test error handling with real API calls."""
    
    async def test_invalid_block_id(self, full_access_client):
        """Test handling invalid block ID."""
        blocks_api = BlocksAPI(full_access_client)
        
        with pytest.raises(httpx.HTTPError) as exc_info:
            await blocks_api.get_block("invalid-id")
        assert exc_info.value.response.status_code in (400, 404)

    async def test_invalid_parent(self, full_access_client):
        """Test handling invalid parent ID."""
        blocks_api = BlocksAPI(full_access_client)
        
        block = blocks_api.create_rich_text_block("Test")
        with pytest.raises(httpx.HTTPError) as exc_info:
            await blocks_api.append_children("invalid-parent-id", [block])
        assert exc_info.value.response.status_code in (400, 404)

    async def test_readonly_access(self, readonly_client, test_page):
        """Test operations with readonly access."""
        blocks_api = BlocksAPI(readonly_client)
        
        block = blocks_api.create_rich_text_block("Test")
        with pytest.raises(httpx.HTTPError) as exc_info:
            await blocks_api.append_children(test_page, [block])
        assert exc_info.value.response.status_code == 403