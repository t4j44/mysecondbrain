import re
from typing import Optional


def sanitize_filename(filename: str) -> str:
    """Strip illegal filesystem characters and prevent path traversal."""
    if not filename:
        return "unnamed_file.txt"

    # Strip directory path traversal attempts like ../ or ..\ or absolute paths
    filename = filename.replace("\\", "/").split("/")[-1]
    if filename in {".", ".."}:
        filename = "unnamed_file.txt"

    # Remove unsupported characters across Linux, macOS, Windows
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", filename).strip()

    # Avoid reserved Windows device names (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
    base = cleaned.split(".")[0].upper()
    reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
    if base in reserved:
        cleaned = f"safe_{cleaned}"

    return cleaned or "unnamed_file.txt"


def normalize_empty_string(value: Optional[str]) -> Optional[str]:
    """Normalize whitespace-only strings to None."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None
