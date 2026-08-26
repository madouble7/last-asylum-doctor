"""Offline tests for explicit full-corpus science ingestion."""

import json
from dataclasses import dataclass

from last_asylum_doctor.models import RetrievalMetadata
from last_asylum_doctor.scraping.client import FetchedResource
from last_asylum_doctor.scraping.corpus import (
    ScienceCorpusIngestor,
    reconcile_science_sources,
)

BASE_URL = "https://example.test/"


def test_reconciliation_reports_each_source_difference() -> None:
    reconciliation = reconcile_science_sources(
        {"alpha": "page-alpha", "sitemap-only": "page-only"},
        {"alpha": "asset-alpha", "import-only": "asset-only"},
        "https://example.test/assets/index.js",
    )

    assert reconciliation.sitemap_science_slug_count == 2
    assert reconciliation.import_map_science_slug_count == 2
    assert reconciliation.intersection_count == 1
    assert reconciliation.sitemap_only_slugs == ("sitemap-only",)
    assert reconciliation.import_map_only_slugs == ("import-only",)


def test_full_ingestion_records_partial_node_failure(tmp_path) -> None:
    urls = {
        f"{BASE_URL}robots.txt": "User-agent: *\nAllow: /\n",
        f"{BASE_URL}science": (
            '<script type="module" src="/assets/index-Main.js"></script>'
        ),
        f"{BASE_URL}sitemap.xml": (
            "<?xml version='1.0'?><urlset>"
            f"<url><loc>{BASE_URL}science/alpha</loc></url>"
            f"<url><loc>{BASE_URL}science/beta</loc></url></urlset>"
        ),
        f"{BASE_URL}assets/index-Main.js": (
            'var m={"../content/science/alpha.json":()=>import(`./alpha.js`),'
            '"../content/science/beta.json":()=>import(`./beta.js`)}'
        ),
        f"{BASE_URL}assets/alpha.js": _module("alpha"),
        f"{BASE_URL}assets/beta.js": "var f=alert(`not data`);export{f as default};",
    }
    output_path = tmp_path / "research_corpus.json"
    result = ScienceCorpusIngestor(_FakeClient(urls), base_url=BASE_URL).ingest(
        output_path
    )
    output = json.loads(output_path.read_text(encoding="utf-8"))

    assert result.requested_slugs == ("alpha", "beta")
    assert [node.slug for node in result.nodes] == ["alpha"]
    assert [failure.slug for failure in result.failures] == ["beta"]
    assert "unsupported or unknown identifier" in result.failures[0].reason
    assert output["reconciliation"]["intersection_count"] == 2
    assert output["failures"][0]["slug"] == "beta"


def _module(slug: str) -> str:
    return (
        "var l=[{level:1,time_sec:1,time:`1s`,power:1,costs:[]}],"
        f"f={{id:`1`,slug:`{slug}`,name:`{slug}`,description:`effect`,tab:`Tree`,"
        "tab_slug:`tree`,max_level:1,levels_count:1,levels:l};"
        "export{f as default};"
    )


@dataclass
class _FakeClient:
    responses: dict[str, str]

    def fetch(self, url: str, *, refresh: bool = False) -> FetchedResource:
        del refresh
        content = self.responses[url].encode("utf-8")
        return FetchedResource(
            content=content,
            metadata=RetrievalMetadata(
                source_url=url,
                retrieved_at="2026-08-26T00:00:00+00:00",
                sha256="a" * 64,
            ),
            from_cache=False,
        )
