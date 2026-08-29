import pytest

from dairyos.farm.herd.services.animal_classification_service import (
    AnimalCategory,
    AnimalClassificationError,
    AnimalClassificationService,
)


def test_milking_cow_classification_is_canonical():
    result = AnimalClassificationService.classify("LACTATING", "FEMALE")

    assert result.category is AnimalCategory.MILKING_COWS
    assert result.lifecycle_status == "LACTATING"
    assert result.sex == "FEMALE"


def test_dry_cow_classification_is_canonical():
    result = AnimalClassificationService.classify("DRY", "FEMALE")

    assert result.category is AnimalCategory.DRY_COWS


def test_legacy_male_heifer_pair_is_normalised_to_bull():
    result = AnimalClassificationService.classify("HEIFER", "MALE")

    assert result.category is AnimalCategory.BULLS
    assert result.lifecycle_status == "BULL"
    assert result.sex == "MALE"


def test_bull_category_never_translates_back_to_heifer():
    result = AnimalClassificationService.from_category("Bulls")

    assert result.category is AnimalCategory.BULLS
    assert result.lifecycle_status == "BULL"
    assert result.sex == "MALE"


def test_calves_are_split_by_sex():
    assert (
        AnimalClassificationService.classify("CALF", "FEMALE").category
        is AnimalCategory.FEMALE_CALVES
    )
    assert (
        AnimalClassificationService.classify("CALF", "MALE").category
        is AnimalCategory.MALE_CALVES
    )


def test_exited_animals_are_not_presented_as_active_categories():
    for lifecycle in ("SOLD", "CULLED", "DECEASED"):
        result = AnimalClassificationService.classify(lifecycle, "FEMALE")
        assert result.category is AnimalCategory.EXITED


def test_invalid_male_cow_lifecycle_is_rejected():
    with pytest.raises(AnimalClassificationError):
        AnimalClassificationService.classify("LACTATING", "MALE")


def test_invalid_female_bull_lifecycle_is_rejected():
    with pytest.raises(AnimalClassificationError):
        AnimalClassificationService.classify("BULL", "FEMALE")


def test_unknown_category_is_rejected():
    with pytest.raises(AnimalClassificationError):
        AnimalClassificationService.from_category("Unknown Category")
