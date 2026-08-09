from dataclasses import dataclass


@dataclass
class FeedEfficiency:

    animal_group: str
    milk_output_liters: float
    dry_matter_intake_kg: float


    @property
    def efficiency(self) -> float:

        if self.dry_matter_intake_kg == 0:
            return 0

        return (
            self.milk_output_liters
            /
            self.dry_matter_intake_kg
        )
