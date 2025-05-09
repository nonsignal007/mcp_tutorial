"""
Basic CRUD operation tests for Notion Databases API.
"""
import os
import pytest
import pytest_asyncio
import httpx
from notion_api_mcp.api.databases import DatabasesAPI

# Import common fixtures
from ..common.conftest import (
    full_access_client,
    strip_hyphens,
)

@pytest_asyncio.fixture
async def test_database(full_access_client):
    """Create and cleanup a test database"""
    databases_api = DatabasesAPI(full_access_client)
    parent_id = strip_hyphens(os.getenv("NOTION_PARENT_PAGE_ID"))
    
    # Create test database
    database = await databases_api.create_database(
        parent_page_id=parent_id,
        title=f"Test Database {os.urandom(4).hex()}",
        properties={"Name": {"title": {}}}  # Minimal schema
    )
    
    database_id = database["id"]
    yield database_id
    
    # Cleanup: Archive the test database
    try:
        await databases_api.update_database(
            database_id=database_id,
            properties={"archived": True}
        )
    except Exception as e:
        print(f"Error cleaning up test database {database_id}: {e}")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_database(full_access_client):
    """Test database creation with basic schema"""
    databases_api = DatabasesAPI(full_access_client)
    parent_id = strip_hyphens(os.getenv("NOTION_PARENT_PAGE_ID"))
    
    try:
        database = await databases_api.create_database(
            parent_page_id=parent_id,
            title=f"Test Database {os.urandom(4).hex()}",
            properties={
                "Name": {"title": {}},
                "Description": {"rich_text": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "To Do", "color": "red"},
                            {"name": "In Progress", "color": "yellow"},
                            {"name": "Done", "color": "green"}
                        ]
                    }
                }
            }
        )
        
        assert database is not None
        assert "id" in database
        assert "properties" in database
        assert "Name" in database["properties"]
        assert "Description" in database["properties"]
        assert "Status" in database["properties"]
        
        # Cleanup
        await databases_api.update_database(
            database_id=database["id"],
            archived=True
        )
    except Exception as e:
        pytest.fail(f"Database creation failed: {str(e)}")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_database(full_access_client, test_database):
    """Test database querying"""
    databases_api = DatabasesAPI(full_access_client)
    
    try:
        response = await databases_api.query_database(test_database)
        assert response is not None
        assert "results" in response
        assert isinstance(response["results"], list)
    except Exception as e:
        pytest.fail(f"Database query failed: {str(e)}")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_database(full_access_client, test_database):
    """Test database schema updates"""
    databases_api = DatabasesAPI(full_access_client)
    
    try:
        # Add new property to schema
        response = await databases_api.update_database(
            database_id=test_database,
            title="Updated Test Database",
            properties={
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "High", "color": "red"},
                            {"name": "Medium", "color": "yellow"},
                            {"name": "Low", "color": "blue"}
                        ]
                    }
                }
            }
        )
        
        assert response is not None
        assert "id" in response
        assert "properties" in response
        assert "Priority" in response["properties"]
        
        # Verify property was added
        properties = response["properties"]
        assert properties["Priority"]["type"] == "select"
        assert len(properties["Priority"]["select"]["options"]) == 3
        
    except Exception as e:
        pytest.fail(f"Database update failed: {str(e)}")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_database(full_access_client, test_database):
    """Test retrieving database metadata"""
    databases_api = DatabasesAPI(full_access_client)
    
    try:
        response = await databases_api.get_database(test_database)
        assert response is not None
        assert "id" in response
        assert "properties" in response
        assert "title" in response
    except Exception as e:
        pytest.fail(f"Database retrieval failed: {str(e)}")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_databases(full_access_client):
    """Test listing all databases"""
    databases_api = DatabasesAPI(full_access_client)
    
    try:
        response = await databases_api.list_databases()
        assert response is not None
        assert "results" in response
        assert isinstance(response["results"], list)
    except Exception as e:
        pytest.fail(f"Database listing failed: {str(e)}")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_error_handling(full_access_client):
    """Test error handling for database operations"""
    databases_api = DatabasesAPI(full_access_client)
    
    # Test with invalid database ID
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await databases_api.get_database("invalid-id")
    assert exc_info.value.response.status_code in [404, 400]
    
    # Test with invalid parent page ID
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await databases_api.create_database(
            parent_page_id="invalid-id",
            title="Should Fail",
            properties={"Name": {"title": {}}}
        )
    assert exc_info.value.response.status_code in [404, 400]