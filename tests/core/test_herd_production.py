from datetime import date


from dairyos.herd.production.models import (

    MilkRecord,

    ProductionGroup

)


from dairyos.herd.production.services.production_service import (

    ProductionService

)



def test_milk_record_total():


    record = MilkRecord(

        animal_id="HF-7001",

        production_date=date.today(),

        morning_litres=13,

        evening_litres=12

    )


    assert record.total_litres == 25



def test_production_tracking():


    service = ProductionService()


    record = MilkRecord(

        animal_id="HF-7002",

        production_date=date.today(),

        morning_litres=15,

        evening_litres=10

    )


    service.record_milk(record)


    assert service.milk_record_count() == 1



def test_production_group():


    service = ProductionService()


    group = ProductionGroup(

        name="PEAK_LACTATION",

        description="High producing cows"

    )


    service.add_group(group)


    assert service.group_count() == 1
