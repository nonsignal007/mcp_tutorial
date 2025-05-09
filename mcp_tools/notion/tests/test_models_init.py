"""Test models/__init__.py module."""
import pytest
from notion_api_mcp.models import (
    Priority,
    Status,
    BlockType,
    PropertyType,
    TODO_DATABASE_SCHEMA
)

def test_priority_enum():
    """Test Priority enum values and string representations."""
    assert Priority.HIGH == "high"
    assert Priority.MEDIUM == "medium"
    assert Priority.LOW == "low"
    
    # Test all enum values are included
    assert sorted([p.value for p in Priority]) == sorted(["high", "medium", "low"])

def test_status_enum():
    """Test Status enum values and string representations."""
    assert Status.NOT_STARTED == "not_started"
    assert Status.IN_PROGRESS == "in_progress"
    assert Status.COMPLETED == "completed"
    
    # Test all enum values are included
    assert sorted([s.value for s in Status]) == sorted([
        "not_started", "in_progress", "completed"
    ])

def test_block_type_enum():
    """Test BlockType enum values."""
    expected_types = {
        "paragraph", "heading_1", "heading_2", "heading_3",
        "bulleted_list_item", "numbered_list_item", "to_do",
        "toggle", "code", "quote", "callout", "divider"
    }
    
    # Test all enum values are included
    assert set(t.value for t in BlockType) == expected_types

def test_property_type_enum():
    """Test PropertyType enum values."""
    expected_types = {
        "title", "rich_text", "number", "select",
        "multi_select", "date", "checkbox", "status"
    }
    
    # Test all enum values are included
    assert set(t.value for t in PropertyType) == expected_types

def test_todo_database_schema():
    """Test TODO_DATABASE_SCHEMA structure and values."""
    # Test required fields
    required_fields = {
        "Task", "Description", "Due Date",
        "Priority", "Tags", "Status"
    }
    assert set(TODO_DATABASE_SCHEMA.keys()) == required_fields
    
    # Test Task field (title)
    assert TODO_DATABASE_SCHEMA["Task"]["type"] == "title"
    assert "title" in TODO_DATABASE_SCHEMA["Task"]
    
    # Test Description field (rich_text)
    assert TODO_DATABASE_SCHEMA["Description"]["type"] == "rich_text"
    assert "rich_text" in TODO_DATABASE_SCHEMA["Description"]
    
    # Test Due Date field (date)
    assert TODO_DATABASE_SCHEMA["Due Date"]["type"] == "date"
    assert "date" in TODO_DATABASE_SCHEMA["Due Date"]
    
    # Test Priority field (select)
    priority_field = TODO_DATABASE_SCHEMA["Priority"]
    assert priority_field["type"] == "select"
    assert "select" in priority_field
    assert "options" in priority_field["select"]
    
    priority_options = {opt["name"] for opt in priority_field["select"]["options"]}
    assert priority_options == {p.value for p in Priority}
    
    # Test Tags field (multi_select)
    tags_field = TODO_DATABASE_SCHEMA["Tags"]
    assert tags_field["type"] == "multi_select"
    assert "multi_select" in tags_field
    assert "options" in tags_field["multi_select"]
    assert tags_field["multi_select"]["options"] == []  # Empty by default
    
    # Test Status field (status)
    status_field = TODO_DATABASE_SCHEMA["Status"]
    assert status_field["type"] == "status"
    assert "status" in status_field
    assert "options" in status_field["status"]
    
    status_options = {opt["name"] for opt in status_field["status"]["options"]}
    assert status_options == {s.value for s in Status}

def test_schema_color_assignments():
    """Test color assignments in schema options."""
    # Test Priority colors
    priority_options = TODO_DATABASE_SCHEMA["Priority"]["select"]["options"]
    color_map = {opt["name"]: opt["color"] for opt in priority_options}
    assert color_map[Priority.HIGH] == "red"
    assert color_map[Priority.MEDIUM] == "yellow"
    assert color_map[Priority.LOW] == "blue"
    
    # Test Status colors
    status_options = TODO_DATABASE_SCHEMA["Status"]["status"]["options"]
    color_map = {opt["name"]: opt["color"] for opt in status_options}
    assert color_map[Status.NOT_STARTED] == "gray"
    assert color_map[Status.IN_PROGRESS] == "yellow"
    assert color_map[Status.COMPLETED] == "green"