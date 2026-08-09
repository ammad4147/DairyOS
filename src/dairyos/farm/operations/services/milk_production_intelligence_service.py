from dairyos.farm.operations.services.milk_production_intelligence import (
    MilkProductionIntelligence,
)


class MilkProductionIntelligenceService:
    """
    Generates milk production intelligence
    from verified FarmOperationalState milk facts.

    Source:
        FarmOperationalState.milk_status

    Rules:
        - Operational state remains source of truth.
        - No mutation of farm facts.
        - No automatic production creation.
        - Intelligence only.
    """


    def __init__(
        self,
        operational_state_service,
    ):

        self.operational_state_service = (
            operational_state_service
        )



    def generate(
        self,
    ) -> MilkProductionIntelligence:

        state = (
            self.operational_state_service
            .get_state()
        )


        milk_status = (
            state.milk_status
        )


        total_litres = 0.0


        shift_production = {}


        completed_checkpoints = []


        operational_signals = []


        notes = []



        for shift, record in milk_status.items():


            litres = record.get(
                "litres",
                0,
            )


            total_litres += litres


            shift_production[shift] = litres



            if record.get(
                "status"
            ) == "completed":

                completed_checkpoints.append(
                    shift
                )



            if litres == 0:

                operational_signals.append(
                    {
                        "type":
                            "ZERO_PRODUCTION_CHECKPOINT",

                        "checkpoint":
                            shift,

                        "severity":
                            "ATTENTION",
                    }
                )



        schedule_state = getattr(
            state,
            "schedule_state",
            None,
        )


        expected_checkpoints = []


        if schedule_state is not None:


            expected_checkpoints = list(
                getattr(
                    schedule_state,
                    "milk_checkpoints",
                    []
                )
            )



        missing_checkpoints = [

            checkpoint

            for checkpoint in expected_checkpoints

            if checkpoint
            not in completed_checkpoints

        ]



        if missing_checkpoints:

            operational_signals.append(
                {
                    "type":
                        "MISSING_MILK_CHECKPOINT",

                    "checkpoints":
                        missing_checkpoints,

                    "severity":
                        "ATTENTION",
                }
            )


            notes.append(
                "Milk production entry incomplete for scheduled checkpoints."
            )



        production_status = (

            "VERIFIED"

            if not missing_checkpoints

            else

            "INCOMPLETE"

        )



        shift_contribution = {}


        if total_litres > 0:


            for shift, litres in shift_production.items():

                shift_contribution[shift] = (

                    litres
                    /
                    total_litres

                ) * 100



        dominant_shift = None


        if shift_production:


            dominant_shift = max(

                shift_production,

                key=shift_production.get,

            )



        production_analytics = {

            "daily_total_litres":
                total_litres,


            "completed_checkpoints":
                len(
                    completed_checkpoints
                ),


            "expected_checkpoints":
                len(
                    expected_checkpoints
                ),


            "missing_checkpoints":
                len(
                    missing_checkpoints
                ),


            "dominant_shift":
                dominant_shift,


            "shift_count":
                len(
                    shift_production
                ),

        }



        return MilkProductionIntelligence(

            total_litres=total_litres,

            shift_production=shift_production,

            shift_contribution=shift_contribution,

            expected_checkpoints=expected_checkpoints,

            completed_checkpoints=completed_checkpoints,

            missing_checkpoints=missing_checkpoints,

            production_status=production_status,

            production_analytics=production_analytics,

            operational_signals=operational_signals,

            notes=notes,

        )



    def summary(
        self,
    ):

        return (
            self.generate()
            .summary()
        )
