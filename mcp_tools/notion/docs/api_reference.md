# Notion API Quick Reference for MCP Implementation

## Base Configuration
- Base URL: `https://api.notion.com`
- HTTPS required for all requests
- Authentication: Integration token required via `Authorization` header
- API Version: Specified via `Notion-Version` header

## Core Concepts
1. Resource Properties:
   - All resources have an `"object"` property identifying type
   - Resources identified by UUIDv4 `"id"` (dashes optional)
   - Property names use `snake_case`
   - Empty strings not supported (use `null` instead)

2. Data Formats:
   - Request/response bodies: JSON
   - Dates: ISO 8601
     - Datetime: `2020-08-12T02:12:33.231Z`
     - Date only: `2020-08-12`

3. Pagination Support:
   - Default: 10 items per call
   - Response Fields:
     - `has_more`: boolean indicating more results
     - `next_cursor`: string for retrieving next page
     - `object`: constant "list"
     - `results`: array of objects
     - `type`: indicates object type in results

4. Pagination Parameters:
   - `page_size`: 
     - Default: 100
     - Maximum: 100
   - `start_cursor`: opaque value from previous response

## Current Implementation Status
- [x] Basic CRUD operations
- [x] Authentication handling
- [x] Error handling
- [x] Pagination support
- [x] Rate limiting
- [x] Comprehensive error recovery
- [x] Request retries
- [x] Request timeouts

## Implemented Features

### Database Operations
- Create database with todo schema
- Add multiple todos
- Query with basic filters
- Multi-criteria filtering
- Sorting capabilities
- Date range queries
- Pagination support
- Search implementation

### Content Management
- Block operations (create, update, delete)
- Rich text formatting
- Link embedding
- List support
- Subtasks
- Nested block handling

### Authentication & Permissions
- Token-based authentication
- Parent-child ID relationships
- Permission inheritance
- Integration access validation
- Error handling for invalid tokens
- Automated test page sharing

### Query Operations
- Basic pagination
- Multi-criteria filtering
- Sort by various properties
- Date range filtering
- Search functionality

## API Endpoints

### Databases
- POST /v1/databases
  - Create a new database
- GET /v1/databases/:id
  - Retrieve database details
- POST /v1/databases/:id/query
  - Query database with filters
- PATCH /v1/databases/:id
  - Update database properties

### Pages
- POST /v1/pages
  - Create a new page
- GET /v1/pages/:id
  - Retrieve page details
- PATCH /v1/pages/:id
  - Update page properties
- GET /v1/pages/:id/properties/:id
  - Retrieve page property

### Blocks
- GET /v1/blocks/:id
  - Retrieve block details
- PATCH /v1/blocks/:id
  - Update block content
- DELETE /v1/blocks/:id
  - Delete a block
- GET /v1/blocks/:id/children
  - List block children
- PATCH /v1/blocks/:id/children
  - Append block children

## Implementation Notes
- GET requests: parameters in query string
- POST requests: parameters in request body
- Empty strings not allowed (use null)
- Cursor-based pagination implemented for list operations
- Rate limiting with exponential backoff
- Comprehensive error handling with detailed responses
- Request retries for transient failures
- Request timeouts configured
- Permission inheritance verified at multiple levels
