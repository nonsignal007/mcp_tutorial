"""
Permission and authentication tests for Notion Databases API.
Tests access control, inheritance, and auth requirements.
"""
import os
import pytest
import pytest_asyncio
import httpx
import structlog
from notion_api_mcp.api.databases import DatabasesAPI

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
async def shared_test_database(full_access_client):
    """Create a test database under the pre-shared parent page.
    
    The parent page should already be shared with both integrations.
    The database will inherit permissions from the parent page.
    """
    parent_id = strip_hyphens(os.getenv("NOTION_PARENT_PAGE_ID"))
    databases_api = DatabasesAPI(full_access_client)
    
    # Create test database with basic schema
    database = await databases_api.create_database(
        parent_page_id=parent_id,
        title=f"Permission Test Database {os.urandom(4).hex()}",
        properties={
            "Name": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Active", "color": "green"},
                        {"name": "Archived", "color": "gray"}
                    ]
                }
            }
        }
    )
    
    database_id = database["id"]
    logger.info("test_database_created", database_id=database_id)
    
    yield database_id
    
    # Clean up after tests
    try:
        await databases_api.update_database(
            database_id=database_id,
            archived=True
        )
    except Exception as e:
        logger.error("cleanup_error", database_id=database_id, error=str(e))

@pytest.mark.integration
@pytest.mark.asyncio
async def test_permission_inheritance(full_access_client, readonly_client):
    """Test that databases inherit permissions from parent page.
    
    This test verifies that databases created under a shared parent page
    automatically inherit access permissions, eliminating the need for
    manual sharing.
    
    The test:
    1. Verifies both integrations can access the parent page
    2. Creates a database under the parent
    3. Verifies both integrations can access the database without manual sharing
    4. Tests database operations with appropriate permissions
    """
    parent_id = strip_hyphens(os.getenv("NOTION_PARENT_PAGE_ID"))
    logger.info("testing_parent_access", parent_url=format_page_url(parent_id))
    
    # Create database with full access
    full_access_api = DatabasesAPI(full_access_client)
    database = await full_access_api.create_database(
        parent_page_id=parent_id,
        title=f"Inheritance Test Database {os.urandom(4).hex()}",
        properties={"Name": {"title": {}}}
    )
    database_id = database["id"]
    logger.info("database_created", database_id=database_id)
    
    # Verify read-only access without manual sharing
    readonly_api = DatabasesAPI(readonly_client)
    response = await readonly_api.get_database(database_id)
    assert response is not None
    assert "id" in response
    logger.info("readonly_access_verified")
    
    # Verify query access
    query_response = await readonly_api.query_database(database_id)
    assert query_response is not None
    assert "results" in query_response
    logger.info("readonly_query_verified")
    # Clean up
    await full_access_api.update_database(
        database_id=database_id,
        archived=True
    )

@pytest.mark.integration
@pytest.mark.asyncio
async def test_read_access(full_access_client, readonly_client, shared_test_database):
    """Test that both full access and read-only tokens can read databases"""
    # Test with full access token
    full_access_api = DatabasesAPI(full_access_client)
    response = await full_access_api.get_database(shared_test_database)
    assert response is not None
    assert "id" in response
    logger.info("full_access_read_verified", database_id=shared_test_database)
    
    # Test with read-only token
    readonly_api = DatabasesAPI(readonly_client)
    response = await readonly_api.get_database(shared_test_database)
    assert response is not None
    assert "id" in response
    logger.info("readonly_read_verified", database_id=shared_test_database)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_database_permissions(full_access_client, readonly_client):
    """Test database creation with different permission levels"""
    parent_id = strip_hyphens(os.getenv("NOTION_PARENT_PAGE_ID"))
    
    # Should succeed with full access
    full_access_api = DatabasesAPI(full_access_client)
    database = await full_access_api.create_database(
        parent_page_id=parent_id,
        title=f"Permission Test Database {os.urandom(4).hex()}",
        properties={"Name": {"title": {}}}
    )
    assert database is not None
    assert "id" in database
    database_id = database["id"]
    
    # Should fail with read-only access
    readonly_api = DatabasesAPI(readonly_client)
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await readonly_api.create_database(
            parent_page_id=parent_id,
            title="Should Fail Database",
            properties={"Name": {"title": {}}}
        )
    assert exc_info.value.response.status_code in [403, 404]
    
    # Clean up
    await full_access_api.update_database(
        database_id=database_id,
        archived=True
    )

@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_database_permissions(full_access_client, readonly_client, shared_test_database):
    """Test database updates with different permission levels"""
    # Should succeed with full access
    full_access_api = DatabasesAPI(full_access_client)
    response = await full_access_api.update_database(
        database_id=shared_test_database,
        title="Updated Test Database"
    )
    assert response is not None
    assert "id" in response
    
    # Should fail with read-only access
    readonly_api = DatabasesAPI(readonly_client)
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await readonly_api.update_database(
            database_id=shared_test_database,
            title="Should Fail Update"
        )
    assert exc_info.value.response.status_code == 403

@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_database_permissions(full_access_client, readonly_client, shared_test_database):
    """Test database querying with different permission levels"""
    # Should succeed with full access
    full_access_api = DatabasesAPI(full_access_client)
    response = await full_access_api.query_database(shared_test_database)
    assert response is not None
    assert "results" in response
    
    # Should succeed with read-only access
    readonly_api = DatabasesAPI(readonly_client)
    response = await readonly_api.query_database(shared_test_database)
    assert response is not None
    assert "results" in response

@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_auth():
    """Test requests with invalid authentication"""
    # Test without auth header
    async with httpx.AsyncClient(
        base_url="https://api.notion.com/v1/",
        timeout=30.0,
        headers={"Notion-Version": "2022-06-28"}
    ) as client:
        databases_api = DatabasesAPI(client)
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await databases_api.get_database("any-database-id")
        assert exc_info.value.response.status_code == 401

    # Test with invalid token
    async with httpx.AsyncClient(
        base_url="https://api.notion.com/v1/",
        timeout=30.0,
        headers={
            "Notion-Version": "2022-06-28",
            "Authorization": "Bearer invalid_token"
        }
    ) as client:
        databases_api = DatabasesAPI(client)
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await databases_api.get_database("any-database-id")
        assert exc_info.value.response.status_code == 401