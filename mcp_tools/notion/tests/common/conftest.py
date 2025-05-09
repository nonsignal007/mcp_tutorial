"""
Common test fixtures and configuration.
"""
import os
import pytest
import pytest_asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv

from notion_api_mcp.utils.auth import get_auth_headers
import structlog

logger = structlog.get_logger()

# Load integration test environment
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env.integration'

if not env_path.exists():
    pytest.skip(
        "Skipping integration tests: .env.integration not found. "
        "Create this file with required tokens to run integration tests.",
        allow_module_level=True
    )

load_dotenv(env_path)
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_READONLY_API_KEY = os.getenv("NOTION_READONLY_API_KEY")
PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID")

# Track resources created during tests
test_resources = {
    "pages": set(),
    "databases": set(),
    "blocks": set()
}

@pytest.fixture(autouse=True)
async def cleanup_test_resources():
    """Automatically clean up test resources after each test."""
    yield  # Run the test
    
    # Clean up resources in reverse order of creation
    async with httpx.AsyncClient() as client:
        headers = get_auth_headers(NOTION_API_KEY)
        client.headers.update(headers)
        
        # Delete blocks
        for block_id in test_resources["blocks"]:
            try:
                await client.delete(f"blocks/{block_id}")
                logger.info("Cleaned up block", block_id=block_id)
            except httpx.HTTPError as e:
                logger.warning("Failed to cleanup block", block_id=block_id, error=str(e))
        
        # Delete pages
        for page_id in test_resources["pages"]:
            try:
                await client.delete(f"pages/{page_id}")
                logger.info("Cleaned up page", page_id=page_id)
            except httpx.HTTPError as e:
                logger.warning("Failed to cleanup page", page_id=page_id, error=str(e))
        
        # Delete databases
        for db_id in test_resources["databases"]:
            try:
                await client.delete(f"databases/{db_id}")
                logger.info("Cleaned up database", database_id=db_id)
            except httpx.HTTPError as e:
                logger.warning("Failed to cleanup database", database_id=db_id, error=str(e))
        
        # Clear tracked resources
        test_resources["blocks"].clear()
        test_resources["pages"].clear()
        test_resources["databases"].clear()

if not all([NOTION_API_KEY, NOTION_READONLY_API_KEY, PARENT_PAGE_ID]):
    pytest.skip(
        "Skipping integration tests: Missing required environment variables. "
        "Ensure all required variables are set in .env.integration",
        allow_module_level=True
    )

@pytest_asyncio.fixture
async def full_access_client():
    """Create HTTP client with full access token"""
    headers = get_auth_headers(NOTION_API_KEY)
    async with httpx.AsyncClient(
        base_url="https://api.notion.com/v1/",
        timeout=30.0,
        headers=headers
    ) as client:
        yield client

@pytest_asyncio.fixture
async def readonly_client():
    """Create HTTP client with read-only token"""
    headers = get_auth_headers(NOTION_READONLY_API_KEY)
    async with httpx.AsyncClient(
        base_url="https://api.notion.com/v1/",
        timeout=30.0,
        headers=headers
    ) as client:
        yield client

@pytest_asyncio.fixture
async def invalid_client():
    """Create HTTP client with invalid auth token"""
    headers = get_auth_headers("invalid_token_for_testing")
    async with httpx.AsyncClient(
        base_url="https://api.notion.com/v1/",
        timeout=30.0,
        headers=headers
    ) as client:
        yield client

def strip_hyphens(page_id: str) -> str:
    """Remove hyphens from page ID for API calls"""
    return page_id.replace("-", "") if page_id else None

def format_page_url(page_id: str) -> str:
    """Format a Notion page URL for sharing"""
    return f"https://notion.so/{page_id.replace('-', '')}"