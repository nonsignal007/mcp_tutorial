"""Test API module initialization and exports."""
from notion_api_mcp.api import BlocksAPI, DatabasesAPI, PagesAPI

def test_api_exports():
    """Test that API classes are properly exported."""
    # Simply verify we can import the classes
    assert BlocksAPI
    assert DatabasesAPI
    assert PagesAPI