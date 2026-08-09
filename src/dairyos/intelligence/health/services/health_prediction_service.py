from ..models.health_risk import HealthRisk


class HealthPredictionService:


    def evaluate(

        self,

        animal_id,

        milk_decline,

        health_events,

        activity_change

    ):


        score = 0


        if milk_decline:

            score += 35


        if health_events:

            score += 40


        if activity_change:

            score += 25


        if score >= 70:

            risk_level = "HIGH"

            recommendation = "Veterinary review required"


        elif score >= 30:

            risk_level = "MEDIUM"

            recommendation = "Monitor animal closely"


        else:

            risk_level = "LOW"

            recommendation = "Continue normal observation"


        return HealthRisk(

            animal_id,

            score,

            risk_level,

            recommendation

        )