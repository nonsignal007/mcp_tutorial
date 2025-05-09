"""
Integration tests for Notion MCP server using real Notion API.
Requires valid Notion API credentials in .env.integration file.
"""
import os
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
import httpx
from dotenv import load_dotenv
from pathlib import Path

from notion_api_mcp.server import NotionServer, ServerConfig
from notion_api_mcp.api.databases import DatabasesAPI
from notion_api_mcp.api.pages import PagesAPI

# Load integration test environment
project_root = Path(__file__).parent.parent
env_path = project_root / '.env.integration'

if not env_path.exists():
    pytest.skip(
        "Skipping integration tests: .env.integration not found. "
        "Create this file with NOTION_API_KEY and NOTION_DATABASE_ID to run integration tests.",
        allow_module_level=True
    )

load_dotenv(env_path)

# Verify credentials
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
# Format page ID with hyphens for API call
PARENT_PAGE_ID = "173dd756-6405-8016-b7e0-dc9aee0a97d6"

if not NOTION_API_KEY or not DATABASE_ID:
    pytest.skip(
        "Skipping integration tests: Missing required environment variables. "
        "Ensure NOTION_API_KEY and NOTION_DATABASE_ID are set in .env.integration",
        allow_module_level=True
    )

# Test database schema
TODO_DATABASE_SCHEMA = {
    "Task": {
        "title": {}
    },
    "TaskStatus": {  # Renamed from 'Status' due to API limitations
        "select": {
            "options": [
                {"name": "Not Started", "color": "gray"},
                {"name": "In Progress", "color": "blue"},
                {"name": "Done", "color": "green"}
            ]
        }
    },
    "Priority": {
        "select": {
            "options": [
                {"name": "high", "color": "red"},
                {"name": "medium", "color": "yellow"},
                {"name": "low", "color": "green"}
            ]
        }
    },
    "Description": {
        "rich_text": {}
    },
    "Due Date": {
        "date": {}
    },
    "Tags": {
        "multi_select": {
            "options": [
                {"name": "test", "color": "blue"},
                {"name": "integration", "color": "green"}
            ]
        }
    }
}

# Initialize HTTP client for tests
@pytest_asyncio.fixture
async def http_client():
    """Create and cleanup HTTP client for tests"""
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    async with httpx.AsyncClient(
        base_url="https://api.notion.com/v1/",
        timeout=30.0,
        headers=headers
    ) as client:
        yield client

@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_authorization(http_client):
    """
    Basic test to validate API authorization is working.
    This test creates a database and verifies we can interact with it,
    which requires both read and write permissions.
    """
    databases_api = DatabasesAPI(http_client)
    
    # Create a test database
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_title = f"Auth Test Database {timestamp}"
    
    try:
        # Attempt to create database
        database = await databases_api.create_database(
            parent_page_id=PARENT_PAGE_ID,
            title=test_title,
            properties={"Name": {"title": {}}}  # Minimal schema
        )
        
        database_id = database["id"]
        
        # Verify we can read the database
        retrieved = await databases_api.get_database(database_id)
        assert retrieved["title"][0]["text"]["content"] == test_title
        
        # Cleanup: Archive the database
        await databases_api.update_database(
            database_id=database_id,
            properties={"archived": True}
        )
        
        # Test passed if we got here
        assert True, "API authorization validated successfully"
        
    except Exception as e:
        pytest.fail(f"API authorization test failed: {str(e)}")

@pytest_asyncio.fixture
async def test_database(http_client):
    """Create and cleanup test database"""
    databases_api = DatabasesAPI(http_client)
    
    # Create a test database
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    database = await databases_api.create_database(
        parent_page_id=PARENT_PAGE_ID,
        title=f"Test Todo Database {timestamp}",
        properties=TODO_DATABASE_SCHEMA
    )
    
    database_id = database["id"]
    
    # Update environment for other tests
    os.environ["NOTION_DATABASE_ID"] = database_id
    
    yield database_id
    
    # Cleanup: Archive the test database
    try:
        await databases_api.update_database(
            database_id=database_id,
            properties={"archived": True}
        )
    except Exception as e:
        print(f"Error cleaning up test database {database_id}: {e}")

@pytest_asyncio.fixture
async def server():
    """Create NotionServer instance for tests"""
    config = ServerConfig(
        NOTION_API_KEY=NOTION_API_KEY,
        NOTION_DATABASE_ID=DATABASE_ID,
        NOTION_PARENT_PAGE_ID=PARENT_PAGE_ID
    )
    server = NotionServer(config)
    yield server
    await server.close()

@pytest_asyncio.fixture
async def cleanup_todos(http_client, test_database):
    """Cleanup test todos after tests"""
    created_pages = []
    
    yield created_pages
    
    # Cleanup after tests
    databases_api = DatabasesAPI(http_client)
    for page_id in created_pages:
        try:
            await databases_api.update_page(
                page_id,
                archived=True
            )
        except Exception as e:
            print(f"Error cleaning up todo {page_id}: {e}")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_todo_lifecycle(server, cleanup_todos):
    """
    Integration test for complete todo lifecycle.
    Tests creation, update, and completion of a todo.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_task = f"Lifecycle Test Todo {timestamp}"
    
    # 1. Create todo
    create_result = await server.app.call_tool("add_todo", {
        "task": test_task,
        "description": "Initial description",
        "priority": "medium",
        "status": "Not Started"
    })
    
    # Get page ID for updates and cleanup
    page_url = create_result[0].text.split("\n")[1].strip()
    page_id = page_url.split("-")[-1]
    cleanup_todos.append(page_id)
    
    # 2. Update todo
    update_result = await server.app.call_tool("update_todo", {
        "id": page_id,
        "description": "Updated description",
        "priority": "high",
        "status": "In Progress"
    })
    
    # Verify update
    assert "Todo updated" in update_result[0].text
    
    # 3. Complete todo
    complete_result = await server.app.call_tool("update_todo", {
        "id": page_id,
        "status": "Done"
    })
    
    # Verify completion
    assert "Todo updated" in complete_result[0].text
    
    # 4. Verify final state
    search_result = await server.app.call_tool("search_todos", {
        "query": test_task
    })
    
    result_text = search_result[0].text
    assert "Done" in result_text
    assert "high" in result_text
    assert "Updated description" in result_text