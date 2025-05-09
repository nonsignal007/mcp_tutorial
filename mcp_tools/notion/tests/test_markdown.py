"""
Validation tests for markdown conversion and block formatting.
"""
import pytest
from notion_api_mcp.utils.formatting import (
    parse_markdown_to_blocks,
    blocks_to_markdown,
    create_rich_text,
    create_block,
    BlockType
)

# Test Data: (markdown, expected_blocks, description)
MARKDOWN_TEST_CASES = [
    (
        "# Heading 1\n## Heading 2\n### Heading 3",
        [
            {"type": "heading_1", "heading_1": {"rich_text": [{"type": "text", "text": {"content": "Heading 1"}}]}},
            {"type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Heading 2"}}]}},
            {"type": "heading_3", "heading_3": {"rich_text": [{"type": "text", "text": {"content": "Heading 3"}}]}}
        ],
        "Headers of different levels"
    ),
    (
        "- Item 1\n- Item 2\n1. First\n2. Second",
        [
            {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": "Item 1"}}]}},
            {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": "Item 2"}}]}},
            {"type": "numbered_list_item", "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": "First"}}]}},
            {"type": "numbered_list_item", "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": "Second"}}]}}
        ],
        "Mixed list types"
    ),
    (
        "[ ] Todo item\n[x] Completed item",
        [
            {"type": "to_do", "to_do": {"rich_text": [{"type": "text", "text": {"content": "Todo item"}}], "checked": False}},
            {"type": "to_do", "to_do": {"rich_text": [{"type": "text", "text": {"content": "Completed item"}}], "checked": True}}
        ],
        "Todo items with different states"
    ),
    (
        "```python\nprint('hello')\n```\n> Quote block",
        [
            {"type": "code", "code": {"rich_text": [{"type": "text", "text": {"content": "python"}}]}},
            {"type": "quote", "quote": {"rich_text": [{"type": "text", "text": {"content": "Quote block"}}]}}
        ],
        "Code and quote blocks"
    ),
    (
        "Normal paragraph\nwith multiple\nlines",
        [
            {"type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Normal paragraph"}}]}},
            {"type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "with multiple"}}]}},
            {"type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "lines"}}]}}
        ],
        "Multi-line paragraphs"
    )
]

# Complex formatting cases
COMPLEX_MARKDOWN = """
# Project Overview

## Features
- Basic functionality
- **Advanced** features
- *Optional* components

### Implementation Details
1. First step
2. Second step
   - Sub-item 1
   - Sub-item 2

```python
def example():
    return "Hello World"
```

> Important note
> Continued quote

[ ] Task pending
[x] Task completed

Regular paragraph with **bold** and *italic* text.
"""

class TestMarkdownParsing:
    """Test markdown parsing functionality."""

    @pytest.mark.parametrize("markdown,expected_blocks,description", MARKDOWN_TEST_CASES)
    def test_markdown_to_blocks(self, markdown, expected_blocks, description):
        """Test conversion of markdown to blocks."""
        blocks = parse_markdown_to_blocks(markdown)
        assert len(blocks) == len(expected_blocks), f"Failed for: {description}"
        for actual, expected in zip(blocks, expected_blocks):
            assert actual["type"] == expected["type"]
            actual_content = actual[actual["type"]]["rich_text"][0]["text"]["content"]
            expected_content = expected[expected["type"]]["rich_text"][0]["text"]["content"]
            assert actual_content == expected_content

    def test_complex_markdown(self):
        """Test parsing of complex markdown with mixed elements."""
        blocks = parse_markdown_to_blocks(COMPLEX_MARKDOWN)
        
        # Verify structure
        block_types = [block["type"] for block in blocks]
        assert "heading_1" in block_types
        assert "heading_2" in block_types
        assert "bulleted_list_item" in block_types
        assert "numbered_list_item" in block_types
        assert "code" in block_types
        assert "quote" in block_types
        assert "to_do" in block_types
        assert "paragraph" in block_types

        # Verify content preservation
        markdown_result = blocks_to_markdown(blocks)
        assert "Project Overview" in markdown_result
        assert "**Advanced**" in markdown_result
        assert "*Optional*" in markdown_result
        assert "```python" in markdown_result
        assert "Important note" in markdown_result

    def test_empty_lines(self):
        """Test handling of empty lines."""
        markdown = "Line 1\n\nLine 2\n\n\nLine 3"
        blocks = parse_markdown_to_blocks(markdown)
        assert len(blocks) == 3
        assert all(block["type"] == "paragraph" for block in blocks)

    def test_special_characters(self):
        """Test handling of special characters."""
        markdown = "Special chars: & < > \" '\nEmojis: 🌟 ✨ 🚀"
        blocks = parse_markdown_to_blocks(markdown)
        assert len(blocks) == 2
        assert "&" in blocks[0]["paragraph"]["rich_text"][0]["text"]["content"]
        assert "🌟" in blocks[1]["paragraph"]["rich_text"][0]["text"]["content"]

