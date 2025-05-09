# Notion API MCP

A Model Context Protocol (MCP) server that provides advanced todo list management and content organization capabilities through Notion's API. MCP enables AI models to interact with external tools and services, allowing seamless integration with Notion's powerful features.

## MCP Overview

Python-based MCP server that enables AI models to interact with Notion's API, providing:
- **Todo Management**: Create, update, and track tasks with rich text, due dates, priorities, and nested subtasks
- **Database Operations**: Create and manage Notion databases with custom properties, filters, and views
- **Content Organization**: Structure and format content with Markdown support, hierarchical lists, and block operations
- **Real-time Integration**: Direct interaction with Notion's workspace, pages, and databases through clean async implementation

[Full feature list →](docs/features.md)

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/notion-api-mcp.git
cd notion-api-mcp
uv venv && source .venv/bin/activate

# Install and configure
uv pip install -e .
cp .env.integration.template .env

# Add your Notion credentials to .env:
# NOTION_API_KEY=ntn_your_integration_token_here
# NOTION_PARENT_PAGE_ID=your_page_id_here  # For new databases
# NOTION_DATABASE_ID=your_database_id_here  # For existing databases

# Run the server
python -m notion_api_mcp
```

## Getting Started

### 1. Create a Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Name your integration (e.g., "My MCP Integration")
4. Select the workspace where you'll use the integration
5. Copy the "Internal Integration Token" - this will be your `NOTION_API_KEY`
   - Should start with "ntn_"

### 2. Set Up Notion Access

You'll need either a parent page (for creating new databases) or an existing database ID:

#### Option A: Parent Page for New Databases
1. Open Notion in your browser
2. Create a new page or open an existing one where you want to create databases
3. Click the ••• menu in the top right
4. Select "Add connections" and choose your integration
5. Copy the page ID from the URL - it's the string after the last slash and before the question mark
   - Example: In `https://notion.so/myworkspace/123456abcdef...`, the ID is `123456abcdef...`
   - This will be your `NOTION_PARENT_PAGE_ID`

#### Option B: Existing Database
1. Open your existing Notion database
2. Make sure it's connected to your integration (••• menu > Add connections)
3. Copy the database ID from the URL
   - Example: In `https://notion.so/myworkspace/123456abcdef...?v=...`, the ID is `123456abcdef...`
   - This will be your `NOTION_DATABASE_ID`

### 3. Install the MCP Server

1. Create virtual environment:
```bash
cd notion-api-mcp
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
uv pip install -e .
```

3. Configure environment:
```bash
cp .env.integration.template .env
```

4. Edit .env with your Notion credentials:
```env
NOTION_API_KEY=ntn_your_integration_token_here

# Choose one or both of these depending on your needs:
NOTION_PARENT_PAGE_ID=your_page_id_here  # For creating new databases
NOTION_DATABASE_ID=your_database_id_here  # For working with existing databases
```

### 4. Configure Claude Desktop

IMPORTANT: While the server supports both .env files and environment variables, Claude Desktop specifically requires configuration in its config file to use the MCP.

Add to Claude Desktop's config (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "notion-api": {
      "command": "/path/to/your/.venv/bin/python",
      "args": ["-m", "notion_api_mcp"],
      "env": {
        "NOTION_API_KEY": "ntn_your_integration_token_here",
        
        // Choose one or both:
        "NOTION_PARENT_PAGE_ID": "your_page_id_here",
        "NOTION_DATABASE_ID": "your_database_id_here"
      }
    }
  }
}
```

Note: Even if you have a .env file configured, you must add these environment variables to the Claude Desktop config for Claude to use the MCP. The .env file is primarily for local development and testing.

## Documentation

- [Configuration Details](docs/configuration.md) - Detailed configuration options and environment variables
- [Features](docs/features.md) - Complete feature list and capabilities
- [Architecture](docs/ARCHITECTURE.md) - Overview of available tools and usage examples
- [API Reference](docs/api_reference.md) - Detailed API endpoints and implementation details
- [Test Coverage Matrix](docs/test_coverage_matrix.md) - Test coverage and validation status
- [Dependencies](docs/dependencies.md) - Project dependencies and version information
- [Changelog](docs/CHANGELOG.md) - Development progress and updates

## Development

The server uses modern Python async features throughout:
- Type-safe configuration using Pydantic models
- Async HTTP using httpx for better performance
- Clean MCP integration for exposing Notion capabilities
- Proper resource cleanup and error handling

### Debugging

The server includes comprehensive logging:
- Console output for development
- File logging when running as a service
- Detailed error messages
- Request/response logging at debug level

Set `PYTHONPATH` to include the project root when running directly:

```bash
PYTHONPATH=/path/to/project python -m notion_api_mcp
```

## Future Development

Planned enhancements:
1. Performance Optimization
   - Add request caching
   - Optimize database queries
   - Implement connection pooling

2. Advanced Features
   - Multi-workspace support
   - Batch operations
   - Real-time updates
   - Advanced search capabilities

3. Developer Experience
   - Interactive API documentation
   - CLI tools for common operations
   - Additional code examples
   - Performance monitoring

4. Testing Enhancements
   - Performance benchmarks
   - Load testing
   - Additional edge cases
   - Extended integration tests