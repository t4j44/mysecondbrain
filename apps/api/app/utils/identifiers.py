import re
import uuid


def generate_uuid() -> str:
    """Generate a standard UUID version 4 string."""
    return str(uuid.uuid4())


def slugify(text: str) -> str:
    """Convert an entity title or name into a clean URL and filesystem safe slug."""
    if not text:
        return "unnamed-item"
    text = text.lower().strip()
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r"[^a-z0-9\-_]+", "-", text)
    # Remove duplicate hyphens
    text = re.sub(r"-+", "-", text)
    return text.strip("-") or "unnamed-item"
