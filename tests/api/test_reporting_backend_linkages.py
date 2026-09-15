from pathlib import Path

from dairyos.api.reporting import REPORTS


def test_every_reporting_catalog_entry_has_backend_dispatch():
    source = Path("src/dairyos/api/reporting.py").read_text(encoding="utf-8")
    for report in REPORTS:
        assert f'"{report.id}"' in source


def test_reporting_backend_is_read_only_projection():
    source = Path("src/dairyos/api/reporting.py").read_text(encoding="utf-8")
    for forbidden in (".commit(", ".add(", ".delete(", ".save(", ".update("):
        assert forbidden not in source


def test_reporting_normalizes_datetime_before_date_comparison():
    source = Path("src/dairyos/api/reporting.py").read_text(encoding="utf-8")
    datetime_check = source.index("if isinstance(value, datetime):")
    date_check = source.index("if isinstance(value, date):")
    assert datetime_check < date_check


def test_reporting_no_longer_has_unimplemented_catalog_routes():
    source = Path("src/dairyos/api/reporting.py").read_text(encoding="utf-8")
    dispatch = source[source.index("def _canonical_dataset"):source.index('@router.get("/catalog")')]
    expected = {report.id for report in REPORTS}
    assert all(report_id in dispatch for report_id in expected)
