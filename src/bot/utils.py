"""Utility functions for Telegram bot"""
from typing import List
import re
from loguru import logger


# Telegram message length limit
TELEGRAM_MAX_MESSAGE_LENGTH = 4096


def fix_html(text: str) -> str:
    """
    Fix and sanitize HTML formatting for Telegram.

    Telegram HTML mode supports:
    - Bold: <b>text</b>
    - Italic: <i>text</i>
    - Code: <code>text</code>
    - Pre: <pre>text</pre>
    - Links: <a href="url">text</a>

    This function:
    1. Converts Markdown to HTML if any remains
    2. Escapes HTML special characters in content
    3. Ensures all tags are properly closed

    Args:
        text: Text with potentially mixed Markdown/HTML

    Returns:
        Text with proper HTML formatting for Telegram
    """
    if not text:
        return text

    result = text

    # Convert any remaining Markdown to HTML
    # Headers
    result = re.sub(r'^### (.+)$', r'<b>\1</b>', result, flags=re.MULTILINE)
    result = re.sub(r'^## (.+)$', r'<b>\1</b>', result, flags=re.MULTILINE)
    result = re.sub(r'^# (.+)$', r'<b>\1</b>', result, flags=re.MULTILINE)

    # Bold
    result = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', result)

    # Code blocks (remove language specifiers first)
    result = re.sub(r'```\w+\n', '```\n', result)
    result = re.sub(r'```(.+?)```', r'<pre>\1</pre>', result, flags=re.DOTALL)

    # Inline code
    result = re.sub(r'`(.+?)`', r'<code>\1</code>', result)

    # Convert Markdown links to HTML links
    # [text](url) -> <a href="url">text</a>
    result = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', result)

    # Escape HTML special characters < and > that are NOT part of HTML tags
    # Strategy: Use regex to protect complete HTML tags, then escape remaining < >

    import uuid
    placeholders = {}

    # Protect complete HTML tags with placeholders (including full <a href="..."> tags)
    html_tag_patterns = [
        (r'<b>', '<b>'),
        (r'</b>', '</b>'),
        (r'<i>', '<i>'),
        (r'</i>', '</i>'),
        (r'<code>', '<code>'),
        (r'</code>', '</code>'),
        (r'<pre>', '<pre>'),
        (r'</pre>', '</pre>'),
        (r'<a href="[^"]*">', None),  # <a href="url"> - full tag with any URL
        (r'</a>', '</a>'),
    ]

    for pattern, replacement in html_tag_patterns:
        if replacement:
            # Simple replacement
            while replacement in result:
                placeholder = f"___PH_{uuid.uuid4().hex[:8]}___"
                placeholders[placeholder] = replacement
                result = result.replace(replacement, placeholder, 1)
        else:
            # Regex pattern (for <a href="...">)
            matches = list(re.finditer(pattern, result))
            for match in reversed(matches):  # Process from end to avoid offset issues
                matched_text = match.group(0)
                placeholder = f"___PH_{uuid.uuid4().hex[:8]}___"
                placeholders[placeholder] = matched_text
                result = result[:match.start()] + placeholder + result[match.end():]

    # Now escape remaining < and >
    result = result.replace('<', '&lt;').replace('>', '&gt;')

    # Restore our valid tags
    for placeholder, tag in placeholders.items():
        result = result.replace(placeholder, tag)

    logger.debug("Converted Markdown to HTML and escaped special characters")

    return result


def split_message(text: str, max_length: int = TELEGRAM_MAX_MESSAGE_LENGTH) -> List[str]:
    """
    Split long message into chunks that fit Telegram's 4096 character limit.

    Tries to split on paragraphs (double newline) first, then on single newlines,
    then on sentences, to keep formatting intact.

    Args:
        text: Text to split
        max_length: Maximum length per chunk (default: 4096)

    Returns:
        List of message chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    # Split by paragraphs first (markdown preserving)
    paragraphs = text.split('\n\n')

    for paragraph in paragraphs:
        # If single paragraph is too long, split it further
        if len(paragraph) > max_length:
            # Split by newlines
            lines = paragraph.split('\n')
            for line in lines:
                # If single line is too long, split by sentences
                if len(line) > max_length:
                    sentences = line.split('. ')
                    for sentence in sentences:
                        # If single sentence is too long, split by words
                        if len(sentence) > max_length:
                            words = sentence.split(' ')
                            for word in words:
                                if len(current_chunk) + len(word) + 1 <= max_length:
                                    current_chunk += word + ' '
                                else:
                                    if current_chunk:
                                        chunks.append(current_chunk.strip())
                                    current_chunk = word + ' '
                        else:
                            if len(current_chunk) + len(sentence) + 2 <= max_length:
                                current_chunk += sentence + '. '
                            else:
                                if current_chunk:
                                    chunks.append(current_chunk.strip())
                                current_chunk = sentence + '. '
                else:
                    if len(current_chunk) + len(line) + 1 <= max_length:
                        current_chunk += line + '\n'
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = line + '\n'
        else:
            # Normal paragraph fits
            if len(current_chunk) + len(paragraph) + 2 <= max_length:
                current_chunk += paragraph + '\n\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + '\n\n'

    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    logger.debug(f"Split message into {len(chunks)} chunks (original length: {len(text)})")
    return chunks
