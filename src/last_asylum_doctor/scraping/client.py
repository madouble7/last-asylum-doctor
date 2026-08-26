"""Respectful HTTP retrieval with retries and auditable raw caching."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import httpx

from last_asylum_doctor.models import RetrievalMetadata

DEFAULT_USER_AGENT = (
    "LastAsylumDoctor/0.1 "
    "(+local factual game-data ingestion; cached and low-frequency requests)"
)
TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}


class SourceFetchError(RuntimeError):
    """Raised when a source response cannot be retrieved safely."""


@dataclass(frozen=True, slots=True)
class FetchedResource:
    """One retrieved or cache-loaded response."""

    content: bytes
    metadata: RetrievalMetadata
    from_cache: bool

    @property
    def text(self) -> str:
        """Decode the site's UTF-8 text assets."""
        try:
            return self.content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise SourceFetchError(
                f"Source was not valid UTF-8: {self.metadata.source_url}"
            ) from error


class CachedHttpClient:
    """Sequential HTTP client with pacing, retries, and content-addressed cache."""

    def __init__(
        self,
        cache_dir: Path,
        *,
        timeout_seconds: float = 20.0,
        minimum_interval_seconds: float = 0.75,
        cache_max_age: timedelta = timedelta(hours=1),
        max_attempts: int = 3,
        user_agent: str = DEFAULT_USER_AGENT,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if minimum_interval_seconds < 0:
            raise ValueError("minimum_interval_seconds cannot be negative")
        if max_attempts <= 0:
            raise ValueError("max_attempts must be positive")

        self.cache_dir = cache_dir
        self.minimum_interval_seconds = minimum_interval_seconds
        self.cache_max_age = cache_max_age
        self.max_attempts = max_attempts
        self._sleep = sleep
        self._last_request_at: float | None = None
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=True,
            headers={"User-Agent": user_agent, "Accept": "*/*"},
            transport=transport,
        )

    def __enter__(self) -> CachedHttpClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying connection pool."""
        self._client.close()

    def fetch(self, url: str, *, refresh: bool = False) -> FetchedResource:
        """Fetch a URL or return its recently cached exact response bytes."""
        requested_url = url
        if not refresh:
            cached = self._load_fresh_cache(requested_url)
            if cached is not None:
                return cached

        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            self._pace_request()
            try:
                response = self._client.get(url)
            except httpx.TransportError as error:
                last_error = error
                if attempt == self.max_attempts:
                    break
                self._sleep(0.5 * 2 ** (attempt - 1))
                continue

            if response.status_code in TRANSIENT_STATUS_CODES:
                last_error = SourceFetchError(
                    f"Transient HTTP {response.status_code} while fetching "
                    f"{requested_url}"
                )
                if attempt == self.max_attempts:
                    break
                self._sleep(self._retry_delay(response, attempt))
                continue

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                raise SourceFetchError(
                    f"HTTP {response.status_code} while fetching {requested_url}"
                ) from error

            return self._store_response(requested_url, response)

        raise SourceFetchError(
            f"Unable to fetch {requested_url} after {self.max_attempts} attempts: "
            f"{last_error}"
        ) from last_error

    def _pace_request(self) -> None:
        now = time.monotonic()
        if self._last_request_at is not None:
            remaining = self.minimum_interval_seconds - (now - self._last_request_at)
            if remaining > 0:
                self._sleep(remaining)
        self._last_request_at = time.monotonic()

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return min(max(float(retry_after), 0.0), 30.0)
            except ValueError:
                pass
        return 0.5 * 2 ** (attempt - 1)

    def _store_response(
        self, requested_url: str, response: httpx.Response
    ) -> FetchedResource:
        content = response.content
        checksum = hashlib.sha256(content).hexdigest()
        retrieved_datetime = datetime.now(timezone.utc)
        retrieved_at = retrieved_datetime.isoformat()
        metadata = RetrievalMetadata(
            source_url=str(response.url),
            retrieved_at=retrieved_at,
            sha256=checksum,
            etag=response.headers.get("ETag"),
            last_modified=response.headers.get("Last-Modified"),
            content_type=response.headers.get("Content-Type"),
        )

        objects_dir = self.cache_dir / "objects"
        index_dir = self.cache_dir / "index"
        records_dir = self.cache_dir / "records" / _url_checksum(requested_url)
        objects_dir.mkdir(parents=True, exist_ok=True)
        index_dir.mkdir(parents=True, exist_ok=True)
        records_dir.mkdir(parents=True, exist_ok=True)

        body_path = objects_dir / f"{checksum}.body"
        record_name = (
            retrieved_datetime.strftime("%Y%m%dT%H%M%S.%fZ")
            + f"-{checksum}.json"
        )
        metadata_path = records_dir / record_name
        index_path = index_dir / f"{_url_checksum(requested_url)}.json"
        if not body_path.exists():
            _atomic_write(body_path, content)
        _atomic_write(
            metadata_path,
            json.dumps(asdict(metadata), indent=2, sort_keys=True).encode("utf-8"),
        )
        _atomic_write(
            index_path,
            json.dumps(
                {
                    "requested_url": requested_url,
                    "retrieved_at": retrieved_at,
                    "sha256": checksum,
                    "metadata": asdict(metadata),
                    "record": str(metadata_path.relative_to(self.cache_dir)),
                },
                indent=2,
                sort_keys=True,
            ).encode("utf-8"),
        )
        return FetchedResource(content=content, metadata=metadata, from_cache=False)

    def _load_fresh_cache(self, url: str) -> FetchedResource | None:
        index_path = self.cache_dir / "index" / f"{_url_checksum(url)}.json"
        try:
            index_data = json.loads(index_path.read_text(encoding="utf-8"))
            retrieved_at = datetime.fromisoformat(index_data["retrieved_at"])
            if datetime.now(timezone.utc) - retrieved_at > self.cache_max_age:
                return None
            checksum = index_data["sha256"]
            objects_dir = self.cache_dir / "objects"
            content = (objects_dir / f"{checksum}.body").read_bytes()
            if hashlib.sha256(content).hexdigest() != checksum:
                return None
            metadata = RetrievalMetadata(**index_data["metadata"])
        except (
            FileNotFoundError,
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            return None
        return FetchedResource(content=content, metadata=metadata, from_cache=True)


def _url_checksum(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _atomic_write(path: Path, content: bytes) -> None:
    temporary_path = path.with_name(f".{path.name}.tmp")
    temporary_path.write_bytes(content)
    temporary_path.replace(path)
