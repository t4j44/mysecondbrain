"""Bounded local MarkItDown conversion; no plugins, URLs, cloud OCR or LLM."""
import hashlib
import io
import json
import os
import subprocess  # nosec B404 - fixed local worker, allowlisted extension, stdin bytes, no shell
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path, PurePosixPath

from app.core.errors import AppError

EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".md", ".csv", ".json", ".html"}
CONVERSION_VERSION = 1
MAX_BYTES = 50 * 1024**2
MAX_TEXT = 2_000_000


class ConversionError(AppError):
    def __init__(self, code="CONVERSION_FAILED"):
        super().__init__("Needs OCR: upload a text-readable version or use Capture." if code == "OCR_REQUIRED"
                         else "Document conversion failed. Check the format and retry.", code=code, status_code=422)


def converter_identity():
    return f"markitdown:{version('markitdown')}:{CONVERSION_VERSION}"


def validate_document(content: bytes, filename: str):
    ext = Path(filename).suffix.lower()
    if ext not in EXTENSIONS or not content or len(content) > MAX_BYTES:
        raise ConversionError("UNSUPPORTED_OR_OVERSIZED_DOCUMENT")
    if ext in {".docx", ".pptx", ".xlsx"}:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                members = archive.infolist()
                if len(members) > 2000 or sum(m.file_size for m in members) > 100 * 1024**2:
                    raise ConversionError("ARCHIVE_LIMIT")
                for member in members:
                    path = PurePosixPath(member.filename)
                    if path.is_absolute() or ".." in path.parts or "\\" in member.filename or ":" in member.filename:
                        raise ConversionError("ARCHIVE_PATH")
                    if member.flag_bits & 1 or member.file_size > 30 * 1024**2 or member.file_size > max(1, member.compress_size) * 100:
                        raise ConversionError("ARCHIVE_LIMIT")
                    if member.filename.lower().endswith(("vbaproject.bin", ".exe", ".dll")):
                        raise ConversionError("ACTIVE_DOCUMENT")
                required = {".docx": "word/document.xml", ".pptx": "ppt/presentation.xml", ".xlsx": "xl/workbook.xml"}[ext]
                if required not in archive.namelist():
                    raise ConversionError("FORMAT_MISMATCH")
        except zipfile.BadZipFile as exc:
            raise ConversionError("FORMAT_MISMATCH") from exc
    if ext == ".pdf" and not content.startswith(b"%PDF-"):
        raise ConversionError("FORMAT_MISMATCH")
    return ext


def normalize(content: bytes, filename: str) -> tuple[str, dict]:
    ext = validate_document(content, filename)
    worker = Path(__file__).with_name("conversion_worker.py").resolve()
    # No account secrets reach the parser child. -I ignores PYTHONPATH/user-site.
    env = {k: os.environ[k] for k in ("SYSTEMROOT", "WINDIR", "PATH") if k in os.environ}
    try:
        with tempfile.TemporaryDirectory(prefix="brain-convert-") as folder:
            result = subprocess.run([sys.executable, "-I", str(worker), ext], input=content,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=40, check=False,
                cwd=folder, env={**env, "TMP": folder, "TEMP": folder, "TMPDIR": folder})  # nosec B603
        if result.returncode != 0 or len(result.stdout) > MAX_TEXT * 12:
            raise ConversionError()
        markdown = json.loads(result.stdout)["markdown"].strip()
    except subprocess.TimeoutExpired as exc:
        raise ConversionError("CONVERSION_TIMEOUT") from exc
    except (KeyError, ValueError) as exc:
        raise ConversionError() from exc
    if len(markdown) > MAX_TEXT:
        raise ConversionError("CONVERSION_LIMIT")
    if not markdown or (ext == ".pdf" and len(markdown.strip()) < 20):
        raise ConversionError("OCR_REQUIRED" if ext == ".pdf" else "NO_READABLE_TEXT")
    return markdown, {"source_checksum": hashlib.sha256(content).hexdigest(),
        "converter": "markitdown", "converter_version": version("markitdown"),
        "conversion_version": CONVERSION_VERSION, "converter_identity": converter_identity(),
        "normalized_at": datetime.now(timezone.utc).isoformat()}
