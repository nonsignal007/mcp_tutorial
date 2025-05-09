"""Test response models and validation."""
import pytest
from datetime import datetime
from pydantic import ValidationError
from notion_api_mcp.models.responses import (
    User,
    Parent,
    DatabaseObject,
    PageObject,
    BlockObject,
    PaginatedList,
    DatabaseList,
    PageList,
    BlockList,
    ErrorResponse,
    SearchResponse,
    PropertyItemResponse,
    PropertyItemList,
    TodoResponse,
    TodoListResponse
)
from notion_api_mcp.models.properties import (
    PropertySchema,
    PropertyValue,
    TitleProperty,
    RichTextObject,
    RichTextContent,
    RichTextProperty,
    DateValue,
    DateProperty,
    SelectOption,
    SelectProperty,
    MultiSelectProperty
)

# Test User Model
def test_user_model():
    """Test User model validation."""
    # Valid user
    user = User(
        object="user",
        id="user_123",
        type="person",
        name="Test User",
        avatar_url="https://example.com/avatar.jpg"
    )
    assert user.id == "user_123"
    assert user.name == "Test User"

    # Invalid object type
    with pytest.raises(ValidationError):
        User(object="invalid", id="user_123", type="person")

# Test Parent Model
def test_parent_model():
    """Test Parent model validation."""
    # Page parent
    parent = Parent(type="page_id", page_id="page_123")
    assert parent.type == "page_id"
    assert parent.page_id == "page_123"

    # Database parent
    parent = Parent(type="database_id", database_id="db_123")
    assert parent.type == "database_id"
    assert parent.database_id == "db_123"

    # Workspace parent
    parent = Parent(type="workspace", workspace=True)
    assert parent.type == "workspace"
    assert parent.workspace is True

# Test DatabaseObject Model
def test_database_object():
    """Test DatabaseObject model validation."""
    now = datetime.now()
    db = DatabaseObject(
        object="database",
        id="db_123",
        created_time=now,
        last_edited_time=now,
        title=[{"text": {"content": "Test DB"}}],
        properties={
            "Name": PropertySchema(
                id="title",
                name="Name",
                type="title"
            )
        },
        parent=Parent(type="workspace", workspace=True),
        url="https://notion.so/db_123"
    )
    assert db.id == "db_123"
    assert db.title[0]["text"]["content"] == "Test DB"
    assert isinstance(db.properties["Name"], PropertySchema)

# Test PageObject Model
def test_page_object():
    """Test PageObject model validation."""
    now = datetime.now()
    user = User(object="user", id="user_123", type="person")
    page = PageObject(
        object="page",
        id="page_123",
        created_time=now,
        last_edited_time=now,
        created_by=user,
        last_edited_by=user,
        parent=Parent(type="database_id", database_id="db_123"),
        archived=False,
        properties={
            "Title": PropertyValue(
                id="title",
                type="title",
                value=TitleProperty(title=[
                    RichTextObject(text=RichTextContent(content="Test Page"))
                ])
            )
        },
        url="https://notion.so/page_123"
    )
    assert page.id == "page_123"
    assert isinstance(page.properties["Title"], PropertyValue)
    assert page.properties["Title"].value.title[0].text.content == "Test Page"

# Test BlockObject Model
def test_block_object():
    """Test BlockObject model validation."""
    now = datetime.now()
    block = BlockObject(
        object="block",
        id="block_123",
        type="paragraph",
        created_time=now,
        last_edited_time=now,
        has_children=False,
        archived=False,
        type_content={
            "rich_text": [{"text": {"content": "Test content"}}]
        }
    )
    assert block.id == "block_123"
    assert block.content_type == "paragraph"
    assert "rich_text" in block.content

