from ..models.calf_management import CalfManagement



class CalfManagementService:

    def calculate_adg(
        self,
        birth_weight_kg: float,
        current_weight_kg: float,
        age_days: int,
    ) -> float:
        """Calculate Average Daily Gain (ADG) in kg/day."""
        if age_days <= 0 or current_weight_kg < birth_weight_kg:
            return 0.0
        return round((current_weight_kg - birth_weight_kg) / age_days, 3)

    def evaluate(
        self,
        animal_id,
        age_months,
        sex,
        birth_weight_kg: float | None = None,
        current_weight_kg: float | None = None,
    ):

        if age_months <= 3:
            growth_stage = "PRE-WEANING"
            priority = "HIGH"
            action = "Continue milk and health monitoring"

        elif age_months <= 6:
            growth_stage = "WEANING"
            priority = "MEDIUM"
            action = "Monitor growth development"

        else:
            growth_stage = "GROWING CALF"
            priority = "NORMAL"
            action = "Continue replacement development"

        adg = 0.0
        if birth_weight_kg is not None and current_weight_kg is not None and age_months > 0:
            age_days = int(age_months * 30.4375)
            adg = self.calculate_adg(birth_weight_kg, current_weight_kg, age_days)

        res = CalfManagement(
            animal_id,
            age_months,
            sex,
            growth_stage,
            priority,
            action
        )
        setattr(res, "adg_kg_per_day", adg)
        return res
