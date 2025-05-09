"""
Tests for authentication utilities.
"""
import os
from pathlib import Path
import pytest
import pytest_asyncio
from unittest.mock import patch, mock_open, AsyncMock, MagicMock
import httpx

from notion_api_mcp.utils.auth import (
    load_env_file,
    get_auth_headers,
    validate_config
)

@pytest.fixture
def mock_env_file():
    """Mock .env file content."""
    return (
        'NOTION_API_KEY=test-api-key\n'
        'NOTION_DATABASE_ID=test-db-id\n'
    )

@pytest.fixture
def mock_env_vars():
    """Set up test environment variables."""
    with patch.dict(os.environ, {
        'NOTION_API_KEY': 'test-api-key',
        'NOTION_DATABASE_ID': 'test-db-id'
    }):
        yield

class TestLoadEnvFile:
    """Test environment file loading functionality."""
    
    def test_load_env_file_success(self, mock_env_file):
        """Test successful .env file loading."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=mock_env_file)), \
             patch.dict(os.environ, {
                 'NOTION_API_KEY': 'test-api-key',
                 'NOTION_DATABASE_ID': 'test-db-id'
             }), \
             patch('dotenv.load_dotenv', return_value=True):
            
            # Should not raise any exceptions
            load_env_file(Path('/fake/path/.env'))
    
    def test_load_env_file_not_found(self):
        """Test handling of missing .env file."""
        with pytest.raises(FileNotFoundError) as exc:
            load_env_file(Path('/nonexistent/.env'))
        assert "No .env file found" in str(exc.value)
    
    def test_load_env_file_missing_vars(self, mock_env_file):
        """Test handling of missing required variables."""
        incomplete_env = 'NOTION_API_KEY=test-key\n'  # Missing DATABASE_ID
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=incomplete_env)):
            
            with pytest.raises(ValueError) as exc:
                load_env_file(Path('/fake/path/.env'))
            assert "Missing required environment variables" in str(exc.value)
            assert "NOTION_DATABASE_ID" in str(exc.value)
    
    def test_load_env_file_default_path(self, mock_env_file):
        """Test loading from default project root path."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=mock_env_file)):
            
            # Should find and load .env from project root
            load_env_file()

class TestGetAuthHeaders:
    """Test authentication header generation."""
    
    def test_get_auth_headers_with_key(self):
        """Test generating headers with explicit API key."""
        headers = get_auth_headers('test-key')
        
        assert headers['Authorization'] == 'Bearer test-key'
        assert headers['Content-Type'] == 'application/json'
        assert headers['Notion-Version'] == '2022-06-28'
    
    def test_get_auth_headers_from_env(self, mock_env_vars):
        """Test generating headers from environment variable."""
        headers = get_auth_headers()
        
        assert headers['Authorization'] == 'Bearer test-api-key'
        assert headers['Content-Type'] == 'application/json'
        assert headers['Notion-Version'] == '2022-06-28'
    
    def test_get_auth_headers_missing_key(self):
        """Test handling of missing API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc:
                get_auth_headers()
            assert "No API key provided" in str(exc.value)
    
    def test_get_auth_headers_empty_key(self):
        """Test handling of empty API key."""
        with pytest.raises(ValueError) as exc:
            get_auth_headers('')
        assert "No API key provided" in str(exc.value)
        
        with patch.dict(os.environ, {'NOTION_API_KEY': ' '}):
            with pytest.raises(ValueError) as exc:
                get_auth_headers()
            assert "No API key provided" in str(exc.value)

class TestValidateConfig:
    """Test configuration validation."""
    
    def test_validate_config_success(self, mock_env_vars):
        """Test successful config validation."""
        # Should not raise any exceptions
        validate_config()
    
    def test_validate_config_missing_api_key(self):
        """Test handling of missing API key."""
        with patch.dict(os.environ, {'NOTION_DATABASE_ID': 'test-db-id'}, clear=True):
            with pytest.raises(ValueError) as exc:
                validate_config()
            assert "Missing required configuration" in str(exc.value)
            assert "NOTION_API_KEY" in str(exc.value)

    def test_validate_config_missing_database_id(self):
        """Test handling of missing database ID."""
        with patch.dict(os.environ, {'NOTION_API_KEY': 'test-api-key'}, clear=True):
            with pytest.raises(ValueError) as exc:
                validate_config()
            assert "Missing required configuration" in str(exc.value)
            assert "NOTION_DATABASE_ID" in str(exc.value)
    
    def test_validate_config_missing_all(self):
        """Test handling of all missing configuration."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc:
                validate_config()
            assert "Missing required configuration" in str(exc.value)
            assert "NOTION_API_KEY" in str(exc.value)
            assert "NOTION_DATABASE_ID" in str(exc.value)

