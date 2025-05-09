"""
Integration tests for todo-specific database operations.
Tests schema, queries, and data operations relevant to todo functionality.
"""
import os
import pytest
import pytest_asyncio
import httpx
import structlog
from datetime import datetime, timezone
from notion_api_mcp.api.databases import DatabasesAPI

# Import common fixtures
from ..common.conftest import (
    full_access_client,
    readonly_client,
    strip_hyphens,
)

logger = structlog.get_logger()

TODO_SCHEMA = {
    "Name": {"title": {}},  # Required title property
    "Status": {
        "select": {
            "options": [
                {"name": "Not Started", "color": "gray"},
                {"name": "In Progress", "color": "yellow"},
                {"name": "Done", "color": "green"}
            ]
        }
    },
    "Priority": {
        "select": {
            "options": [
                {"name": "High", "color": "red"},
                {"name": "Medium", "color": "yellow"},
                {"name": "Low", "color": "blue"}
            ]
        }
    },
    "Due Date": {"date": {}},
    "Notes": {"rich_text": {}}
}

@pytest_asyncio.fixture
async def todo_database(full_access_client):
    """Create a test todo database with full schema."""
    parent_id = strip_hyphens(os.getenv("NOTION_PARENT_PAGE_ID"))
    databases_api = DatabasesAPI(full_access_client)
    
    # Create database with todo schema
    database = await databases_api.create_database(
        parent_page_id=parent_id,
        title=f"Test Todo Database {os.urandom(4).hex()}",
        properties=TODO_SCHEMA
    )
    
    database_id = database["id"]
    logger.info("todo_database_created", database_id=database_id)
    
    yield database_id
    
    # Clean up
    try:
        await databases_api.update_database(
            database_id=database_id,
            archived=True
        )
    except Exception as e:
        logger.error("cleanup_error", database_id=database_id, error=str(e))

@pytest.mark.integration
@pytest.mark.asyncio
async def test_todo_schema_creation(full_access_client):
    """Test creating a database with todo-specific schema"""
    parent_id = strip_hyphens(os.getenv("NOTION_PARENT_PAGE_ID"))
    databases_api = DatabasesAPI(full_access_client)
    
    database = await databases_api.create_database(
        parent_page_id=parent_id,
        title=f"Schema Test Database {os.urandom(4).hex()}",
        properties=TODO_SCHEMA
    )
    
    assert database is not None
    assert "properties" in database
    
    # Verify all required properties exist
    properties = database["properties"]
    assert "Name" in properties
    assert "Status" in properties
    assert "Priority" in properties
    assert "Due Date" in properties
    assert "Notes" in properties
    
    # Verify property types
    assert properties["Name"]["type"] == "title"
    assert properties["Status"]["type"] == "select"
    assert properties["Priority"]["type"] == "select"
    assert properties["Due Date"]["type"] == "date"
    assert properties["Notes"]["type"] == "rich_text"
    
    # Verify select options
    assert len(properties["Status"]["select"]["options"]) == 3
    assert len(properties["Priority"]["select"]["options"]) == 3
    
    # Clean up
    await databases_api.update_database(
        database_id=database["id"],
        archived=True
    )

@pytest.mark.integration
@pytest.mark.asyncio
async def test_todo_filters(full_access_client, todo_database):
    """Test filtering todos by status and priority"""
    databases_api = DatabasesAPI(full_access_client)
    
    # Create filter for active (not done) high priority todos
    filter_conditions = databases_api.create_filter([
        {
            "property": "Status",
            "select": {"does_not_equal": "Done"}
        },
        {
            "property": "Priority",
            "select": {"equals": "High"}
        }
    ])
    
    response = await databases_api.query_database(
        database_id=todo_database,
        filter_conditions=filter_conditions
    )
    
    assert response is not None
    assert "results" in response
    # Note: Results may be empty if no matching todos exist

@pytest.mark.integration
@pytest.mark.asyncio
async def test_todo_date_filters(full_access_client, todo_database):
    """Test filtering todos by due date"""
    databases_api = DatabasesAPI(full_access_client)
    
    # Create filter for overdue todos
    now = datetime.now(timezone.utc)
    date_filter = databases_api.create_date_filter(
        property_name="Due Date",
        condition="before",
        value=now
    )
    
    response = await databases_api.query_database(
        database_id=todo_database,
        filter_conditions=date_filter
    )
    
    assert response is not None
    assert "results" in response
    # Note: Results may be empty if no overdue todos exist

@pytest.mark.integration
@pytest.mark.asyncio
async def test_todo_sorting(full_access_client, todo_database):
    """Test sorting todos by priority and due date"""
    databases_api = DatabasesAPI(full_access_client)
    
    # Sort by priority (high to low) then due date
    sorts = [
        databases_api.create_sort("Priority", "descending"),
        databases_api.create_sort("Due Date", "ascending")
    ]
    
    response = await databases_api.query_database(
        database_id=todo_database,
        sorts=sorts
    )
    
    assert response is not None
    assert "results" in response
    # Note: Results may be empty in fresh database

@pytest.mark.integration
@pytest.mark.asyncio
async def test_todo_search(full_access_client, todo_database):
    """Test searching todos by name and notes"""
    databases_api = DatabasesAPI(full_access_client)
    
    # Search in title and notes
    response = await databases_api.query_database(
        database_id=todo_database,
        filter_conditions={
            "or": [
                {
                    "property": "Name",
                    "rich_text": {"contains": "test"}
                },
                {
                    "property": "Notes",
                    "rich_text": {"contains": "test"}
                }
            ]
        }
    )
    
    assert response is not None
    assert "results" in response
    
    # Search specifically in notes
    response = await databases_api.query_database(
        database_id=todo_database,
        filter_conditions={
            "property": "Notes",
            "rich_text": {"contains": "test"}
        }
    )
    
    assert response is not None
    assert "results" in response

@pytest.mark.integration
@pytest.mark.asyncio
async def test_todo_schema_update(full_access_client, todo_database):
    """Test updating todo database schema"""
    databases_api = DatabasesAPI(full_access_client)
    
    # Add a new property for tags
    updated_properties = TODO_SCHEMA.copy()
    updated_properties["Tags"] = {
        "multi_select": {
            "options": [
                {"name": "Work", "color": "blue"},
                {"name": "Personal", "color": "green"},
                {"name": "Urgent", "color": "red"}
            ]
        }
    }
    
    response = await databases_api.update_database(
        database_id=todo_database,
        properties=updated_properties
    )
    
    assert response is not None
    assert "properties" in response
    assert "Tags" in response["properties"]
    assert response["properties"]["Tags"]["type"] == "multi_select"