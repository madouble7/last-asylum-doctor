"""Tests for safe parsing of the observed data-only ESM structure."""

import pytest

from last_asylum_doctor.scraping.esm import ModuleParseError, parse_research_module


def test_parses_aliases_nested_literals_and_scientific_notation() -> None:
    module = (
        "var e=`11022`,t=`def-boost-iii`,n=`DEF Boost III`,"
        "l=[{level:1,time_sec:964e3,time:`11d 3h 46m 40s`,power:15020,"
        "costs:[{resource:`Farms`,amount:31736e3,amount_fmt:`31736000`},"
        "{resource:`Study Scroll`,amount:1440,item_id:`item_research_info`,"
        "amount_fmt:`1440`}]}],"
        "f={id:e,slug:t,name:n,description:`Soldier DEF`,tab:`Elite Troop`,"
        "tab_slug:`elite-troop`,tech_type:11,max_level:1,levels_count:1,levels:l};"
        "export{f as default,l as levels};"
    )

    parsed = parse_research_module(module)

    assert parsed["id"] == "11022"
    assert parsed["levels"][0]["time_sec"] == 964_000
    assert parsed["levels"][0]["costs"][0]["amount"] == 31_736_000


def test_rejects_executable_javascript() -> None:
    with pytest.raises(ModuleParseError, match="unsupported"):
        parse_research_module("var f=alert(`unsafe`);export{f as default};")


def test_rejects_template_interpolation() -> None:
    with pytest.raises(ModuleParseError, match="template interpolation"):
        parse_research_module("var f={name:`${danger}`};export{f as default};")