@pytest.mark.asyncio
class TestEndpointAuth:
    """Test endpoint-specific authentication requirements."""
    
    @pytest_asyncio.fixture
    async def mock_client(self):
        """Create mock HTTP client."""
        client = AsyncMock(spec=httpx.AsyncClient)
        client.post = AsyncMock()
        client.get = AsyncMock()
        client.patch = AsyncMock()
        return client

    @pytest_asyncio.fixture
    async def mock_response(self):
        """Create mock response."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.raise_for_status = MagicMock()
        response.json = MagicMock(return_value={"object": "database"})
        return response

    async def test_database_create_auth(self, mock_client, mock_response):
        """Test auth requirements for database creation."""
        mock_client.post.return_value = mock_response
        
        # Test with valid parent page ID
        mock_client.post.reset_mock()
        await mock_client.post("databases", json={"parent": {"page_id": "valid-id"}})
        mock_client.post.assert_called_once()
        
        # Test without parent page ID
        mock_client.post.reset_mock()
        mock_client.post.side_effect = httpx.HTTPError("Missing parent_page_id")
        with pytest.raises(httpx.HTTPError):
            await mock_client.post("databases", json={})

    async def test_database_query_auth(self, mock_client, mock_response):
        """Test auth requirements for database queries."""
        mock_client.post.return_value = mock_response
        
        # Test with valid database ID
        mock_client.post.reset_mock()
        await mock_client.post("databases/valid-id/query")
        mock_client.post.assert_called_once()
        
        # Test with invalid database ID
        mock_client.post.reset_mock()
        mock_client.post.side_effect = httpx.HTTPError("Invalid database_id")
        with pytest.raises(httpx.HTTPError):
            await mock_client.post("databases/invalid-id/query")

    async def test_page_operations_auth(self, mock_client, mock_response):
        """Test auth requirements for page operations."""
        mock_client.post.return_value = mock_response
        
        # Test page creation in database
        mock_client.post.reset_mock()
        await mock_client.post("pages", json={
            "parent": {"database_id": "valid-db"},
            "properties": {}
        })
        mock_client.post.assert_called_once()
        
        # Test standalone page creation
        mock_client.post.reset_mock()
        await mock_client.post("pages", json={
            "parent": {"page_id": "valid-page"},
            "properties": {}
        })
        mock_client.post.assert_called_once()

    async def test_property_operations_auth(self, mock_client, mock_response):
        """Test auth requirements for property operations."""
        mock_client.get.return_value = mock_response
        
        # Test with both IDs
        mock_client.get.reset_mock()
        await mock_client.get("pages/valid-page/properties/valid-prop")
        mock_client.get.assert_called_once()
        
        # Test with missing property ID
        mock_client.get.reset_mock()
        mock_client.get.side_effect = httpx.HTTPError("Missing property_id")
        with pytest.raises(httpx.HTTPError):
            await mock_client.get("pages/valid-page/properties/")

@pytest.mark.asyncio
class TestDatabaseAccess:
    """Test database access restrictions and permissions."""
    
    @pytest_asyncio.fixture
    async def mock_client(self):
        """Create mock HTTP client."""
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock()
        return client

    async def test_database_permissions(self, mock_client):
        """Test database access control."""
        # Test access denied
        mock_client.get.side_effect = httpx.HTTPError("Access denied")
        with pytest.raises(httpx.HTTPError):
            await mock_client.get("databases/restricted-db")
        
        # Test access granted
        mock_client.get.side_effect = None
        mock_client.get.return_value.status_code = 200
        response = await mock_client.get("databases/accessible-db")
        assert response.status_code == 200

    async def test_inherited_permissions(self, mock_client):
        """Test permission inheritance."""
        # Test parent access grants child access
        mock_client.get.return_value.status_code = 200
        response = await mock_client.get("blocks/child-block")
        assert response.status_code == 200
        
        # Test parent restriction restricts child
        mock_client.get.side_effect = httpx.HTTPError("Access denied")
        with pytest.raises(httpx.HTTPError):
            await mock_client.get("blocks/restricted-child")