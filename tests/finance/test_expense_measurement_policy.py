from dairyos.finance.expense_measurement import allowed_units, measurement_policy, validate_unit


def test_units_are_item_specific_and_do_not_default_to_kg():
    assert allowed_units("Semen Straws (Sexed / Conventional)") == ("straw",)
    assert "kg" not in allowed_units("Vaccinations (FMD, HS, LSD, Anthrax)")
    assert "L" in allowed_units("Generator Fuel (Diesel / Petrol)")
    assert allowed_units("Insurance Premiums") == ("policy period",)


def test_legitimate_mass_items_can_still_use_kg():
    assert "kg" in allowed_units("Animal Bedding (Sand, Sawdust, Straw)")
    assert "kg" in allowed_units("LPG / Gas")


def test_invalid_unit_is_rejected_without_guessing():
    try:
        validate_unit("Semen Straws (Sexed / Conventional)", "kg")
    except ValueError as exc:
        assert "straw" in str(exc)
    else:
        raise AssertionError("invalid semen unit was accepted")


def test_unknown_item_has_no_implicit_measurement_authority():
    policy = measurement_policy("Unclassified future item")
    assert policy.units == ()
    assert policy.operational_authority == "FINANCE"
