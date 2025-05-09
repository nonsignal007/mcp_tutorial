"""Test text and content formatting utilities."""
import pytest
from datetime import datetime
from notion_api_mcp.models import BlockType, RichTextObject, RichTextContent
from notion_api_mcp.utils.formatting import (
    create_rich_text,
    create_block,
    format_date,
    parse_markdown_to_blocks,
    blocks_to_markdown,
    format_rich_text_content
)

# Test data constants
TEXT_ANNOTATIONS = {
    "bold": True,
    "italic": True,
    "strikethrough": False,
    "underline": False,
    "code": False,
    "color": "blue"
}

class TestRichText:
    """Test rich text creation and validation."""
    
    def test_create_basic_rich_text(self):
        """Test basic rich text creation."""
        result = create_rich_text("Test content")
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert result[0]["text"]["content"] == "Test content"

    def test_rich_text_with_link(self):
        """Test rich text with link."""
        result = create_rich_text("Test content", link="https://example.com")
        assert result[0]["text"]["link"] == {"url": "https://example.com"}

    def test_rich_text_with_annotations(self):
        """Test rich text with annotations."""
        result = create_rich_text("Test content", annotations=TEXT_ANNOTATIONS)
        assert result[0]["annotations"] == TEXT_ANNOTATIONS

    def test_rich_text_validation_errors(self):
        """Test rich text validation error cases."""
        # Empty content
        with pytest.raises(ValueError, match="Content cannot be empty"):
            create_rich_text("")
            
        with pytest.raises(ValueError, match="Content cannot be empty"):
            create_rich_text(None)

        # Invalid annotations
        with pytest.raises(ValueError, match="Invalid annotations"):
            create_rich_text("Test", annotations={"invalid": True})

        # Invalid color type
        with pytest.raises(ValueError, match="Color annotation must be a string"):
            create_rich_text("Test", annotations={"color": True})

class TestBlocks:
    """Test block creation and validation."""
    
    def test_create_basic_blocks(self):
        """Test creating different types of blocks."""
        # Paragraph block
        result = create_block("Test content", BlockType.PARAGRAPH)
        assert result["type"] == "paragraph"
        assert result["paragraph"]["rich_text"][0]["text"]["content"] == "Test content"

        # Heading block
        result = create_block("Test heading", BlockType.HEADING_1)
        assert result["type"] == "heading_1"
        assert result["heading_1"]["rich_text"][0]["text"]["content"] == "Test heading"

    def test_block_with_annotations(self):
        """Test block with text annotations."""
        result = create_block(
            "Test content",
            BlockType.PARAGRAPH,
            annotations=TEXT_ANNOTATIONS
        )
        assert result["paragraph"]["rich_text"][0]["annotations"] == TEXT_ANNOTATIONS

    def test_todo_block(self):
        """Test todo block with checked state."""
        result = create_block(
            "Todo item",
            BlockType.TO_DO,
            extra_props={"checked": True}
        )
        assert result["to_do"]["checked"] is True

    def test_code_block(self):
        """Test code block with language."""
        # Code block with language
        result = create_block(
            "print('hello')",
            BlockType.CODE,
            extra_props={"language": "python"}
        )
        assert result["code"]["language"] == "python"
        assert result["code"]["content"] == "print('hello')"

        # Code block without content (valid for CODE type)
        result = create_block("", BlockType.CODE)
        assert result["type"] == "code"

    def test_block_validation_errors(self):
        """Test block validation error cases."""
        # Empty content for non-code block
        with pytest.raises(ValueError, match="Content cannot be empty"):
            create_block("", BlockType.PARAGRAPH)

        # Invalid block type string
        with pytest.raises(ValueError, match="Invalid block type"):
            create_block("Test", "invalid_type")

        # Invalid annotations
        with pytest.raises(ValueError, match="Invalid annotations"):
            create_block("Test", BlockType.PARAGRAPH, annotations={"invalid": True})

