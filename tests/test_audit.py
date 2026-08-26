"""Tests for bounded research schema profiling without network access."""

from last_asylum_doctor.scraping.audit import (
    REQUIRED_AUDIT_SLUGS,
    audit_module,
    build_audit_report,
    select_representative_sample,
)


def test_sample_includes_required_slugs_and_category_coverage() -> None:
    slugs = list(REQUIRED_AUDIT_SLUGS) + [
        "alpha-one",
        "alpha-two",
        "beta-one",
        "beta-two",
        "gamma-one",
        "gamma-two",
    ]
    page_urls = {slug: f"https://example.test/science/{slug}" for slug in slugs}
    asset_urls = {slug: f"https://example.test/assets/{slug}.js" for slug in slugs}
    catalog = {
        slug: {"slug": slug, "tab_slug": slug.split("-")[0]}
        for slug in slugs
    }

    sample = select_representative_sample(
        page_urls, asset_urls, catalog, sample_size=5
    )

    assert sample[:3] == list(REQUIRED_AUDIT_SLUGS)
    assert len(sample) == 5
    assert len(set(sample)) == 5


def test_audit_reports_dropped_and_redundant_source_fields() -> None:
    source = (
        "var e=`1`,l=[{level:1,time_sec:1,time:`1s`,power:2,ability:2,"
        "cost_farms:3,costs:[{resource:`Farms`,amount:3,amount_fmt:`3`}]}],"
        "f={id:e,slug:`sample`,name:`Sample`,description:`Effect`,tab:`Tree`,"
        "tab_slug:`tree`,tech_type:1,max_level:1,levels_count:1,levels:l,"
        "extra_top:`source fact`};export{f as default};"
    )
    node = audit_module(
        "sample",
        source,
        source_page_url="https://example.test/science/sample",
        source_asset_url="https://example.test/assets/sample.js",
        catalog_entry=None,
    )
    report = build_audit_report(
        [node],
        sample_method="test",
        sitemap_science_slug_count=1,
        main_bundle_url="https://example.test/assets/index.js",
        catalog_error=None,
    )

    assert node["status"] == "failure"
    assert node["failure_stage"] == "normalization_or_validation"
    top_fields = {
        field["field"]
        for field in node["field_compatibility"]["top_level"]
    }
    top_classifications = {
        field["field"]: field["classification"]
        for field in node["field_compatibility"]["top_level"]
    }
    level_classifications = {
        field["field"]: field["classification"]
        for field in node["field_compatibility"]["level"]
    }
    assert "extra_top" in top_fields
    assert top_classifications["extra_top"] == "C"
    assert level_classifications["ability"] == "B"
    assert level_classifications["cost_farms"] == "B"
    assert report["meaningful_fields_currently_dropped"] == [
        {
            "scope": "top_level",
            "field": "extra_top",
            "classification": "C",
            "reason": "meaningful factual field is not currently preserved",
        }
    ]


def test_audit_records_parse_failures_without_hiding_them() -> None:
    node = audit_module(
        "sample",
        "var f=alert(`unsafe`);export{f as default};",
        source_page_url="https://example.test/science/sample",
        source_asset_url="https://example.test/assets/sample.js",
        catalog_entry=None,
    )

    assert node["status"] == "failure"
    assert node["failure_stage"] == "parser"
