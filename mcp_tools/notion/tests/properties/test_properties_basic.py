"""
Basic property operation tests for Notion Pages API.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import httpx
from datetime import datetime

from notion_api_mcp.api.pages import PagesAPI
from notion_api_mcp.models.properties import (
    TitleProperty,
    RichTextProperty,
    DateProperty,
    SelectProperty,
    MultiSelectProperty,
    NumberProperty,
    CheckboxProperty,
    StatusProperty
)

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
class TestPropertyRetrieval:
    """Test property retrieval operations."""

    async def test_get_property_item_basic(self, pages_api):
        """Test basic property item retrieval."""
        result = await pages_api.get_property_item(
            "test-page-id",
            "test-prop-id"
        )
        
        assert result == {"object": "property_item"}
        pages_api._client.get.assert_called_once_with(
            "pages/test-page-id/properties/test-prop-id",
            params={"page_size": 100}
        )

    async def test_get_property_item_custom_page_size(self, pages_api):
        """Test property item retrieval with custom page size."""
        result = await pages_api.get_property_item(
            "test-page-id",
            "test-prop-id",
            page_size=50
        )
        
        assert result == {"object": "property_item"}
        pages_api._client.get.assert_called_once_with(
            "pages/test-page-id/properties/test-prop-id",
            params={"page_size": 50}
        )

@pytest.mark.asyncio
class TestPropertyUpdates:
    """Test property update operations."""

    async def test_update_title_property(self, pages_api):
        """Test updating a title property."""
        properties = {
            "Title": {
                "title": [{
                    "text": {"content": "Updated Title"}
                }]
            }
        }
        
        result = await pages_api.update_page(
            "test-page-id",
            properties=properties
        )
        
        assert result == {"object": "property_item"}
        pages_api._client.patch.assert_called_once_with(
            "pages/test-page-id",
            json={"properties": properties}
        )

    async def test_update_rich_text_property(self, pages_api):
        """Test updating a rich text property."""
        properties = {
            "Description": {
                "rich_text": [{
                    "text": {"content": "Updated description"}
                }]
            }
        }
        
        result = await pages_api.update_page(
            "test-page-id",
            properties=properties
        )
        
        assert result == {"object": "property_item"}
        pages_api._client.patch.assert_called_once_with(
            "pages/test-page-id",
            json={"properties": properties}
        )

    async def test_update_date_property(self, pages_api):
        """Test updating a date property."""
        now = datetime.now()
        properties = {
            "Due Date": {
                "date": {
                    "start": now.isoformat()
                }
            }
        }
        
        result = await pages_api.update_page(
            "test-page-id",
            properties=properties
        )
        
        assert result == {"object": "property_item"}
        pages_api._client.patch.assert_called_once_with(
            "pages/test-page-id",
            json={"properties": properties}
        )

    async def test_update_select_property(self, pages_api):
        """Test updating a select property."""
        properties = {
            "Status": {
                "select": {
                    "name": "In Progress"
                }
            }
        }
        
        result = await pages_api.update_page(
            "test-page-id",
            properties=properties
        )
        
        assert result == {"object": "property_item"}
        pages_api._client.patch.assert_called_once_with(
            "pages/test-page-id",
            json={"properties": properties}
        )

    async def test_update_multi_select_property(self, pages_api):
        """Test updating a multi-select property."""
        properties = {
            "Tags": {
                "multi_select": [
                    {"name": "urgent"},
                    {"name": "bug"}
                ]
            }
        }
        
        result = await pages_api.update_page(
            "test-page-id",
            properties=properties
        )
        
        assert result == {"object": "property_item"}
        pages_api._client.patch.assert_called_once_with(
            "pages/test-page-id",
            json={"properties": properties}
        )

@pytest.mark.asyncio
class TestPropertyErrorHandling:
    """Test property error handling."""

    async def test_invalid_property_id(self, pages_api):
        """Test error handling with invalid property ID."""
        pages_api._client.get.side_effect = httpx.HTTPError("Invalid property ID")
        
        with pytest.raises(httpx.HTTPError):
            await pages_api.get_property_item(
                "test-page-id",
                "invalid-prop-id"
            )

    async def test_invalid_property_value(self, pages_api):
        """Test error handling with invalid property value."""
        pages_api._client.patch.side_effect = httpx.HTTPError("Invalid property value")
        
        with pytest.raises(httpx.HTTPError):
            await pages_api.update_page(
                "test-page-id",
                properties={"Invalid": {"invalid_type": "value"}}
            )

    async def test_property_permission_error(self, pages_api):
        """Test error handling with insufficient permissions."""
        pages_api._client.get.side_effect = httpx.HTTPError("Permission denied")
        
        with pytest.raises(httpx.HTTPError):
            await pages_api.get_property_item(
                "test-page-id",
                "restricted-prop-id"
            )

@pytest.mark.asyncio
class TestPropertyValidation:
    """Test property validation."""

    async def test_empty_property_update(self, pages_api):
        """Test updating with empty properties."""
        with pytest.raises(ValueError):
            await pages_api.update_page("test-page-id")

    async def test_invalid_page_size(self, pages_api):
        """Test invalid page size parameter."""
        with pytest.raises(ValueError):
            await pages_api.get_property_item(
                "test-page-id",
                "test-prop-id",
                page_size=0
            )