class TestMarkdownRoundtrip:
    """Test markdown roundtrip conversion."""

    @pytest.mark.parametrize("markdown,_,description", MARKDOWN_TEST_CASES)
    def test_markdown_roundtrip(self, markdown, _, description):
        """Test markdown -> blocks -> markdown conversion."""
        blocks = parse_markdown_to_blocks(markdown)
        result = blocks_to_markdown(blocks)
        
        # Normalize whitespace for comparison
        normalized_original = "\n".join(line.strip() for line in markdown.split("\n") if line.strip())
        normalized_result = "\n".join(line.strip() for line in result.split("\n") if line.strip())
        
        assert normalized_original == normalized_result, f"Failed roundtrip for: {description}"

    def test_complex_markdown_roundtrip(self):
        """Test roundtrip of complex markdown."""
        blocks = parse_markdown_to_blocks(COMPLEX_MARKDOWN)
        result = blocks_to_markdown(blocks)
        
        # Verify key elements preserved
        assert "# Project Overview" in result
        assert "## Features" in result
        assert "**Advanced**" in result
        assert "*Optional*" in result
        assert "```python" in result
        assert "def example():" in result
        assert "> Important note" in result
        assert "[ ]" in result
        assert "[x]" in result

class TestBlockCreation:
    """Test block creation utilities."""

    def test_create_rich_text_basic(self):
        """Test basic rich text creation."""
        rich_text = create_rich_text("Test content")
        assert rich_text[0]["type"] == "text"
        assert rich_text[0]["text"]["content"] == "Test content"

    def test_create_rich_text_with_link(self):
        """Test rich text with link."""
        rich_text = create_rich_text("Test link", link="https://example.com")
        assert rich_text[0]["text"]["link"]["url"] == "https://example.com"

    def test_create_rich_text_with_annotations(self):
        """Test rich text with annotations."""
        annotations = {"bold": True, "italic": True}
        rich_text = create_rich_text("Test format", annotations=annotations)
        assert rich_text[0]["annotations"] == annotations

    def test_create_block_basic(self):
        """Test basic block creation."""
        block = create_block("Test content", BlockType.PARAGRAPH)
        assert block["type"] == "paragraph"
        assert block["paragraph"]["rich_text"][0]["text"]["content"] == "Test content"

    def test_create_block_with_extra_props(self):
        """Test block creation with extra properties."""
        block = create_block(
            "Test todo",
            BlockType.TO_DO,
            extra_props={"checked": True}
        )
        assert block["to_do"]["checked"] is True

def test_error_handling():
    """Test error handling in markdown processing."""
    # Test invalid block type
    with pytest.raises(ValueError):
        create_block("Test", "invalid_type")
    
    # Test empty content
    with pytest.raises(ValueError):
        create_rich_text("")
    
    # Test None content
    with pytest.raises(ValueError):
        create_rich_text(None)
    
    # Test invalid annotations
    with pytest.raises(ValueError):
        create_rich_text("Test", annotations={"invalid": True})