"""Tests for HTTP retries and raw-response caching."""

import httpx

from last_asylum_doctor.scraping.client import CachedHttpClient


def test_reuses_a_fresh_content_addressed_cache(tmp_path) -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(
            200,
            content=b"source evidence",
            headers={"ETag": '"abc"', "Content-Type": "text/plain"},
            request=request,
        )

    with CachedHttpClient(
        tmp_path,
        minimum_interval_seconds=0,
        transport=httpx.MockTransport(handler),
    ) as client:
        first = client.fetch("https://example.test/source")
        second = client.fetch("https://example.test/source")

    assert request_count == 1
    assert not first.from_cache
    assert second.from_cache
    assert second.content == b"source evidence"
    assert second.metadata.sha256 == first.metadata.sha256
    assert second.metadata.etag == '"abc"'


def test_retries_transient_statuses(tmp_path) -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        status = 503 if request_count == 1 else 200
        return httpx.Response(status, content=b"ok", request=request)

    with CachedHttpClient(
        tmp_path,
        minimum_interval_seconds=0,
        transport=httpx.MockTransport(handler),
        sleep=lambda _seconds: None,
    ) as client:
        response = client.fetch("https://example.test/retry")

    assert request_count == 2
    assert response.content == b"ok"
