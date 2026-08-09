from datetime import date


from dairyos.herd.nutrition.models import (

    FeedPlan,

    FeedConsumption

)


from dairyos.herd.nutrition.services.nutrition_service import (

    NutritionService

)



def test_feed_plan_creation():


    plan = FeedPlan(

        group_name="HIGH_LACTATION",

        silage_kg=25,

        concentrate_kg=8,

        mineral_grams=100

    )


    assert plan.concentrate_kg == 8



def test_feed_consumption_tracking():


    service = NutritionService()


    consumption = FeedConsumption(

        group_name="MILKING_COWS",

        consumption_date=date.today(),

        total_feed_kg=750,

        animals_count=25

    )


    service.record_consumption(

        consumption

    )


    assert service.consumption_count() == 1



def test_nutrition_service():


    service = NutritionService()


    plan = FeedPlan(

        group_name="DRY_COWS",

        silage_kg=15,

        concentrate_kg=3,

        mineral_grams=80

    )


    service.add_feed_plan(plan)


    assert service.feed_plan_count() == 1
