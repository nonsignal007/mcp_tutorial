"""
Permission and authentication tests for Notion Blocks API.
Tests access control, inheritance, and auth requirements.
"""
import os
import pytest
import pytest_asyncio
import httpx
import structlog
from unittest.mock import AsyncMock, MagicMock
from notion_api_mcp.api.blocks import BlocksAPI
from notion_api_mcp.api.pages import PagesAPI

# Import common fixtures
from ..common.conftest import (
    full_access_client,
    readonly_client,
    invalid_client,
    strip_hyphens,
    format_page_url,
)

logger = structlog.get_logger()

@pytest_asyncio.fixture
async def shared_test_page(full_access_client):
    """Create a test page with blocks under the pre-shared parent page."""
    parent_id = strip_hyphens(os.getenv("NOTION_PARENT_PAGE_ID"))
    pages_api = PagesAPI(full_access_client)
    
    # Create test page with content blocks
    test_page = await pages_api.create_page(
        parent_id=parent_id,
        properties={
            "title": [{
                "type": "text",
                "text": {"content": "Block Test Page"}
            }]
        },
        children=[
            {
                "paragraph": {
                    "rich_text": [{
                        "text": {"content": "Test paragraph block"}
                    }]
                }
            },
            {
                "heading_2": {
                    "rich_text": [{
                        "text": {"content": "Test heading block"}
                    }]
                }
            }
        ],
        is_database=False
    )
    
    page_id = test_page["id"]
    logger.info("test_page_created", page_id=page_id, url=format_page_url(page_id))
    
    yield page_id
    
    # Clean up after tests
    await pages_api.archive_page(page_id)

@pytest_asyncio.fixture
async def shared_test_block(full_access_client, shared_test_page):
    """Create a test block that inherits permissions from parent page."""
    blocks_api = BlocksAPI(full_access_client)
    
    # Create test block
    response = await blocks_api.append_children(
        shared_test_page,
        [{
            "paragraph": {
                "rich_text": [{
                    "text": {"content": "Permission test block"}
                }]
            }
        }]
    )
    
    block_id = response["results"][0]["id"]
    logger.info("test_block_created", block_id=block_id)
    
    yield block_id
    
    # Clean up after tests
    try:
        await blocks_api.delete_block(block_id)
    except Exception as e:
        logger.error("cleanup_error", block_id=block_id, error=str(e))

