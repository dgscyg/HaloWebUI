import pathlib
import sys
from types import SimpleNamespace

from langchain_core.documents import Document

_BACKEND_DIR = pathlib.Path(__file__).resolve().parents[3]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from open_webui.retrieval import document_processing as document_processing_module  # noqa: E402
from open_webui.retrieval.document_processing import (  # noqa: E402
    DOCUMENT_PROVIDER_AZURE_DOCUMENT_INTELLIGENCE,
    DOCUMENT_PROVIDER_LOCAL_DEFAULT,
    DOCUMENT_PROVIDER_OPEN_MINERU,
    FILE_PROCESSING_MODE_FULL_CONTEXT,
    FILE_PROCESSING_MODE_NATIVE_FILE,
    FILE_PROCESSING_MODE_RETRIEVAL,
    _get_loader_for_provider,
    build_default_document_provider_configs,
    extract_documents_for_file,
    normalize_document_provider,
    normalize_file_processing_mode,
    provider_supports_file,
)


def test_normalize_file_processing_mode_recognizes_new_modes():
    assert normalize_file_processing_mode("retrieval") == FILE_PROCESSING_MODE_RETRIEVAL
    assert normalize_file_processing_mode("full_context") == FILE_PROCESSING_MODE_FULL_CONTEXT
    assert normalize_file_processing_mode("native_file") == FILE_PROCESSING_MODE_NATIVE_FILE
    assert normalize_file_processing_mode("full") == FILE_PROCESSING_MODE_FULL_CONTEXT
    assert normalize_file_processing_mode("native") == FILE_PROCESSING_MODE_NATIVE_FILE


def test_normalize_document_provider_maps_legacy_document_intelligence():
    assert normalize_document_provider("document_intelligence") == DOCUMENT_PROVIDER_AZURE_DOCUMENT_INTELLIGENCE
    assert normalize_document_provider("") == DOCUMENT_PROVIDER_LOCAL_DEFAULT


def test_provider_supports_expected_file_types():
    assert provider_supports_file("mineru", "slides.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation") is True
    assert provider_supports_file("doc2x", "slides.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation") is False
    assert provider_supports_file(
        DOCUMENT_PROVIDER_AZURE_DOCUMENT_INTELLIGENCE,
        "report.pdf",
        "application/pdf",
    ) is True


class _DummyFile:
    def __init__(self, filename: str, content_type: str):
        self.filename = filename
        self.meta = {"content_type": content_type}
        self.path = "/tmp/mock-file"
        self.id = "file-1"
        self.user_id = "user-1"


def _build_request(*, document_provider: str, content_extraction_engine: str):
    config = SimpleNamespace(
        DOCUMENT_PROVIDER=document_provider,
        DOCUMENT_PROVIDER_CONFIGS=build_default_document_provider_configs(),
        CONTENT_EXTRACTION_ENGINE=content_extraction_engine,
        TIKA_SERVER_URL="http://tika",
        DOCLING_SERVER_URL="http://docling",
        PDF_EXTRACT_IMAGES=False,
        DOCUMENT_INTELLIGENCE_ENDPOINT="",
        DOCUMENT_INTELLIGENCE_KEY="",
        MISTRAL_OCR_API_KEY="secret",
        PDF_LOADING_MODE="page",
    )
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(config=config)))


def test_open_mineru_unsupported_text_file_uses_strict_local_fallback(monkeypatch):
    request = _build_request(
        document_provider=DOCUMENT_PROVIDER_OPEN_MINERU,
        content_extraction_engine="mistral_ocr",
    )
    calls = []

    def fake_extract(request, file_obj, provider, provider_config, *, strict_local_only=False):
        calls.append((provider, strict_local_only))
        return [Document(page_content="local fallback text", metadata={})]

    monkeypatch.setattr(
        document_processing_module,
        "_extract_docs_with_provider",
        fake_extract,
    )

    result = extract_documents_for_file(
        request,
        _DummyFile("notes.md", "text/markdown"),
        provider=DOCUMENT_PROVIDER_OPEN_MINERU,
        allow_local_fallback=True,
    )

    assert calls == [(DOCUMENT_PROVIDER_LOCAL_DEFAULT, True)]
    assert result.provider == DOCUMENT_PROVIDER_LOCAL_DEFAULT
    assert result.requested_provider == DOCUMENT_PROVIDER_OPEN_MINERU
    assert result.fallback_provider == DOCUMENT_PROVIDER_LOCAL_DEFAULT
    assert "does not support" in result.primary_provider_error


def test_remote_provider_failure_preserves_primary_error_and_fallback(monkeypatch):
    request = _build_request(
        document_provider=DOCUMENT_PROVIDER_OPEN_MINERU,
        content_extraction_engine="mistral_ocr",
    )
    calls = []

    def fake_extract(request, file_obj, provider, provider_config, *, strict_local_only=False):
        calls.append((provider, strict_local_only))
        if provider == DOCUMENT_PROVIDER_OPEN_MINERU:
            raise RuntimeError("upstream timeout")
        return [Document(page_content="fallback text", metadata={})]

    monkeypatch.setattr(
        document_processing_module,
        "_extract_docs_with_provider",
        fake_extract,
    )

    result = extract_documents_for_file(
        request,
        _DummyFile("report.pdf", "application/pdf"),
        provider=DOCUMENT_PROVIDER_OPEN_MINERU,
        allow_local_fallback=True,
    )

    assert calls == [
        (DOCUMENT_PROVIDER_OPEN_MINERU, False),
        (DOCUMENT_PROVIDER_LOCAL_DEFAULT, True),
    ]
    assert result.provider == DOCUMENT_PROVIDER_LOCAL_DEFAULT
    assert result.requested_provider == DOCUMENT_PROVIDER_OPEN_MINERU
    assert result.primary_provider_error == "upstream timeout"
    assert result.fallback_provider == DOCUMENT_PROVIDER_LOCAL_DEFAULT
    assert result.fallback_reason == "upstream timeout"


def test_force_local_engine_bypasses_advanced_parser():
    request = _build_request(
        document_provider=DOCUMENT_PROVIDER_OPEN_MINERU,
        content_extraction_engine="mistral_ocr",
    )

    loader = _get_loader_for_provider(
        request,
        DOCUMENT_PROVIDER_LOCAL_DEFAULT,
        {},
        force_local_engine=True,
    )

    assert loader.engine == ""
