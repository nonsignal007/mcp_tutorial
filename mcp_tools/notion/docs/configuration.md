# Configuration Details

## Environment Variables

The server supports configuration through both a .env file and system environment variables. When both are present, system environment variables (including those set in the Claude Desktop MCP config) take precedence over .env file values.

Required:
- `NOTION_API_KEY`: Your Notion API integration token
  - Must start with "ntn_"
  - Get from https://www.notion.so/my-integrations

Optional (at least one is required):
- `NOTION_PARENT_PAGE_ID`: ID of a Notion page where you want to create new databases
  - Must be a page that has granted access to your integration
  - Required if you want to create new databases
  - Get from the page's URL

- `NOTION_DATABASE_ID`: ID of an existing database
  - Must be a database that has granted access to your integration
  - Required if you want to work with an existing database
  - Get from the database's URL

## Configuration Sources

You can provide these variables in two ways:

1. Environment File (.env):
```env
NOTION_API_KEY=ntn_your_integration_token_here
NOTION_PARENT_PAGE_ID=your_page_id_here
NOTION_DATABASE_ID=your_database_id_here
```

2. Claude Desktop MCP Config:
```json
{
  "mcpServers": {
    "notion-api": {
      "command": "/path/to/your/.venv/bin/python",
      "args": ["-m", "notion_api_mcp"],
      "env": {
        "NOTION_API_KEY": "ntn_your_integration_token_here",
        "NOTION_PARENT_PAGE_ID": "your_page_id_here",
        "NOTION_DATABASE_ID": "your_database_id_here"
      }
    }
  }
}
```

The server will:
1. First load any values from your .env file
2. Then apply any system environment variables (including those from MCP config)
3. System environment variables take precedence over .env values

This means you can:
- Use .env for local development and testing
- Override values via MCP config for production use
- Mix and match sources (e.g., some values in .env, others in MCP config)