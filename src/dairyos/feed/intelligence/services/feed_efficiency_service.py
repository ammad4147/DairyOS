from dairyos.feed.intelligence.models import FeedEfficiency


class FeedEfficiencyService:


    def calculate_efficiency(
        self,
        animal_group: str,
        milk_output: float,
        dry_matter_intake: float,
    ) -> FeedEfficiency:


        return FeedEfficiency(
            animal_group=animal_group,
            milk_output_liters=milk_output,
            dry_matter_intake_kg=dry_matter_intake,
        )
