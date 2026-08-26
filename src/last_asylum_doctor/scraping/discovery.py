"""Discovery helpers for current LastAsylumDatabase.com assets and slugs."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin, urlparse
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree


class SourceDiscoveryError(ValueError):
    """Raised when the source site's discoverable structure has changed."""


_SCIENCE_IMPORT = re.compile(
    r'''["']\.\./content/science/(?P<slug>[a-z0-9-]+)\.json["']\s*:
        \s*\(\)\s*=>.{0,200}?import\(\s*[`"'](?P<asset>\./[^`"']+\.js)[`"']\s*\)''',
    re.VERBOSE | re.DOTALL,
)
_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def discover_main_bundle(html: str, page_url: str) -> str:
    """Find the same-origin Vite entry module referenced by initial HTML."""
    parser = _ModuleScriptParser()
    parser.feed(html)
    page_origin = _origin(page_url)
    candidates = [
        urljoin(page_url, source)
        for source in parser.sources
        if source.lower().endswith(".js")
        and "/assets/" in urlparse(urljoin(page_url, source)).path
        and _origin(urljoin(page_url, source)) == page_origin
    ]
    if not candidates:
        raise SourceDiscoveryError(
            "Initial HTML did not contain a same-origin Vite module asset"
        )
    preferred = [
        candidate
        for candidate in candidates
        if urlparse(candidate).path.rsplit("/", 1)[-1].startswith("index-")
    ]
    if len(preferred) == 1:
        return preferred[0]
    if len(candidates) == 1:
        return candidates[0]
    raise SourceDiscoveryError(
        f"Could not identify one main bundle; candidates were: {candidates}"
    )


def discover_science_asset_urls(
    bundle_source: str, bundle_url: str
) -> dict[str, str]:
    """Map logical science slugs to current hashed ESM asset URLs."""
    result: dict[str, str] = {}
    for match in _SCIENCE_IMPORT.finditer(bundle_source):
        slug = match.group("slug")
        asset_url = urljoin(bundle_url, match.group("asset"))
        existing = result.get(slug)
        if existing is not None and existing != asset_url:
            raise SourceDiscoveryError(
                f"Conflicting science assets found for slug {slug!r}"
            )
        result[slug] = asset_url
    if not result:
        raise SourceDiscoveryError(
            "Main bundle did not expose the expected science dynamic-import map"
        )
    return result


def discover_science_pages(sitemap_xml: str, base_url: str) -> dict[str, str]:
    """Read public `/science/{slug}` entries from a sitemap."""
    try:
        root = ElementTree.fromstring(sitemap_xml)
    except ElementTree.ParseError as error:
        raise SourceDiscoveryError("Sitemap is not valid XML") from error

    expected_origin = _origin(base_url)
    result: dict[str, str] = {}
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "loc" or not element.text:
            continue
        url = element.text.strip()
        parsed = urlparse(url)
        if _origin(url) != expected_origin:
            continue
        parts = [unquote(part) for part in parsed.path.strip("/").split("/")]
        if len(parts) != 2 or parts[0] != "science":
            continue
        slug = parts[1]
        if not _SLUG.fullmatch(slug):
            raise SourceDiscoveryError(f"Invalid science slug in sitemap: {slug!r}")
        existing = result.get(slug)
        if existing is not None and existing != url:
            raise SourceDiscoveryError(f"Duplicate sitemap entries for {slug!r}")
        result[slug] = url
    if not result:
        raise SourceDiscoveryError("Sitemap contained no science node URLs")
    return result


def ensure_robots_allowed(
    robots_text: str, robots_url: str, user_agent: str, urls: list[str]
) -> None:
    """Fail before retrieval if robots.txt disallows any intended URL."""
    policy = RobotFileParser()
    policy.set_url(robots_url)
    policy.parse(robots_text.splitlines())
    disallowed = [url for url in urls if not policy.can_fetch(user_agent, url)]
    if disallowed:
        raise SourceDiscoveryError(
            "robots.txt disallows intended source access: " + ", ".join(disallowed)
        )


def validate_slug(slug: str) -> str:
    """Reject malformed or path-like input before constructing URLs."""
    if not _SLUG.fullmatch(slug):
        raise SourceDiscoveryError(f"Invalid science slug: {slug!r}")
    return slug


def _origin(url: str) -> tuple[str, str, int | None]:
    parsed = urlparse(url)
    return parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.port


class _ModuleScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[str] = []

    def handle_starttag(
        self, tag: str, attributes: list[tuple[str, str | None]]
    ) -> None:
        if tag.lower() != "script":
            return
        values = dict(attributes)
        if values.get("type", "").lower() == "module" and values.get("src"):
            self.sources.append(values["src"] or "")
