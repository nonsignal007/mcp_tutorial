"""
Basic CRUD operation tests for Notion Pages API.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import httpx
from datetime import datetime

from notion_api_mcp.api.pages import PagesAPI

@pytest_asyncio.fixture
async def mock_client():
    """Mock httpx client for testing."""
    client = AsyncMock(spec=httpx.AsyncClient)
    
    # Create a mock response
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()  # Regular method that does nothing
    mock_response.json = MagicMock(return_value={"object": "page"})  # Regular method returning test data
    
    # Make client methods return the mock response
    client.post.return_value = mock_response
    client.patch.return_value = mock_response
    client.get.return_value = mock_response
    
    return client

@pytest_asyncio.fixture
async def pages_api(mock_client):
    """PagesAPI instance with mocked client."""
    return PagesAPI(mock_client)

class TestPageCreation:
    """Test page creation functionality."""

    @pytest.mark.asyncio
    async def test_create_page_database_parent(self, pages_api):
        """Test creating a page in a database."""
        properties = {"Title": {"title": [{"text": {"content": "Test Page"}}]}}
        result = await pages_api.create_page("test-db-id", properties)
        
        assert result == {"object": "page"}
        pages_api._client.post.assert_called_once_with(
            "pages",
            json={
                "parent": {
                    "type": "database_id",
                    "database_id": "test-db-id"
                },
                "properties": properties
            }
        )

    @pytest.mark.asyncio
    async def test_create_page_with_children(self, pages_api):
        """Test creating a page with content blocks."""
        properties = {"Title": {"title": [{"text": {"content": "Test Page"}}]}}
        children = [{"paragraph": {"text": "Test content"}}]
        
        result = await pages_api.create_page(
            "test-db-id",
            properties,
            children=children
        )
        
        assert result == {"object": "page"}
        pages_api._client.post.assert_called_once_with(
            "pages",
            json={
                "parent": {
                    "type": "database_id",
                    "database_id": "test-db-id"
                },
                "properties": properties,
                "children": children
            }
        )

    @pytest.mark.asyncio
    async def test_create_page_page_parent(self, pages_api):
        """Test creating a page under another page."""
        properties = {"Title": {"title": [{"text": {"content": "Test Page"}}]}}
        result = await pages_api.create_page(
            "test-page-id",
            properties,
            is_database=False
        )
        
        assert result == {"object": "page"}
        pages_api._client.post.assert_called_once_with(
            "pages",
            json={
                "parent": {
                    "type": "page_id",
                    "page_id": "test-page-id"
                },
                "properties": properties
            }
        )

    def test_create_todo_properties_basic(self, pages_api):
        """Test creating basic todo properties."""
        properties = pages_api.create_todo_properties("Test Todo")
        
        assert "Task" in properties
        assert properties["Task"]["title"][0]["text"]["content"] == "Test Todo"

    def test_create_todo_properties_full(self, pages_api):
        """Test creating todo properties with all fields."""
        due_date = datetime.now()
        properties = pages_api.create_todo_properties(
            title="Test Todo",
            description="Test Description",
            due_date=due_date,
            priority="High",
            tags=["work", "urgent"],
            status="In Progress"
        )
        
        assert properties["Task"]["title"][0]["text"]["content"] == "Test Todo"
        assert properties["Description"]["rich_text"][0]["text"]["content"] == "Test Description"
        assert properties["Due Date"]["date"]["start"] == due_date.isoformat()
        assert properties["Priority"]["select"]["name"] == "High"
        assert [tag["name"] for tag in properties["Tags"]["multi_select"]] == ["work", "urgent"]
        assert properties["Status"]["status"]["name"] == "In Progress"

@pytest.mark.asyncio
class TestPageOperations:
    """Test page manipulation operations."""

    async def test_update_page_properties(self, pages_api):
        """Test updating page properties."""
        properties = {"Title": {"title": [{"text": {"content": "Updated"}}]}}
        result = await pages_api.update_page("test-page-id", properties)
        
        assert result == {"object": "page"}
        pages_api._client.patch.assert_called_once_with(
            "pages/test-page-id",
            json={"properties": properties}
        )

    async def test_update_page_archive(self, pages_api):
        """Test archiving a page."""
        result = await pages_api.update_page("test-page-id", archived=True)
        
        assert result == {"object": "page"}
        pages_api._client.patch.assert_called_once_with(
            "pages/test-page-id",
            json={"archived": True}
        )

    async def test_get_page(self, pages_api):
        """Test retrieving a page."""
        result = await pages_api.get_page("test-page-id")
        
        assert result == {"object": "page"}
        pages_api._client.get.assert_called_once_with(
            "pages/test-page-id"
        )

    async def test_archive_page(self, pages_api):
        """Test archiving a page using dedicated method."""
        result = await pages_api.archive_page("test-page-id")
        
        assert result == {"object": "page"}
        pages_api._client.patch.assert_called_once_with(
            "pages/test-page-id",
            json={"archived": True}
        )

    async def test_restore_page(self, pages_api):
        """Test restoring an archived page."""
        result = await pages_api.restore_page("test-page-id")
        
        assert result == {"object": "page"}
        pages_api._client.patch.assert_called_once_with(
            "pages/test-page-id",
            json={"archived": False}
        )

@pytest.mark.asyncio
class TestPropertyOperations:
    """Test page property operations."""

    async def test_get_property_item(self, pages_api):
        """Test retrieving a property item."""
        result = await pages_api.get_property_item(
            "test-page-id",
            "prop-id",
            page_size=50
        )
        
        assert result == {"object": "page"}
        pages_api._client.get.assert_called_once_with(
            "pages/test-page-id/properties/prop-id",
            params={"page_size": 50}
        )

@pytest.mark.asyncio
class TestErrorHandling:
    """Test API error handling in page operations."""

    async def test_invalid_page_id_error(self, pages_api):
        """Test error handling with invalid page ID format."""
        pages_api._client.get.side_effect = httpx.HTTPError("Invalid page ID")
        
        with pytest.raises(httpx.HTTPError):
            await pages_api.get_page("invalid-format-id")

    async def test_malformed_properties_error(self, pages_api):
        """Test error handling with malformed properties."""
        pages_api._client.post.side_effect = httpx.HTTPError("Malformed properties")
        
        with pytest.raises(httpx.HTTPError):
            await pages_api.create_page("test-id", {"invalid": "property"})

    async def test_invalid_property_error(self, pages_api):
        """Test error handling with invalid property ID."""
        pages_api._client.get.side_effect = httpx.HTTPError("Invalid property")
        
        with pytest.raises(httpx.HTTPError):
            await pages_api.get_property_item("test-id", "invalid-prop")

    async def test_invalid_parent_error(self, pages_api):
        """Test error handling with invalid parent ID."""
        pages_api._client.post.side_effect = httpx.HTTPError("Invalid parent")
        
        with pytest.raises(httpx.HTTPError):
            await pages_api.create_page("invalid-parent", {})