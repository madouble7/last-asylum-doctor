import pytest

from last_asylum_doctor.planner import (
    RL27_REQUIREMENTS,
    TG27_REQUIREMENTS,
    AccountState,
    plan_recovery,
)


def account(**overrides):
    values = {
        "antitoxin": 0,
        "grain": 0,
        "timber": 0,
        "herbs": 0,
        "sanctuary_27_remaining_seconds": 1000,
        "construction_speedup_minutes": 0,
        "training_speedup_minutes": 0,
        "universal_speedup_minutes": 0,
        "current_t8_troops": 100,
        "recoverable_or_wounded_troops": None,
        "desired_combat_ready_troops": None,
    }
    values.update(overrides)
    return values


def test_exact_tg27_resource_gaps():
    report = plan_recovery(account(antitoxin=1_000_000, grain=300_000_000))
    assert report.t9_readiness["gaps"] == {
        "antitoxin": 55_000_000,
        "grain": 0,
        "timber": 252_000_000,
        "herbs": 107_000_000,
    }


def test_exact_rl27_resource_gaps():
    report = plan_recovery(account(antitoxin=1_000_000, timber=500_000_000))
    assert report.s28_preparation["gaps"] == {
        "antitoxin": 113_000_000,
        "grain": 423_000_000,
        "timber": 0,
        "herbs": 134_000_000,
    }


def test_combined_requirements():
    report = plan_recovery(account())
    assert report.combined_s27_follow_on_bank["requirements"] == {
        resource: TG27_REQUIREMENTS[resource] + RL27_REQUIREMENTS[resource]
        for resource in TG27_REQUIREMENTS
    }


def test_fully_funded_tg27_case():
    report = plan_recovery(account(**TG27_REQUIREMENTS))
    assert report.t9_readiness["status"] == "READY"
    assert report.t9_readiness["readiness_percentage"] == 100.0
    assert "genuinely advance" in report.speedup_readiness["message"]


def test_underfunded_tg27_case_warns_about_speedups():
    report = plan_recovery(account(construction_speedup_minutes=60))
    assert report.t9_readiness["status"] == "NOT READY"
    assert "bottleneck earlier" in report.speedup_readiness["message"]


def test_zero_resource_case():
    report = plan_recovery(account())
    assert report.t9_readiness["readiness_percentage"] == 0.0
    assert report.s28_preparation["gaps"] == RL27_REQUIREMENTS


def test_troop_gap_and_nullable_recovery_fields():
    report = plan_recovery(
        account(current_t8_troops=400, desired_combat_ready_troops=1000)
    )
    assert report.post_war_recovery["additional_troops_needed_for_target"] == 600
    assert report.post_war_recovery["recoverable_or_wounded_troops"] is None


def test_account_rejects_missing_or_invalid_values():
    with pytest.raises((KeyError, ValueError)):
        AccountState.from_mapping(account(antitoxin=-1))