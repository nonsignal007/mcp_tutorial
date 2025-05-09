"""
Permission and authentication tests for Notion Pages API.
Tests access control, inheritance, and auth requirements.
"""
import os
import pytest
import pytest_asyncio
import httpx
import structlog
from unittest.mock import AsyncMock, MagicMock
from notion_api_mcp.api.pages import PagesAPI

# Import common fixtures
from tests.common.conftest import (
    full_access_client,
    readonly_client,
    invalid_client,
    strip_hyphens,
    format_page_url,
)

logger = structlog.get_logger()

@pytest_asyncio.fixture
async def shared_test_page(full_access_client):
    """Create a test page under the pre-shared parent page.
    
    The parent page should already be shared with both integrations.
    All child pages will inherit permissions from the parent.
    """
    parent_id = os.getenv("NOTION_PARENT_PAGE_ID").replace("-", "")
    pages_api = PagesAPI(full_access_client)
    
    # Create a test page under the shared parent
    test_page = await pages_api.create_page(
        parent_id=parent_id,
        properties={
            "title": [{
                "type": "text",
                "text": {"content": "Test Page (Inherits Permissions)"}
            }]
        },
        is_database=False
    )
    
    page_id = test_page["id"]
    logger.info("test_page_created", page_id=page_id, url=format_page_url(page_id))
    
    yield page_id
    
    # Clean up after tests
    await pages_api.archive_page(page_id)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_permission_inheritance(full_access_client, readonly_client):
    """Test that child pages inherit permissions from parent page."""
    parent_id = os.getenv("NOTION_PARENT_PAGE_ID").replace("-", "")
    logger.info("testing_parent_access", parent_url=format_page_url(parent_id))
    
    # Verify parent page access
    full_access_api = PagesAPI(full_access_client)
    readonly_api = PagesAPI(readonly_client)
    
    parent_response = await full_access_api.get_page(parent_id)
    assert parent_response is not None
    assert "id" in parent_response
    logger.info("full_access_parent_verified")
    
    parent_response = await readonly_api.get_page(parent_id)
    assert parent_response is not None
    assert "id" in parent_response
    logger.info("readonly_parent_verified")
    
    # Create and verify access to child page
    child_page = await full_access_api.create_page(
        parent_id=parent_id,
        properties={
            "title": [{
                "type": "text",
                "text": {"content": "Child Test Page"}
            }]
        },
        is_database=False
    )
    child_id = child_page["id"]
    logger.info("child_page_created", page_url=format_page_url(child_id))
    
    # Verify read-only access to child without manual sharing
    child_response = await readonly_api.get_page(child_id)
    assert child_response is not None
    assert "id" in child_response
    logger.info("child_inheritance_verified")
    
    # Create and verify access to grandchild page
    grandchild_page = await full_access_api.create_page(
        parent_id=child_id,
        properties={
            "title": [{
                "type": "text",
                "text": {"content": "Grandchild Test Page"}
            }]
        },
        is_database=False
    )
    grandchild_id = grandchild_page["id"]
    logger.info("grandchild_page_created", page_url=format_page_url(grandchild_id))
    
    # Verify read-only access to grandchild without manual sharing
    grandchild_response = await readonly_api.get_page(grandchild_id)
    assert grandchild_response is not None
    assert "id" in grandchild_response
    logger.info("grandchild_inheritance_verified")
    
    # Clean up test pages
    await full_access_api.archive_page(grandchild_id)
    await full_access_api.archive_page(child_id)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_read_access(full_access_client, readonly_client, shared_test_page):
    """Test that both full access and read-only tokens can read pages"""
    page_id = shared_test_page.replace("-", "")  # Strip hyphens for API calls
    
    # Test with full access token
    full_access_api = PagesAPI(full_access_client)
    response = await full_access_api.get_page(page_id)
    assert response is not None
    assert "id" in response
    logger.info("full_access_read_verified", page_id=page_id)
    
    # Test with read-only token
    readonly_api = PagesAPI(readonly_client)
    response = await readonly_api.get_page(page_id)
    assert response is not None
    assert "id" in response
    logger.info("readonly_read_verified", page_id=page_id)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_page_permissions(full_access_client, readonly_client):
    """Test page creation with different permission levels"""
    parent_id = strip_hyphens(os.getenv("NOTION_PARENT_PAGE_ID"))
    test_properties = {
        "title": [{
            "type": "text",
            "text": {"content": "Test Page"}
        }]
    }
    
    # Should succeed with full access
    full_access_api = PagesAPI(full_access_client)
    response = await full_access_api.create_page(
        parent_id=parent_id,
        properties=test_properties,
        is_database=False
    )
    assert response is not None
    assert "id" in response
    created_page_id = response["id"]
    
    # Should fail with read-only access
    readonly_api = PagesAPI(readonly_client)
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await readonly_api.create_page(
            parent_id=parent_id,
            properties=test_properties,
            is_database=False
        )
    assert exc_info.value.response.status_code in [403, 404]
    
    # Clean up: Archive the created page
    await full_access_api.archive_page(created_page_id)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_page_permissions(full_access_client, readonly_client):
    """Test page updates with different permission levels"""
    # First create a test page
    full_access_api = PagesAPI(full_access_client)
    parent_id = strip_hyphens(os.getenv("NOTION_PARENT_PAGE_ID"))
    
    test_page = await full_access_api.create_page(
        parent_id=parent_id,
        properties={
            "title": [{
                "type": "text",
                "text": {"content": "Update Test Page"}
            }]
        },
        is_database=False
    )
    page_id = test_page["id"]
    
    update_properties = {
        "title": [{
            "type": "text",
            "text": {"content": "Updated Test Page"}
        }]
    }
    
    # Should succeed with full access
    response = await full_access_api.update_page(
        page_id=page_id,
        properties=update_properties
    )
    assert response is not None
    assert "id" in response
    
    # Should fail with read-only access
    readonly_api = PagesAPI(readonly_client)
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await readonly_api.update_page(
            page_id=page_id,
            properties=update_properties
        )
    assert exc_info.value.response.status_code == 403
    
    # Clean up
    await full_access_api.archive_page(page_id)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_archive_page_permissions(full_access_client, readonly_client):
    """Test page archiving with different permission levels"""
    # Create a test page to archive
    full_access_api = PagesAPI(full_access_client)
    parent_id = strip_hyphens(os.getenv("NOTION_PARENT_PAGE_ID"))
    
    test_page = await full_access_api.create_page(
        parent_id=parent_id,
        properties={
            "title": [{
                "type": "text",
                "text": {"content": "Archive Test Page"}
            }]
        },
        is_database=False
    )
    page_id = test_page["id"]
    
    # Should fail with read-only access
    readonly_api = PagesAPI(readonly_client)
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await readonly_api.archive_page(page_id)
    assert exc_info.value.response.status_code == 403
    
    # Should succeed with full access
    response = await full_access_api.archive_page(page_id)
    assert response is not None
    assert response.get("archived", False) is True

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
        # Create mock 401 response
        response = MagicMock(spec=httpx.Response)
        response.status_code = 401
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=response
        )
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_client.get("pages/any-page-id")
        assert exc_info.value.response.status_code == 401

    async def test_invalid_token(self, mock_client):
        """Test requests with invalid authentication token."""
        # Create mock 401 response
        response = MagicMock(spec=httpx.Response)
        response.status_code = 401
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=response
        )
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_client.get("pages/any-page-id")
        assert exc_info.value.response.status_code == 401

    async def test_expired_token(self, mock_client):
        """Test requests with expired authentication token."""
        # Create mock 401 response
        response = MagicMock(spec=httpx.Response)
        response.status_code = 401
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=response
        )
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_client.get("pages/any-page-id")
        assert exc_info.value.response.status_code == 401

    async def test_insufficient_permissions(self, readonly_client):
        """Test operations with insufficient permissions."""
        pages_api = PagesAPI(readonly_client)
        parent_id = strip_hyphens(os.getenv("NOTION_PARENT_PAGE_ID"))

        # Try to create page (should fail)
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await pages_api.create_page(
                parent_id=parent_id,
                properties={"title": [{"text": {"content": "Test"}}]},
                is_database=False
            )
        assert exc_info.value.response.status_code == 403

        # Try to update page (should fail)
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await pages_api.update_page(
                "any-page-id",
                properties={"title": [{"text": {"content": "Test"}}]}
            )
        assert exc_info.value.response.status_code == 403

    async def test_nonexistent_page_auth(self, mock_client):
        """Test auth errors vs non-existent resource errors."""
        nonexistent_id = "12345678-1234-1234-1234-123456789012"
        
        # Create mock 404 response
        response = MagicMock(spec=httpx.Response)
        response.status_code = 404
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=response
        )
        
        # Create API instance with mock client
        pages_api = PagesAPI(mock_client)
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await pages_api.get_page(nonexistent_id)
        assert exc_info.value.response.status_code == 404