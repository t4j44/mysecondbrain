"""Markdown sections first; bounded paragraphs/tables with explicit versioning."""
import hashlib
import re

CHUNKING_VERSION = 2


def chunk_markdown(markdown: str, size: int = 1800) -> list[dict]:
    chunks: list[dict] = []
    heading = ""
    current = ""

    def emit():
        nonlocal current
        value = current.strip()
        if value:
            chunks.append({"chunk_index": len(chunks), "chunk_text": value,
                "section_title": heading or None, "page_number": None,
                "character_count": len(value), "token_count": (len(value) + 3) // 4,
                "checksum": hashlib.sha256(value.encode()).hexdigest(),
                "metadata": {"chunking_version": CHUNKING_VERSION, "heading": heading}})
        current = ""

    for block in re.split(r"\n\s*\n", markdown):
        # Split at headings even where the source omitted blank lines.
        for part in re.split(r"(?m)(?=^#{1,6} )", block):
            if not part.strip():
                continue
            if re.match(r"^#{1,6} ", part):
                emit()
                heading = part.splitlines()[0].lstrip("# ")[:300]
            if len(current) + len(part) + 2 <= size:
                current += ("\n\n" if current else "") + part
                continue
            emit()
            if len(part) <= size:
                current = part
                continue
            # Large tables/lists split at rows. Only an oversized single row is cut.
            for line in part.splitlines():
                while len(line) > size:
                    emit()
                    current, line = line[:size], line[size:]
                    emit()
                if len(current) + len(line) + 1 > size:
                    emit()
                current += ("\n" if current else "") + line
    emit()
    return chunks