@pytest.mark.integration
@pytest.mark.asyncio
async def test_permission_inheritance(full_access_client, readonly_client, shared_test_page):
    """Test that blocks inherit permissions from parent page.
    
    This test verifies that blocks created under a shared page
    automatically inherit access permissions, eliminating the need for
    manual sharing.
    
    The test:
    1. Creates blocks under a shared page
    2. Verifies both integrations can access the blocks
    3. Tests block operations with appropriate permissions
    """
    # Create block with full access
    full_access_api = BlocksAPI(full_access_client)
    response = await full_access_api.append_children(
        shared_test_page,
        [{
            "paragraph": {
                "rich_text": [{
                    "text": {"content": "Inheritance test block"}
                }]
            }
        }]
    )
    block_id = response["results"][0]["id"]
    logger.info("block_created", block_id=block_id)
    
    # Verify read-only access without manual sharing
    readonly_api = BlocksAPI(readonly_client)
    response = await readonly_api.get_block(block_id)
    assert response is not None
    assert "id" in response
    logger.info("readonly_access_verified")
    
    # Clean up
    await full_access_api.delete_block(block_id)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_nested_block_inheritance(full_access_client, readonly_client, shared_test_block):
    """Test that nested blocks inherit permissions correctly."""
    # Create nested block with full access
    full_access_api = BlocksAPI(full_access_client)
    response = await full_access_api.append_children(
        shared_test_block,
        [{
            "paragraph": {
                "rich_text": [{
                    "text": {"content": "Nested test block"}
                }]
            }
        }]
    )
    nested_block_id = response["results"][0]["id"]
    logger.info("nested_block_created", block_id=nested_block_id)
    
    # Verify read-only access to nested block
    readonly_api = BlocksAPI(readonly_client)
    response = await readonly_api.get_block(nested_block_id)
    assert response is not None
    assert "id" in response
    logger.info("nested_block_access_verified")
    
    # Clean up
    await full_access_api.delete_block(nested_block_id)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_read_access(full_access_client, readonly_client, shared_test_block):
    """Test that both full access and read-only tokens can read blocks"""
    # Test with full access token
    full_access_api = BlocksAPI(full_access_client)
    response = await full_access_api.get_block(shared_test_block)
    assert response is not None
    assert "id" in response
    logger.info("full_access_read_verified", block_id=shared_test_block)
    
    # Test with read-only token
    readonly_api = BlocksAPI(readonly_client)
    response = await readonly_api.get_block(shared_test_block)
    assert response is not None
    assert "id" in response
    logger.info("readonly_read_verified", block_id=shared_test_block)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_children_access(full_access_client, readonly_client, shared_test_block):
    """Test access to block children with different permission levels"""
    # Test with full access token
    full_access_api = BlocksAPI(full_access_client)
    response = await full_access_api.get_block_children(shared_test_block)
    assert response is not None
    assert "results" in response
    logger.info("full_access_children_verified", block_id=shared_test_block)
    
    # Test with read-only token
    readonly_api = BlocksAPI(readonly_client)
    response = await readonly_api.get_block_children(shared_test_block)
    assert response is not None
    assert "results" in response
    logger.info("readonly_children_verified", block_id=shared_test_block)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_append_block_permissions(full_access_client, readonly_client, shared_test_page):
    """Test block appending with different permission levels"""
    test_block = {
        "paragraph": {
            "rich_text": [{
                "text": {"content": "Test append block"}
            }]
        }
    }
    
    # Should succeed with full access
    full_access_api = BlocksAPI(full_access_client)
    response = await full_access_api.append_children(shared_test_page, [test_block])
    assert response is not None
    assert "results" in response
    block_id = response["results"][0]["id"]
    
    # Should fail with read-only access
    readonly_api = BlocksAPI(readonly_client)
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await readonly_api.append_children(shared_test_page, [test_block])
    assert exc_info.value.response.status_code == 403
    
    # Clean up
    await full_access_api.delete_block(block_id)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_block_permissions(full_access_client, readonly_client, shared_test_block):
    """Test block updates with different permission levels"""
    # Should succeed with full access
    full_access_api = BlocksAPI(full_access_client)
    response = await full_access_api.update_block(
        shared_test_block,
        {
            "paragraph": {
                "rich_text": [{
                    "text": {"content": "Updated content"}
                }]
            }
        }
    )
    assert response is not None
    assert "id" in response
    
    # Should fail with read-only access
    readonly_api = BlocksAPI(readonly_client)
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await readonly_api.update_block(
            shared_test_block,
            {
                "paragraph": {
                    "rich_text": [{
                        "text": {"content": "Should fail update"}
                    }]
                }
            }
        )
    assert exc_info.value.response.status_code == 403

@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_block_permissions(full_access_client, readonly_client, shared_test_block):
    """Test block deletion with different permission levels"""
    # Should fail with read-only access
    readonly_api = BlocksAPI(readonly_client)
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await readonly_api.delete_block(shared_test_block)
    assert exc_info.value.response.status_code == 403
    
    # Should succeed with full access
    full_access_api = BlocksAPI(full_access_client)
    response = await full_access_api.delete_block(shared_test_block)
    assert response is not None
    assert "id" in response

@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthErrors:
    """Test authentication and authorization error scenarios."""
    
    @pytest_asyncio.fixture
    async def mock_client(self):
        """Create a mock client for auth error tests."""
        client = AsyncMock(spec=httpx.AsyncClient)
        return client
    
    async def test_missing_auth_header(self, mock_client):
        """Test requests without authentication header."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 401
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=response
        )
        
        blocks_api = BlocksAPI(mock_client)
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await blocks_api.get_block("any-block-id")
        assert exc_info.value.response.status_code == 401
    
    async def test_invalid_token(self, mock_client):
        """Test requests with invalid authentication token."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 401
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=response
        )
        
        blocks_api = BlocksAPI(mock_client)
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await blocks_api.get_block("any-block-id")
        assert exc_info.value.response.status_code == 401
    
    async def test_expired_token(self, mock_client):
        """Test requests with expired authentication token."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 401
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=response
        )
        
        blocks_api = BlocksAPI(mock_client)
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await blocks_api.get_block("any-block-id")
        assert exc_info.value.response.status_code == 401
    
    async def test_nonexistent_block_auth(self, mock_client):
        """Test auth errors vs non-existent resource errors."""
        nonexistent_id = "12345678-1234-1234-1234-123456789012"
        
        response = MagicMock(spec=httpx.Response)
        response.status_code = 404
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=response
        )
        
        blocks_api = BlocksAPI(mock_client)
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await blocks_api.get_block(nonexistent_id)
        assert exc_info.value.response.status_code == 404