class TestMarkdownConversion:
    """Test markdown to blocks conversion and back."""

    def test_parse_basic_markdown(self):
        """Test parsing basic markdown elements."""
        markdown = """# Heading 1
## Heading 2
### Heading 3

Regular paragraph

- Bullet point
1. Numbered item

[ ] Todo item
[x] Completed todo

```python
def hello():
    print('hello')
```

> Quote block"""

        blocks = parse_markdown_to_blocks(markdown)

        # Verify each block type
        assert blocks[0]["type"] == "heading_1"
        assert blocks[0]["heading_1"]["rich_text"][0]["text"]["content"] == "Heading 1"

        assert blocks[1]["type"] == "heading_2"
        assert blocks[2]["type"] == "heading_3"

        assert blocks[3]["type"] == "paragraph"
        assert blocks[3]["paragraph"]["rich_text"][0]["text"]["content"] == "Regular paragraph"

        assert blocks[4]["type"] == "bulleted_list_item"
        assert blocks[5]["type"] == "numbered_list_item"

        assert blocks[6]["type"] == "to_do"
        assert blocks[6]["to_do"]["checked"] is False
        assert blocks[7]["type"] == "to_do"
        assert blocks[7]["to_do"]["checked"] is True

        # Verify code block with language
        assert blocks[8]["type"] == "code"
        assert blocks[8]["code"]["language"] == "python"
        assert "def hello():" in blocks[8]["code"]["content"]

        assert blocks[9]["type"] == "quote"

    def test_consecutive_lists(self):
        """Test handling of consecutive list items."""
        markdown = """- Item 1
- Item 2
- Item 3

1. First
2. Second
3. Third"""
        
        blocks = parse_markdown_to_blocks(markdown)
        assert len(blocks) == 6
        assert all(b["type"] == "bulleted_list_item" for b in blocks[:3])
        assert all(b["type"] == "numbered_list_item" for b in blocks[3:])

        # Convert back to markdown
        result = blocks_to_markdown(blocks)
        assert "- Item 1" in result
        assert "- Item 2" in result
        assert "1. First" in result
        assert "2. Second" in result

    def test_code_blocks(self):
        """Test code block parsing with and without language."""
        # Code block with language
        markdown = "```python\ndef test():\n    pass\n```"
        blocks = parse_markdown_to_blocks(markdown)
        assert blocks[0]["type"] == "code"
        assert blocks[0]["code"]["language"] == "python"
        assert "def test():" in blocks[0]["code"]["content"]

        # Code block without language
        markdown = "```\nplain text\n```"
        blocks = parse_markdown_to_blocks(markdown)
        assert blocks[0]["type"] == "code"
        # Code blocks without language should have empty string language
        assert blocks[0]["code"].get("language", "") == ""
        assert "plain text" in blocks[0]["code"]["content"]

    def test_markdown_error_cases(self):
        """Test markdown parsing error cases."""
        # Unclosed code block
        with pytest.raises(ValueError, match="Unclosed code block"):
            parse_markdown_to_blocks("```python\ndef test():")

        # Empty input
        assert parse_markdown_to_blocks("") == []
        assert blocks_to_markdown([]) == ""

        # Only whitespace
        assert parse_markdown_to_blocks("   \n   \n") == []

class TestDateFormatting:
    """Test date formatting utilities."""

    def test_format_date(self):
        """Test date formatting."""
        date = datetime(2025, 1, 1, 12, 0, 0)
        result = format_date(date)
        assert result == "2025-01-01T12:00:00"

class TestRichTextContent:
    """Test rich text content formatting."""

    def test_format_rich_text_content(self):
        """Test formatting rich text content."""
        rich_text = [
            RichTextObject(
                type="text",
                text=RichTextContent(content="First part")
            ),
            RichTextObject(
                type="text",
                text=RichTextContent(content="Second part")
            )
        ]

        result = format_rich_text_content(rich_text)
        assert result == "First part Second part"

    def test_empty_rich_text(self):
        """Test formatting empty rich text."""
        assert format_rich_text_content([]) == ""

    def test_rich_text_with_minimal_content(self):
        """Test formatting rich text with minimal content."""
        rich_text = [
            RichTextObject(
                type="text",
                text=RichTextContent(content="Valid content")
            ),
            RichTextObject(
                type="text",
                text=RichTextContent(content="x")  # Minimal valid content
            )
        ]
        result = format_rich_text_content(rich_text)
        assert result == "Valid content x"