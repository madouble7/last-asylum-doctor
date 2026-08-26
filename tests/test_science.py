"""Tests for normalization, validation, and synthetic end-to-end ingestion."""

import json
from dataclasses import dataclass

import pytest

from last_asylum_doctor.models import ResearchValidationError, RetrievalMetadata
from last_asylum_doctor.scraping.client import FetchedResource
from last_asylum_doctor.scraping.science import (
    ScienceIngestionError,
    ScienceIngestor,
    normalize_research_payload,
)

BASE_URL = "https://example.test/"
MODULE = (
    "var e=`11022`,t=`def-boost-iii`,l=["
    "{level:1,time_sec:964e3,time:`11d 3h 46m 40s`,power:15020,raw_id:11022001,"
    "costs:[{resource:`Farms`,amount:31736e3,amount_fmt:`31736000`},"
    "{resource:`Herbs`,amount:97332e3,amount_fmt:`97332000`},"
    "{resource:`Study Scroll`,amount:1440,item_id:`item_research_info`,"
    "amount_fmt:`1440`}]}],"
    "f={id:e,slug:t,name:`DEF Boost III`,description:`Soldier DEF`,"
    "tab:`Elite Troop`,tab_slug:`elite-troop`,tech_type:11,max_level:1,"
    "levels_count:1,levels:l,image:`/images/science/def-boost-iii.png`,"
    "pos:`1_13_2`};export{f as default};"
)


def test_normalizes_generic_costs_and_exact_source_numbers() -> None:
    from last_asylum_doctor.scraping.esm import parse_research_module

    node = normalize_research_payload(
        parse_research_module(MODULE),
        expected_slug="def-boost-iii",
        source_page_url=f"{BASE_URL}science/def-boost-iii",
        source_asset_url=f"{BASE_URL}assets/def-boost-iii-Hash.js",
        retrieval=_metadata(f"{BASE_URL}assets/def-boost-iii-Hash.js"),
    )

    level = node.levels[0]
    assert level.time_seconds == 964_000
    assert level.power == 15_020
    assert level.costs == {
        "farms": 31_736_000,
        "herbs": 97_332_000,
        "study_scroll": 1_440,
    }
    assert level.source_costs[-1].source_label == "Study Scroll"
    assert level.source_costs[-1].item_id == "item_research_info"


def test_rejects_noncontiguous_levels() -> None:
    payload = {
        "id": "1",
        "slug": "sample",
        "name": "Sample",
        "description": "Effect",
        "tab": "Tree",
        "tab_slug": "tree",
        "max_level": 2,
        "levels_count": 2,
        "levels": [
            _raw_level(1),
            _raw_level(3),
        ],
    }

    with pytest.raises(ResearchValidationError, match="contiguous"):
        normalize_research_payload(
            payload,
            expected_slug="sample",
            source_page_url=f"{BASE_URL}science/sample",
            source_asset_url=f"{BASE_URL}assets/sample-Hash.js",
            retrieval=_metadata(f"{BASE_URL}assets/sample-Hash.js"),
        )


def test_synthetic_ingestion_pipeline_writes_normalized_json(tmp_path) -> None:
    urls = {
        f"{BASE_URL}robots.txt": "User-agent: *\nAllow: /\n",
        f"{BASE_URL}science": (
            '<div id="root"></div><script type="module" '
            'src="/assets/index-Main.js"></script>'
        ),
        f"{BASE_URL}sitemap.xml": (
            '<?xml version="1.0"?><urlset>'
            f"<url><loc>{BASE_URL}science/def-boost-iii</loc></url>"
            "</urlset>"
        ),
        f"{BASE_URL}assets/index-Main.js": (
            'var Dr=Object.assign({"../content/science/def-boost-iii.json":'
            '()=>S(()=>import(`./def-boost-iii-Hash.js`),[])})'
        ),
        f"{BASE_URL}assets/def-boost-iii-Hash.js": MODULE,
    }
    client = _FakeClient(urls)
    output_path = tmp_path / "processed" / "research_sample.json"

    result = ScienceIngestor(client, base_url=BASE_URL).ingest(
        ["def-boost-iii"], output_path
    )
    output = json.loads(output_path.read_text(encoding="utf-8"))

    assert result.sitemap_science_slug_count == 1
    assert [node.slug for node in result.nodes] == ["def-boost-iii"]
    assert output["nodes"][0]["levels"][0]["costs"]["farms"] == 31_736_000
    assert client.requested == list(urls)


def test_ingestion_requires_explicit_targeted_slugs(tmp_path) -> None:
    with pytest.raises(ScienceIngestionError, match="explicit science slug"):
        ScienceIngestor(_FakeClient({}), base_url=BASE_URL).ingest(
            [], tmp_path / "unused.json"
        )


def _raw_level(level: int) -> dict[str, object]:
    return {
        "level": level,
        "time_sec": 1,
        "time": "1s",
        "power": 1,
        "costs": [],
    }


def _metadata(url: str) -> RetrievalMetadata:
    return RetrievalMetadata(
        source_url=url,
        retrieved_at="2026-08-26T00:00:00+00:00",
        sha256="0" * 64,
    )


@dataclass
class _FakeClient:
    responses: dict[str, str]

    def __post_init__(self) -> None:
        self.requested: list[str] = []

    def fetch(self, url: str, *, refresh: bool = False) -> FetchedResource:
        del refresh
        self.requested.append(url)
        content = self.responses[url].encode()
        return FetchedResource(
            content=content,
            metadata=_metadata(url),
            from_cache=False,
        )
