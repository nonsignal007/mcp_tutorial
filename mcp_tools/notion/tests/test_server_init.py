"""Unit tests for server initialization and configuration"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

def mock_load_dotenv(path):
    """Mock dotenv loader that behaves differently based on the path"""
    if '.env.test' in str(path):
        # Set test environment variables when loading .env.test
        os.environ["NOTION_API_KEY"] = "test_api_key"
        os.environ["NOTION_DATABASE_ID"] = "test_database_id"
        return True
    return False

@pytest.fixture(autouse=True)
def clear_module_cache():
    """Clear the module cache before each test"""
    to_delete = [name for name in sys.modules if name.startswith('notion_api_mcp.server')]
    for name in to_delete:
        del sys.modules[name]
    yield

@pytest.fixture
def mock_env():
    """Mock environment variables"""
    with patch.dict(os.environ, {
        "NOTION_API_KEY": "test_api_key",
        "NOTION_DATABASE_ID": "test_database_id",
        "PYTEST_CURRENT_TEST": "test_mode"
    }, clear=True):
        yield

@pytest.fixture
def mock_httpx():
    """Mock httpx client"""
    with patch("httpx.AsyncClient") as mock:
        mock.return_value = MagicMock()
        yield mock

def test_env_variables_missing():
    """Test server initialization with missing environment variables"""
    with patch.dict(os.environ, {}, clear=True):
        with patch("dotenv.load_dotenv", return_value=True):
            with pytest.raises(ValueError, match="NOTION_API_KEY not found"):
                import notion_api_mcp.server

def test_test_mode_env():
    """Test environment loading in test mode"""
    with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_mode"}, clear=True):
        with patch("dotenv.load_dotenv", side_effect=mock_load_dotenv) as mock_dotenv:
            import notion_api_mcp.server
            
            # Should attempt to load .env.test
            mock_dotenv.assert_called_once()
            assert ".env.test" in str(mock_dotenv.call_args[0][0])

def test_production_mode_env():
    """Test environment loading in production mode"""
    with patch.dict(os.environ, {}, clear=True):
        with patch("dotenv.load_dotenv", side_effect=mock_load_dotenv):
            with patch("pathlib.Path.exists", return_value=False):
                with pytest.raises(FileNotFoundError, match="No .env file found"):
                    import notion_api_mcp.server

@pytest.mark.asyncio
async def test_server_initialization(mock_env, mock_httpx):
    """Test complete server initialization"""
    with patch("dotenv.load_dotenv", return_value=True):
        import notion_api_mcp.server
        
        # Initialize clients
        notion_api_mcp.server.init_clients()
        
        # Verify server setup
        assert isinstance(notion_api_mcp.server.server, notion_api_mcp.server.Server)
        assert notion_api_mcp.server.server.name == "notion-todo-enhanced"
        
        # Verify HTTP client configuration
        mock_httpx.assert_called_once()
        call_kwargs = mock_httpx.call_args[1]
        assert call_kwargs["timeout"] == 30.0
        assert "Authorization" in call_kwargs["headers"]
        assert call_kwargs["headers"]["Notion-Version"] == "2022-06-28"
        
        # Verify API clients initialization
        assert notion_api_mcp.server.pages_api._client == notion_api_mcp.server.http_client
        assert notion_api_mcp.server.databases_api._client == notion_api_mcp.server.http_client
        assert notion_api_mcp.server.blocks_api._client == notion_api_mcp.server.http_client

@pytest.mark.asyncio
async def test_tool_registration(mock_env):
    """Test tool registration and listing"""
    with patch("dotenv.load_dotenv", return_value=True):
        import notion_api_mcp.server
        
        # Get registered tools
        tools = await notion_api_mcp.server.list_tools()
        
        # Verify essential tools are registered
        tool_names = {tool.name for tool in tools}
        required_tools = {
            "add_todo",
            "search_todos",
            "create_database"
        }
        assert required_tools.issubset(tool_names)
        
        # Verify tool schemas
        add_todo = next(tool for tool in tools if tool.name == "add_todo")
        assert "task" in add_todo.inputSchema["properties"]
        assert "task" in add_todo.inputSchema["required"]

@pytest.mark.asyncio
async def test_http_client_error_handling(mock_env, mock_httpx):
    """Test HTTP client error handling"""
    with patch("dotenv.load_dotenv", return_value=True):
        import notion_api_mcp.server
        import httpx
        
        # Mock HTTP error
        mock_httpx.return_value.post.side_effect = httpx.HTTPError("API Error")
        mock_httpx.return_value.post.return_value = None  # Ensure post is called
        
        # Test error handling
        result = await notion_api_mcp.server.call_tool("add_todo", {"task": "Test task"})
        assert len(result) == 1
        assert "Error executing add_todo" in result[0].text
        assert "API Error" in result[0].text

@pytest.mark.asyncio
async def test_validation_error_handling(mock_env):
    """Test input validation error handling"""
    with patch("dotenv.load_dotenv", return_value=True):
        import notion_api_mcp.server
        
        # Test with invalid date format
        result = await notion_api_mcp.server.call_tool("add_todo", {
            "task": "Test task",
            "due_date": "invalid-date"
        })
        assert len(result) == 1
        assert "Invalid due date format" in result[0].text

@pytest.mark.asyncio
async def test_unknown_tool_error(mock_env):
    """Test error handling for unknown tools"""
    with patch("dotenv.load_dotenv", return_value=True):
        import notion_api_mcp.server
        
        with pytest.raises(ValueError, match="Unknown tool"):
            await notion_api_mcp.server.call_tool("nonexistent_tool", {})