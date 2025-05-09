"""Test property models and validation."""
import pytest
from datetime import datetime
from pydantic import ValidationError
from notion_api_mcp.models.properties import (
    MAX_TEXT_LENGTH,
    MAX_TITLE_LENGTH,
    RichTextContent,
    RichTextObject,
    TitleProperty,
    RichTextProperty,
    DateValue,
    DateProperty,
    SelectOption,
    SelectProperty,
    MultiSelectProperty,
    NumberProperty,
    CheckboxProperty,
    StatusProperty,
    PropertyValue,
    PropertySchema,
    TodoProperties
)

# Test RichTextContent
def test_rich_text_content_validation():
    """Test RichTextContent validation."""
    # Valid content
    content = RichTextContent(content="Test content")
    assert content.content == "Test content"
    assert content.link is None

    # Empty content
    with pytest.raises(ValidationError) as exc:
        RichTextContent(content="")
    assert "Content cannot be empty" in str(exc.value)

    # Whitespace content
    with pytest.raises(ValidationError) as exc:
        RichTextContent(content="   ")
    assert "Content cannot be empty" in str(exc.value)

    # Content too long
    with pytest.raises(ValidationError) as exc:
        RichTextContent(content="x" * (MAX_TEXT_LENGTH + 1))
    assert f"Content length exceeds maximum of {MAX_TEXT_LENGTH}" in str(exc.value)

    # Content with link
    content = RichTextContent(
        content="Test with link",
        link={"url": "https://example.com"}
    )
    assert content.link == {"url": "https://example.com"}

# Test RichTextObject
def test_rich_text_object_validation():
    """Test RichTextObject validation."""
    # Valid object
    obj = RichTextObject(
        text=RichTextContent(content="Test text"),
        annotations={"bold": True, "italic": False}
    )
    assert obj.type == "text"
    assert obj.text.content == "Test text"
    assert obj.annotations == {"bold": True, "italic": False}

    # Invalid type
    with pytest.raises(ValidationError):
        RichTextObject(
            type="invalid",
            text=RichTextContent(content="Test")
        )

    # Invalid annotations
    with pytest.raises(ValidationError) as exc:
        RichTextObject(
            text=RichTextContent(content="Test"),
            annotations={"invalid_key": True}
        )
    assert "Invalid annotation keys" in str(exc.value)

# Test Property Types
def test_title_property():
    """Test TitleProperty validation."""
    title = TitleProperty(title=[
        RichTextObject(text=RichTextContent(content="Test title"))
    ])
    assert title.type == "title"
    assert len(title.title) == 1
    assert title.title[0].text.content == "Test title"

def test_rich_text_property():
    """Test RichTextProperty validation."""
    prop = RichTextProperty(rich_text=[
        RichTextObject(text=RichTextContent(content="Test text"))
    ])
    assert prop.type == "rich_text"
    assert len(prop.rich_text) == 1
    assert prop.rich_text[0].text.content == "Test text"

def test_date_property():
    """Test DateProperty validation."""
    now = datetime.now()
    date = DateProperty(date=DateValue(
        start=now,
        end=now,
        time_zone="UTC"
    ))
    assert date.type == "date"
    assert date.date.start == now
    assert date.date.end == now
    assert date.date.time_zone == "UTC"

def test_select_property():
    """Test SelectProperty validation."""
    select = SelectProperty(select=SelectOption(
        name="Option 1",
        color="blue"
    ))
    assert select.type == "select"
    assert select.select.name == "Option 1"
    assert select.select.color == "blue"

def test_multi_select_property():
    """Test MultiSelectProperty validation."""
    multi = MultiSelectProperty(multi_select=[
        SelectOption(name="Tag 1", color="red"),
        SelectOption(name="Tag 2", color="blue")
    ])
    assert multi.type == "multi_select"
    assert len(multi.multi_select) == 2
    assert multi.multi_select[0].name == "Tag 1"
    assert multi.multi_select[1].color == "blue"

def test_number_property():
    """Test NumberProperty validation."""
    num = NumberProperty(number=42.5, format="number")
    assert num.type == "number"
    assert num.number == 42.5
    assert num.format == "number"

def test_checkbox_property():
    """Test CheckboxProperty validation."""
    checkbox = CheckboxProperty(checkbox=True)
    assert checkbox.type == "checkbox"
    assert checkbox.checkbox is True

def test_status_property():
    """Test StatusProperty validation."""
    status = StatusProperty(status=SelectOption(
        name="In Progress",
        color="yellow"
    ))
    assert status.type == "status"
    assert status.status.name == "In Progress"
    assert status.status.color == "yellow"

# Test TodoProperties
def test_todo_properties_validation():
    """Test TodoProperties validation."""
    # Valid properties
    todo = TodoProperties(
        task="Test task",
        description="Test description",
        due_date=datetime.now(),
        priority="high",
        tags=["tag1", "tag2"],
        status="in_progress"
    )
    assert todo.task == "Test task"
    assert todo.description == "Test description"
    assert todo.priority == "high"
    assert todo.status == "in_progress"

    # Invalid task (empty)
    with pytest.raises(ValidationError) as exc:
        TodoProperties(task="")
    assert "Task title cannot be empty" in str(exc.value)

    # Invalid task (too long)
    with pytest.raises(ValidationError) as exc:
        TodoProperties(task="x" * (MAX_TITLE_LENGTH + 1))
    assert f"Task title exceeds maximum of {MAX_TITLE_LENGTH}" in str(exc.value)

    # Invalid priority
    with pytest.raises(ValidationError):
        TodoProperties(task="Test", priority="invalid")

    # Invalid status
    with pytest.raises(ValidationError):
        TodoProperties(task="Test", status="invalid")

def test_todo_properties_conversion():
    """Test TodoProperties conversion methods."""
    now = datetime.now()
    todo = TodoProperties(
        task="Test task",
        description="Test description",
        due_date=now,
        priority="high",
        tags=["tag1", "tag2"],
        status="in_progress"
    )

    # Test to_notion_properties
    notion_props = todo.to_notion_properties()
    assert notion_props["Task"]["title"][0]["text"]["content"] == "Test task"
    assert notion_props["Description"]["rich_text"][0]["text"]["content"] == "Test description"
    assert notion_props["Due Date"]["date"]["start"] == now.isoformat()
    assert notion_props["Priority"]["select"]["name"] == "high"
    assert notion_props["Tags"]["multi_select"][0]["name"] == "tag1"
    assert notion_props["Status"]["status"]["name"] == "in_progress"

    # Test from_notion_properties
    todo2 = TodoProperties.from_notion_properties(notion_props)
    assert todo2.task == todo.task
    assert todo2.description == todo.description
    assert todo2.priority == todo.priority
    assert todo2.tags == todo.tags
    assert todo2.status == todo.status

def test_property_schema():
    """Test PropertySchema validation."""
    schema = PropertySchema(
        id="prop_id",
        name="Test Property",
        type="select",
        config={"options": [{"name": "Option 1", "color": "blue"}]}
    )
    assert schema.id == "prop_id"
    assert schema.name == "Test Property"
    assert schema.type == "select"
    assert "options" in schema.config

def test_property_value():
    """Test PropertyValue validation."""
    value = PropertyValue(
        id="prop_id",
        type="select",
        value=SelectProperty(select=SelectOption(name="Option 1"))
    )
    assert value.id == "prop_id"
    assert value.type == "select"
    assert isinstance(value.value, SelectProperty)
    assert value.value.select.name == "Option 1"