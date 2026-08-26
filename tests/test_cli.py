"""Tests for the starter package and command-line entry point."""

import last_asylum_doctor
from last_asylum_doctor.cli import main


def test_package_imports() -> None:
    """The package can be imported."""
    assert last_asylum_doctor is not None


def test_entry_point_prints_status(capsys) -> None:
    """The entry point prints its expected starter message."""
    main()

    assert capsys.readouterr().out == "Last Asylum Doctor is alive.\n"