# Test PaginatedList Models
def test_paginated_lists():
    """Test paginated list models."""
    now = datetime.now()
    user = User(object="user", id="user_123", type="person")

    # DatabaseList
    db_list = DatabaseList(
        object="list",
        type="database",
        results=[
            DatabaseObject(
                object="database",
                id="db_123",
                created_time=now,
                last_edited_time=now,
                title=[{"text": {"content": "Test DB"}}],
                properties={},
                parent=Parent(type="workspace", workspace=True),
                url="https://notion.so/db_123"
            )
        ],
        next_cursor="cursor_123",
        has_more=True
    )
    assert db_list.type == "database"
    assert len(db_list.results) == 1
    assert db_list.next_cursor == "cursor_123"

    # PageList
    page_list = PageList(
        object="list",
        type="page",
        results=[
            PageObject(
                object="page",
                id="page_123",
                created_time=now,
                last_edited_time=now,
                created_by=user,
                last_edited_by=user,
                parent=Parent(type="database_id", database_id="db_123"),
                archived=False,
                properties={},
                url="https://notion.so/page_123"
            )
        ],
        has_more=False
    )
    assert page_list.type == "page"
    assert len(page_list.results) == 1
    assert not page_list.has_more

# Test Error Response
def test_error_response():
    """Test ErrorResponse model."""
    error = ErrorResponse(
        object="error",
        status=400,
        code="validation_error",
        message="Invalid request"
    )
    assert error.status == 400
    assert error.code == "validation_error"
    assert error.message == "Invalid request"

# Test TodoResponse
def test_todo_response():
    """Test TodoResponse model and conversion."""
    now = datetime.now()
    user = User(object="user", id="user_123", type="person", name="Test User")

    # Create a page object with todo properties
    page = PageObject(
        object="page",
        id="page_123",
        created_time=now,
        last_edited_time=now,
        created_by=user,
        last_edited_by=user,
        parent=Parent(type="database_id", database_id="db_123"),
        archived=False,
        url="https://notion.so/page_123",
        properties={
            "Task": PropertyValue(
                id="title",
                type="title",
                value=TitleProperty(title=[
                    RichTextObject(text=RichTextContent(content="Test Task"))
                ])
            ),
            "Description": PropertyValue(
                id="rich_text",
                type="rich_text",
                value=RichTextProperty(rich_text=[
                    RichTextObject(text=RichTextContent(content="Test Description"))
                ])
            ),
            "Due Date": PropertyValue(
                id="date",
                type="date",
                value=DateProperty(date=DateValue(start=now))
            ),
            "Priority": PropertyValue(
                id="select",
                type="select",
                value=SelectProperty(select=SelectOption(name="high"))
            ),
            "Tags": PropertyValue(
                id="multi_select",
                type="multi_select",
                value=MultiSelectProperty(multi_select=[
                    SelectOption(name="tag1"),
                    SelectOption(name="tag2")
                ])
            ),
            "Status": PropertyValue(
                id="status",
                type="status",
                value=SelectProperty(select=SelectOption(name="in_progress"))
            )
        }
    )

    # Convert to TodoResponse
    todo = TodoResponse.from_page_object(page)
    assert todo.id == "page_123"
    assert todo.task == "Test Task"
    assert todo.description == "Test Description"
    assert todo.due_date == now
    assert todo.priority == "high"
    assert todo.tags == ["tag1", "tag2"]
    assert todo.status == "in_progress"
    assert todo.created_by == "Test User"

# Test TodoListResponse
def test_todo_list_response():
    """Test TodoListResponse model."""
    now = datetime.now()
    todo_list = TodoListResponse(
        todos=[
            TodoResponse(
                id="todo_123",
                url="https://notion.so/todo_123",
                task="Test Task",
                description="Test Description",
                due_date=now,
                priority="high",
                tags=["tag1", "tag2"],
                status="in_progress",
                created_time=now,
                last_edited_time=now,
                created_by="Test User",
                last_edited_by="Test User"
            )
        ],
        next_cursor="cursor_123",
        has_more=True
    )
    assert len(todo_list.todos) == 1
    assert todo_list.next_cursor == "cursor_123"
    assert todo_list.has_more