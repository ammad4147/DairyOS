from dairyos.feed.intelligence import FeedEfficiencyService


def test_feed_efficiency_calculation():

    service = FeedEfficiencyService()


    result = service.calculate_efficiency(
        animal_group="MILKING_COWS",
        milk_output=500,
        dry_matter_intake=250,
    )


    assert result.milk_output_liters == 500
    assert result.dry_matter_intake_kg == 250
    assert result.efficiency == 2
