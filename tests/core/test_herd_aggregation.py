from dairyos.herd.intelligence.services.herd_aggregator import HerdAggregator

from dairyos.herd.dashboard.services.herd_command_service import HerdCommandService



def test_context_creation():

    aggregator = HerdAggregator()

    context = aggregator.build(

        farm_name="Trident Dairies",

        total_animals=100

    )


    assert context.total_animals == 100



def test_context_to_command():

    context = HerdAggregator().build(

        farm_name="Trident Dairies",

        total_animals=100

    )


    command = HerdCommandService().generate_from_context(context)


    assert command.farm_name == "Trident Dairies"



def test_health_signal_propagation():

    context = HerdAggregator().build(

        farm_name="Trident Dairies",

        total_animals=100,

        health_alerts=2

    )


    command = HerdCommandService().generate_from_context(context)


    assert command.health_status == "ATTENTION REQUIRED"



def test_reproduction_signal_propagation():

    context = HerdAggregator().build(

        farm_name="Trident Dairies",

        total_animals=100,

        open_cows=5

    )


    command = HerdCommandService().generate_from_context(context)


    assert command.reproduction_status == "MONITOR"



def test_production_signal():

    context = HerdAggregator().build(

        farm_name="Trident Dairies",

        total_animals=100,

        production_status="HIGH"

    )


    command = HerdCommandService().generate_from_context(context)


    assert command.production_status == "HIGH"



def test_financial_signal():

    context = HerdAggregator().build(

        farm_name="Trident Dairies",

        total_animals=100,

        financial_status="WARNING"

    )


    command = HerdCommandService().generate_from_context(context)


    assert command.financial_status == "WARNING"



def test_replacement_risk():

    context = HerdAggregator().build(

        farm_name="Trident Dairies",

        total_animals=100,

        replacement_shortage=True

    )


    command = HerdCommandService().generate_from_context(context)


    assert command.overall_risk == "HIGH"
