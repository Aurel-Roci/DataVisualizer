import pytest

from app.domain.parsing import extract_test_date, extract_unit_from_range, parse_tables, parse_test_row


@pytest.mark.parametrize(
    ("reference_range", "unit"),
    [
        ("70-110 mg/dL", "mg/dL"),
        ("< 5 %", "%"),
        ("3.5-5.0 mEq/L", "mEq/L"),
        ("5-10 x10³/uL", "x10³/uL"),
        ("84-96 fL", "fL"),
        ("28-34 pg", "pg"),
        ("Normal 3.5 - 5.0", ""),
        ("max 200", ""),
        ("", ""),
    ],
)
def test_extract_unit(reference_range, unit):
    assert extract_unit_from_range(reference_range) == unit


def test_label_date_preferred_and_formatted_iso():
    text = "MOSHA : 29/08/1993\nDATA E ANALIZËS : 14/03/2026 07:27:49"
    assert extract_test_date(text, None) == "2026-03-14"


def test_birthday_is_skipped_when_no_label():
    assert extract_test_date("born 29/08/1993 tested 02/09/2025", "29/08/1993") == "2025-09-02"


def test_date_falls_back_to_today_when_missing():
    assert len(extract_test_date("no dates here", None)) == 10


def test_row_index_dropped_but_integer_result_kept():
    # Regression: Platelets 308 used to be dropped and replaced by the range's lower bound (140)
    result = parse_test_row(["2", "Platelets (PLT)*", "308", "140 -400 x10³/uL"], "2026-03-14")
    assert result is not None
    assert (result.test_name, result.value, result.unit) == ("Platelets (PLT)", 308.0, "x10³/uL")


def test_zero_value_is_not_missing():
    result = parse_test_row(["Basophils", "0", "0 - 0.1 x10³/uL"], "2026-03-14")
    assert result is not None
    assert result.value == 0.0


def test_row_without_numeric_value_is_skipped():
    assert parse_test_row(["Comment", "see doctor"], "2026-03-14") is None


def test_parse_tables_skips_header_and_builds_record():
    table = [["REZULTATI", "VLERAT REFERUESE"], ["1", "Glukoza*", "91.7", "74 - 106 mg/dL"]]
    record = parse_tables([table], "Ada", "2026-03-14")
    assert record.patient_name == "Ada"
    assert record.test_date == "2026-03-14"
    assert [(r.test_name, r.value, r.unit) for r in record.results] == [("Glukoza", 91.7, "mg/dL")]
