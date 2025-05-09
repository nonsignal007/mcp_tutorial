"""
Comprehensive validation tests for rich text description functionality.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from pydantic import ValidationError
from notion_api_mcp.models.properties import (
    RichTextContent,
    RichTextObject,
    RichTextProperty,
    TodoProperties,
    MAX_TEXT_LENGTH,
    MAX_TITLE_LENGTH
)

# Test Data
MARKDOWN_SAMPLES = [
    ("Basic text", "Simple description"),
    ("Bold text", "This is **bold** text"),
    ("Italic text", "This is *italic* text"),
    ("Combined formatting", "**Bold** and *italic* text"),
    ("Links", "Check [this link](https://example.com)"),
    ("Lists", "- Item 1\n- Item 2\n- Item 3"),
    ("Code blocks", "```python\nprint('hello')\n```"),
    ("Special characters", "Special chars: &<>\"'"),
    ("Unicode", "Unicode: 你好，世界！ 🌎"),
    ("Long text", "x" * 1000),  # Reduced length for valid tests
]

@pytest.fixture
def mock_notion_api():
    """Mock Notion API client"""
    mock = AsyncMock()
    mock.post = AsyncMock(return_value=AsyncMock(
        status_code=200,
        json=AsyncMock(return_value={"object": "page"})
    ))
    return mock

class TestRichTextModels:
    """Test rich text model validation and conversion."""

    def test_rich_text_content_basic(self):
        """Test basic rich text content creation."""
        content = RichTextContent(content="Test content")
        assert content.content == "Test content"
        assert content.link is None

    def test_rich_text_content_with_link(self):
        """Test rich text content with link."""
        content = RichTextContent(
            content="Test with link",
            link={"url": "https://example.com"}
        )
        assert content.link["url"] == "https://example.com"

    def test_rich_text_object_basic(self):
        """Test basic rich text object creation."""
        text = RichTextObject(
            text=RichTextContent(content="Test text")
        )
        assert text.type == "text"
        assert text.text.content == "Test text"
        assert text.annotations is None

    def test_rich_text_object_with_annotations(self):
        """Test rich text object with formatting annotations."""
        text = RichTextObject(
            text=RichTextContent(content="Formatted text"),
            annotations={
                "bold": True,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default"
            }
        )
        assert text.annotations["bold"] is True
        assert text.annotations["color"] == "default"

    @pytest.mark.parametrize("name,content", MARKDOWN_SAMPLES)
    def test_rich_text_content_variations(self, name, content):
        """Test various rich text content patterns."""
        prop = RichTextProperty(rich_text=[
            RichTextObject(text=RichTextContent(content=content))
        ])
        assert prop.type == "rich_text"
        assert prop.rich_text[0].text.content == content

class TestTodoPropertiesRichText:
    """Test rich text handling in todo properties."""

    def test_todo_description_basic(self):
        """Test basic description conversion."""
        todo = TodoProperties(
            task="Test Task",
            description="Basic description"
        )
        props = todo.to_notion_properties()
        assert props["Description"]["rich_text"][0]["text"]["content"] == "Basic description"

    def test_todo_description_max_length(self):
        """Test description length limits."""
        long_text = "x" * (MAX_TEXT_LENGTH + 100)  # Exceed limit
        with pytest.raises(ValidationError) as exc_info:
            TodoProperties(
                task="Test Task",
                description=long_text
            )
        assert "String should have at most 2000 characters" in str(exc_info.value)

    @pytest.mark.parametrize("name,content", MARKDOWN_SAMPLES)
    def test_todo_description_formatting(self, name, content):
        """Test various description formatting patterns."""
        todo = TodoProperties(
            task="Test Task",
            description=content
        )
        props = todo.to_notion_properties()
        assert props["Description"]["rich_text"][0]["text"]["content"] == content

@pytest.mark.asyncio
class TestRichTextIntegration:
    """Integration tests for rich text functionality."""

    async def test_create_todo_with_formatted_description(self, mock_notion_api):
        """Test creating a todo with formatted description."""
        formatted_text = (
            "# Important Task\n"
            "\n"
            "This task needs **immediate** attention:\n"
            "- First step\n"
            "- *Second* step\n"
            "- Final step\n"
            "\n"
            "[Reference link](https://example.com)"
        )
        todo = TodoProperties(
            task="Integration Test",
            description=formatted_text
        )
        props = todo.to_notion_properties()
        
        # Verify formatting structure
        rich_text = props["Description"]["rich_text"][0]
        assert rich_text["type"] == "text"
        assert rich_text["text"]["content"].strip() == formatted_text.strip()

    async def test_create_todo_with_special_characters(self, mock_notion_api):
        """Test creating a todo with special characters."""
        special_chars = "Special chars: &<>\"' and emojis: 🌟✨🚀"
        todo = TodoProperties(
            task="Special Chars Test",
            description=special_chars
        )
        props = todo.to_notion_properties()
        assert props["Description"]["rich_text"][0]["text"]["content"] == special_chars

    @pytest.mark.parametrize("name,content", MARKDOWN_SAMPLES)
    async def test_roundtrip_formatting(self, mock_notion_api, name, content):
        """Test roundtrip of formatted content through the API."""
        # Create todo with formatted content
        todo = TodoProperties(
            task=f"Format Test: {name}",
            description=content
        )
        props = todo.to_notion_properties()
        
        # Simulate API response
        api_response = {
            "properties": {
                "Task": {"title": [{"text": {"content": todo.task}}]},
                "Description": {"rich_text": props["Description"]["rich_text"]}
            }
        }
        
        # Convert back from API format
        roundtrip_todo = TodoProperties.from_notion_properties(api_response["properties"])
        assert roundtrip_todo.description == content

def test_rich_text_error_handling():
    """Test error handling for rich text operations."""
    # Test empty content
    with pytest.raises(ValidationError):
        RichTextContent(content="")
    
    # Test None content
    with pytest.raises(ValidationError):
        RichTextContent(content=None)
    
    # Test invalid annotations
    with pytest.raises(ValidationError):
        RichTextObject(
            text=RichTextContent(content="Test"),
            annotations={"invalid": True}
        )
    
    # Test exceeding max length
    with pytest.raises(ValidationError):
        RichTextContent(content="x" * (MAX_TEXT_LENGTH + 1))