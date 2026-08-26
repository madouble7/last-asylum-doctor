"""Tests for source discovery without network access."""

import pytest

from last_asylum_doctor.scraping.discovery import (
    SourceDiscoveryError,
    discover_main_bundle,
    discover_science_asset_urls,
    discover_science_pages,
    ensure_robots_allowed,
)


def test_discovers_current_main_bundle_from_html() -> None:
    html = '<div id="root"></div><script type="module" src="/assets/index-Ab12.js">'

    assert discover_main_bundle(html, "https://example.test/science") == (
        "https://example.test/assets/index-Ab12.js"
    )


def test_discovers_science_dynamic_import_mapping() -> None:
    bundle = (
        'var Dr=Object.assign({"../content/science/def-boost-iii.json":'
        '()=>S(()=>import(`./def-boost-iii-Hash1.js`),[]),'
        '"../content/science/training-points.json":'
        '()=>S(()=>import(`./training-points-Hash2.js`),[])})'
    )

    assert discover_science_asset_urls(
        bundle, "https://example.test/assets/index-Main.js"
    ) == {
        "def-boost-iii": "https://example.test/assets/def-boost-iii-Hash1.js",
        "training-points": "https://example.test/assets/training-points-Hash2.js",
    }


def test_discovers_only_science_node_urls_from_sitemap() -> None:
    sitemap = """<?xml version="1.0"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.test/science</loc></url>
      <url><loc>https://example.test/science/def-boost-iii</loc></url>
      <url><loc>https://example.test/buildings/sanctuary</loc></url>
      <url><loc>https://other.test/science/not-ours</loc></url>
    </urlset>"""

    assert discover_science_pages(sitemap, "https://example.test/") == {
        "def-boost-iii": "https://example.test/science/def-boost-iii"
    }


def test_robots_policy_fails_closed_for_disallowed_url() -> None:
    robots = "User-agent: *\nDisallow: /assets/"

    with pytest.raises(SourceDiscoveryError, match="robots.txt disallows"):
        ensure_robots_allowed(
            robots,
            "https://example.test/robots.txt",
            "LastAsylumDoctor/0.1",
            ["https://example.test/assets/index.js"],
        )
