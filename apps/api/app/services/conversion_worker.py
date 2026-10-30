"""Isolated byte-only converter. Never accepts paths or URLs from a document."""
import io
import json
import sys


def deny_network(event, args):
    if event in {"socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system"}:
        raise PermissionError("Conversion cannot access the network or launch programs")


def main():
    # Unix resource ceilings complement the parent's wall-clock timeout. Windows
    # has the same input/output/ZIP limits and process timeout, but no RLIMIT_AS.
    if sys.platform != "win32":
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (1536 * 1024**2, 1536 * 1024**2))
        resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    sys.addaudithook(deny_network)
    from markitdown import StreamInfo
    from markitdown.converters import (
        DocxConverter,
        HtmlConverter,
        PdfConverter,
        PlainTextConverter,
        PptxConverter,
        XlsxConverter,
    )
    ext = sys.argv[1]
    converters = {".pdf": PdfConverter, ".docx": DocxConverter, ".pptx": PptxConverter,
                  ".xlsx": XlsxConverter, ".html": HtmlConverter}
    content = sys.stdin.buffer.read(50 * 1024**2 + 1)
    if len(content) > 50 * 1024**2:
        raise ValueError("Input limit exceeded")
    converter = converters.get(ext, PlainTextConverter)()
    result = converter.convert(io.BytesIO(content), StreamInfo(extension=ext))
    value = result.markdown
    if len(value) > 2_000_000:
        raise ValueError("Output limit exceeded")
    print(json.dumps({"markdown": value}, ensure_ascii=True))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Parser errors can embed private content. Return only a fixed code.
        print('{"error":"CONVERSION_FAILED"}')
        sys.exit(1)
