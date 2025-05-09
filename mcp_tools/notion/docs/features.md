# Features

## Core Functionality
- Clean async implementation using httpx
- Type-safe configuration using Pydantic
- Simple configuration via environment variables
- Comprehensive error handling
- Resource cleanup and connection management

## Database Operations

The create_database tool allows you to create new databases in Notion. Important notes:
- The parent must be a Notion page that has granted access to your integration
- Currently, databases can only be created as children of Notion pages or wiki databases (Notion API limitation)
- Once created, databases cannot be moved to a different parent

Example database creation:
```python
{
  "parent_page_id": "your_page_id",
  "title": "My Tasks",
  "properties": {
    "Name": {"title": {}},
    "Status": {
      "select": {
        "options": [
          {"name": "Not Started", "color": "red"},
          {"name": "In Progress", "color": "yellow"},
          {"name": "Done", "color": "green"}
        ]
      }
    }
  }
}
```

Other database features:
- Dynamic property types including select, multi-select, date, number, formula
- Advanced filtering with multiple conditions (AND/OR logic)
- Rich sorting options combining multiple properties
- Smart pagination for efficient data access
- Powerful search across all content

## Todo Management
- Rich text descriptions with full Markdown and inline code support
- Flexible due dates with timezone-aware scheduling and reminders
- Customizable priority levels (high/medium/low) with visual indicators
- Dynamic status tracking (Not Started, In Progress, Completed, etc.)
- Hierarchical categories and multiple tags for powerful organization
- Collaborative task notes and threaded comments
- Nested subtasks with independent progress tracking
- Database templates for recurring task patterns (Note: Template blocks deprecated as of March 27, 2023)

## Content Management
- Rich text formatting with support for headings, quotes, callouts, and code blocks
- Structured block operations for content organization
- Smart link previews and embeds
- Hierarchical list management
- Advanced block features including synced blocks and database views