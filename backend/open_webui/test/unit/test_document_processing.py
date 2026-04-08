import pathlib
import sys


_BACKEND_DIR = pathlib.Path(__file__).resolve().parents[3]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from open_webui.retrieval.document_processing import (  # noqa: E402
    DOCUMENT_PROVIDER_AZURE_DOCUMENT_INTELLIGENCE,
    DOCUMENT_PROVIDER_LOCAL_DEFAULT,
    FILE_PROCESSING_MODE_FULL_CONTEXT,
    FILE_PROCESSING_MODE_NATIVE_FILE,
    FILE_PROCESSING_MODE_RETRIEVAL,
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
