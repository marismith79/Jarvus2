import re

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text


class TextFormatter:
    def __init__(self):
        self.buffer = ""
        self.console = Console()

    def format_chunk(self, chunk: str) -> str:
        """
        Format a chunk of text, maintaining state between chunks.
        """
        # Add the new chunk to the buffer
        self.buffer += chunk

        # Try to find complete sentences or list items
        formatted_text = self._format_buffer()

        return formatted_text

    def _format_buffer(self) -> str:
        """
        Format the current buffer content.
        """
        # Split into lines for processing
        lines = self.buffer.split("\n")
        processed_lines = []
        in_list = False
        list_indent = 0

        for line in lines:
            # Check for numbered list items
            list_match = re.match(r"^\s*(\d+)[\.\)]\s+(.+)$", line)
            if list_match:
                if not in_list:
                    in_list = True
                    list_indent = len(line) - len(line.lstrip())
                # Format as markdown list item
                processed_lines.append(
                    " " * list_indent
                    + f"{list_match.group(1)}. {list_match.group(2)}"
                )
            else:
                # Handle regular text
                if in_list and not line.strip():
                    processed_lines.append("")
                    in_list = False
                elif in_list and line.strip():
                    processed_lines.append(
                        " " * (list_indent + 4) + line.lstrip()
                    )
                else:
                    processed_lines.append(line)

        # Join the processed lines
        processed_text = "\n".join(processed_lines)

        # Convert to markdown and render
        markdown = Markdown(processed_text)
        with self.console.capture() as capture:
            self.console.print(markdown)

        return capture.get()

    def reset(self):
        """Reset the buffer."""
        self.buffer = ""


def format_chat_message(message: str) -> str:
    """
    Format a chat message with rich text formatting.
    """
    formatter = TextFormatter()
    return formatter.format_chunk(message)


def format_number(number: int) -> str:
    """
    Format a number with commas for thousands.
    """
    return f"{number:,}"


def format_list(items: list) -> str:
    """
    Format a list of items with bullet points.
    """
    return "\n".join(f"• {item}" for item in items)


def format_code_block(code: str, language: str = "python") -> str:
    """
    Format a code block with syntax highlighting.
    """
    console = Console()
    with console.capture() as capture:
        console.print(Panel(code, title=language, border_style="blue"))
    return capture.get()


def format_recipe(ingredients: list, instructions: list) -> str:
    """
    Format a recipe with ingredients and instructions.
    """
    console = Console()

    # Format ingredients
    ingredients_text = "**Ingredients:**\n" + "\n".join(
        f"• {ingredient}" for ingredient in ingredients
    )

    # Format instructions
    instructions_text = "**Instructions:**\n" + "\n".join(
        f"{i+1}. {instruction}" for i, instruction in enumerate(instructions)
    )

    # Combine and format
    recipe_text = f"{ingredients_text}\n\n{instructions_text}"

    with console.capture() as capture:
        console.print(Markdown(recipe_text))

    return capture.get()
