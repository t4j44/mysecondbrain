import hashlib
import io
import re
from typing import Any, Dict, List, Optional


class ExtractionResult:
    def __init__(
        self,
        extracted_text: str,
        metadata: Dict[str, Any],
        chunks: List[Dict[str, Any]],
        error: Optional[str] = None,
    ):
        self.extracted_text = extracted_text
        self.metadata = metadata
        self.chunks = chunks
        self.error = error
        self.success = error is None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "extracted_text": self.extracted_text,
            "metadata": self.metadata,
            "chunks_count": len(self.chunks),
            "error": self.error,
        }


class DocumentExtractor:
    """
    Production document text extraction and semantic chunking service.
    Supports txt, md, and PDF files without external binary dependencies.
    """

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}
    SUPPORTED_MIME_TYPES = {
        "text/plain",
        "text/markdown",
        "application/pdf",
        "application/octet-stream",
    }

    @staticmethod
    def calculate_checksum(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @classmethod
    def extract_text(
        cls,
        content: bytes,
        filename: str,
        mime_type: Optional[str] = None,
        chunk_size: int = 600,
        chunk_overlap: int = 100,
    ) -> ExtractionResult:
        """
        Extract text from raw file bytes, compute metadata, and chunk text.
        """
        if not content:
            return ExtractionResult(
                extracted_text="",
                metadata={"filename": filename, "size_bytes": 0},
                chunks=[],
                error="Document content is empty.",
            )

        checksum = cls.calculate_checksum(content)
        ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""

        extracted_text = ""
        page_count = 1
        extra_meta: Dict[str, Any] = {}

        try:
            if ext == ".txt" or mime_type == "text/plain":
                extracted_text = cls._extract_txt(content)
            elif ext == ".md" or mime_type == "text/markdown":
                extracted_text = cls._extract_md(content)
            elif ext == ".pdf" or mime_type == "application/pdf":
                extracted_text, page_count, extra_meta = cls._extract_pdf(content)
            else:
                # Attempt text decoding as fallback if content seems textual
                try:
                    extracted_text = content.decode("utf-8")
                except UnicodeDecodeError:
                    return ExtractionResult(
                        extracted_text="",
                        metadata={"filename": filename, "checksum": checksum, "extension": ext},
                        chunks=[],
                        error=f"Unsupported file format: extension '{ext}', mime '{mime_type}'",
                    )

            cleaned_text = cls._clean_text(extracted_text)

            if not cleaned_text.strip():
                return ExtractionResult(
                    extracted_text="",
                    metadata={
                        "filename": filename,
                        "checksum": checksum,
                        "extension": ext,
                        "size_bytes": len(content),
                        "page_count": page_count,
                        **extra_meta,
                    },
                    chunks=[],
                    error="No readable text could be extracted from the document.",
                )

            chunks = cls.split_text_into_chunks(
                cleaned_text,
                chunk_size=chunk_size,
                overlap=chunk_overlap,
                source_metadata={"filename": filename, "checksum": checksum},
            )

            metadata = {
                "filename": filename,
                "checksum": checksum,
                "extension": ext,
                "size_bytes": len(content),
                "character_count": len(cleaned_text),
                "word_count": len(cleaned_text.split()),
                "page_count": page_count,
                **extra_meta,
            }

            return ExtractionResult(
                extracted_text=cleaned_text, metadata=metadata, chunks=chunks
            )

        except Exception as exc:
            return ExtractionResult(
                extracted_text="",
                metadata={"filename": filename, "checksum": checksum, "extension": ext},
                chunks=[],
                error=f"Document parsing error: {str(exc)}",
            )

    @staticmethod
    def _extract_txt(content: bytes) -> str:
        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                return content.decode(enc)
            except UnicodeDecodeError:
                continue
        return content.decode("utf-8", errors="replace")

    @staticmethod
    def _extract_md(content: bytes) -> str:
        raw_text = DocumentExtractor._extract_txt(content)
        clean = re.sub(r"^---\s*\n.*?\n---\s*\n", "", raw_text, flags=re.DOTALL)
        return clean

    @staticmethod
    def _extract_pdf(content: bytes) -> tuple[str, int, Dict[str, Any]]:
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError

        try:
            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    raise PdfReadError("PDF is password-encrypted and cannot be processed.") from None

            pages_text = []
            page_count = len(reader.pages)

            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(f"--- Page {idx + 1} ---\n{page_text}")

            pdf_meta = {}
            if reader.metadata:
                for k, v in reader.metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        pdf_meta[str(k).lstrip("/")] = v

            return "\n\n".join(pages_text), page_count, {"pdf_metadata": pdf_meta}
        except Exception as exc:
            raise ValueError(f"Failed to parse PDF document: {str(exc)}") from exc

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text.strip()

    @classmethod
    def split_text_into_chunks(
        cls,
        text: str,
        chunk_size: int = 600,
        overlap: int = 100,
        source_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Recursive character splitting with sentence and paragraph awareness.
        """
        if not text:
            return []

        if len(text) <= chunk_size:
            chunk_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            return [
                {
                    "chunk_index": 0,
                    "chunk_text": text,
                    "character_count": len(text),
                    "token_count": len(text.split()),
                    "checksum": chunk_hash,
                    "metadata": source_metadata or {},
                }
            ]

        paragraphs = text.split("\n\n")
        raw_chunks: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= chunk_size:
                current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para
            else:
                if current_chunk:
                    raw_chunks.append(current_chunk)

                if len(para) > chunk_size:
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    current_sub = ""
                    for sent in sentences:
                        if len(current_sub) + len(sent) + 1 <= chunk_size:
                            current_sub = f"{current_sub} {sent}" if current_sub else sent
                        else:
                            if current_sub:
                                raw_chunks.append(current_sub)

                            if len(sent) > chunk_size:
                                for i in range(0, len(sent), max(1, chunk_size - overlap)):
                                    raw_chunks.append(sent[i : i + chunk_size])
                                current_sub = ""
                            else:
                                current_sub = sent
                    if current_sub:
                        current_chunk = current_sub
                    else:
                        current_chunk = ""
                else:
                    current_chunk = para

        if current_chunk:
            raw_chunks.append(current_chunk)

        final_chunks: List[Dict[str, Any]] = []
        for idx, chunk_str in enumerate(raw_chunks):
            chunk_clean = chunk_str.strip()
            if not chunk_clean:
                continue
            chunk_hash = hashlib.sha256(chunk_clean.encode("utf-8")).hexdigest()
            final_chunks.append(
                {
                    "chunk_index": idx,
                    "chunk_text": chunk_clean,
                    "character_count": len(chunk_clean),
                    "token_count": len(chunk_clean.split()),
                    "checksum": chunk_hash,
                    "metadata": {
                        **(source_metadata or {}),
                        "chunk_index": idx,
                    },
                }
            )

        return final_chunks
