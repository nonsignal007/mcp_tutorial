"""
Permission-related tests for Notion property operations.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import httpx

from notion_api_mcp.api.pages import PagesAPI

@pytest_asyncio.fixture
async def mock_client():
    """Mock httpx client for testing."""
    client = AsyncMock(spec=httpx.AsyncClient)
    
    # Create a mock response
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"object": "property_item"})
    
    # Make client methods return the mock response
    client.get.return_value = mock_response
    client.patch.return_value = mock_response
    
    return client

@pytest_asyncio.fixture
async def pages_api(mock_client):
    """PagesAPI instance with mocked client."""
    return PagesAPI(mock_client)

@pytest.mark.asyncio
class TestPropertyPermissions:
    """Test property permission scenarios."""

    async def test_read_only_property(self, pages_api):
        """Test handling read-only property updates."""
        # Mock 401 response for unauthorized update
        pages_api._client.patch.side_effect = httpx.HTTPError("Cannot update read-only property")
        
        with pytest.raises(httpx.HTTPError) as exc:
            await pages_api.update_page(
                "test-page-id",
                properties={
                    "ReadOnly": {
                        "rich_text": [{
                            "text": {"content": "Cannot update this"}
                        }]
                    }
                }
            )
        assert "Cannot update read-only property" in str(exc.value)

    async def test_restricted_property_access(self, pages_api):
        """Test handling restricted property access."""
        # Mock 403 response for forbidden access
        pages_api._client.get.side_effect = httpx.HTTPError("Access to property forbidden")
        
        with pytest.raises(httpx.HTTPError) as exc:
            await pages_api.get_property_item(
                "test-page-id",
                "restricted-prop-id"
            )
        assert "Access to property forbidden" in str(exc.value)

    async def test_property_not_found(self, pages_api):
        """Test handling non-existent property access."""
        # Mock 404 response for not found
        pages_api._client.get.side_effect = httpx.HTTPError("Property not found")
        
        with pytest.raises(httpx.HTTPError) as exc:
            await pages_api.get_property_item(
                "test-page-id",
                "nonexistent-prop-id"
            )
        assert "Property not found" in str(exc.value)

    async def test_invalid_auth_token(self, pages_api):
        """Test handling invalid authentication."""
        # Mock 401 response for invalid auth
        pages_api._client.get.side_effect = httpx.HTTPError("Invalid authentication token")
        
        with pytest.raises(httpx.HTTPError) as exc:
            await pages_api.get_property_item(
                "test-page-id",
                "test-prop-id"
            )
        assert "Invalid authentication token" in str(exc.value)

    async def test_rate_limit_exceeded(self, pages_api):
        """Test handling rate limit errors."""
        # Mock 429 response for rate limit
        pages_api._client.get.side_effect = httpx.HTTPError("Rate limit exceeded")
        
        with pytest.raises(httpx.HTTPError) as exc:
            await pages_api.get_property_item(
                "test-page-id",
                "test-prop-id"
            )
        assert "Rate limit exceeded" in str(exc.value)

@pytest.mark.asyncio
class TestBulkPropertyOperations:
    """Test bulk property operation permissions."""

    async def test_mixed_permission_update(self, pages_api):
        """Test updating multiple properties with mixed permissions."""
        # Mock error for partial permission failure
        pages_api._client.patch.side_effect = httpx.HTTPError(
            "Some properties could not be updated due to permissions"
        )
        
        with pytest.raises(httpx.HTTPError) as exc:
            await pages_api.update_page(
                "test-page-id",
                properties={
                    "Allowed": {"rich_text": [{"text": {"content": "Can update"}}]},
                    "Restricted": {"rich_text": [{"text": {"content": "Cannot update"}}]}
                }
            )
        assert "Some properties could not be updated" in str(exc.value)

    async def test_bulk_property_retrieval(self, pages_api):
        """Test retrieving multiple properties with different permissions."""
        # First call succeeds, second fails with permission error
        pages_api._client.get.side_effect = [
            AsyncMock(
                status_code=200,
                json=MagicMock(return_value={"object": "property_item"})
            ),
            httpx.HTTPError("Access denied to some properties")
        ]
        
        # First property retrieval should succeed
        result = await pages_api.get_property_item(
            "test-page-id",
            "allowed-prop-id"
        )
        assert result == {"object": "property_item"}
        
        # Second property retrieval should fail
        with pytest.raises(httpx.HTTPError) as exc:
            await pages_api.get_property_item(
                "test-page-id",
                "restricted-prop-id"
            )
        assert "Access denied" in str(exc.value)