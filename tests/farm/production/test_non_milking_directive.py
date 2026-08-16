from dairyos.farm.production.models.non_milking_directive import (
    NonMilkingDirective,
)


def test_none_remains_in_active_milking_herd():
    directive = NonMilkingDirective.NONE

    assert directive.is_outside_active_milking_herd is False
    assert directive.expects_milk is False


def test_temporary_non_milking_leaves_active_milking_herd():
    directive = NonMilkingDirective.TEMPORARY_NON_MILKING

    assert directive.is_outside_active_milking_herd is True
    assert directive.expects_milk is False


def test_milk_separately_leaves_active_milking_herd_but_expects_milk():
    directive = NonMilkingDirective.MILK_SEPARATELY

    assert directive.is_outside_active_milking_herd is True
    assert directive.expects_milk is True


def test_permanent_non_milking_leaves_active_milking_herd():
    directive = NonMilkingDirective.PERMANENT_NON_MILKING

    assert directive.is_outside_active_milking_herd is True
    assert directive.expects_milk is False


def test_directive_values_are_stable():
    assert NonMilkingDirective.NONE.value == "NONE"
    assert (
        NonMilkingDirective.TEMPORARY_NON_MILKING.value
        == "TEMPORARY_NON_MILKING"
    )
    assert (
        NonMilkingDirective.MILK_SEPARATELY.value
        == "MILK_SEPARATELY"
    )
    assert (
        NonMilkingDirective.PERMANENT_NON_MILKING.value
        == "PERMANENT_NON_MILKING"
    )
