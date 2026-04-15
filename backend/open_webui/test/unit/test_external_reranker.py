from open_webui.retrieval.models.external import (
    ExternalReranker,
    normalize_external_reranking_url,
)


def test_normalize_external_reranking_url_keeps_full_endpoint():
    assert (
        normalize_external_reranking_url("https://example.com/v1/rerank")
        == "https://example.com/v1/rerank"
    )


def test_normalize_external_reranking_url_appends_rerank_to_version_path():
    assert (
        normalize_external_reranking_url("https://example.com/api/v1")
        == "https://example.com/api/v1/rerank"
    )


def test_normalize_external_reranking_url_uses_default_v1_endpoint_for_root_url():
    assert (
        normalize_external_reranking_url("https://example.com")
        == "https://example.com/v1/rerank"
    )


def test_external_reranker_predict_maps_scores_by_index(monkeypatch):
    captured = {}

    class DummyResponse:
        ok = True
        reason = "OK"

        def json(self):
            return {
                "results": [
                    {"index": 1, "relevance_score": 0.25},
                    {"index": 0, "relevance_score": 0.75},
                ]
            }

    def fake_post(url, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return DummyResponse()

    monkeypatch.setattr("open_webui.retrieval.models.external.requests.post", fake_post)

    reranker = ExternalReranker(
        model="reranker",
        api_url="https://example.com/v1",
        api_key="secret",
        timeout=15,
    )

    scores = reranker.predict([("hello", "doc-a"), ("hello", "doc-b")])

    assert captured["url"] == "https://example.com/v1/rerank"
    assert captured["json"] == {
        "model": "reranker",
        "query": "hello",
        "documents": ["doc-a", "doc-b"],
        "top_n": 2,
    }
    assert captured["headers"]["Authorization"] == "Bearer secret"
    assert captured["timeout"] == 15
    assert scores == [0.75, 0.25]
