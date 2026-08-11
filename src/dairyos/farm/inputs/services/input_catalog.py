from dairyos.farm.inputs.models.input_definition import (
    OperationalInputDefinition,
)

from dairyos.farm.inputs.models.input_type import (
    OperationalInputType,
)


class InputCatalog:
    """
    Enterprise catalogue of recognized farm operational inputs.

    Each input definition represents an operational contract
    accepted by DairyOS.

    Field aliases define operator-friendly input variations
    which are normalized into canonical DairyOS fields.

    Metadata controls downstream intelligence:
        - analytics
        - notifications
        - governance
        - normalization
    """


    @staticmethod
    def definitions():

        return [

            OperationalInputDefinition(
                input_type=OperationalInputType.MILK_PRODUCTION.value,

                name="Milk Production Entry",

                description=(
                    "Daily milk production operational records "
                    "supporting production analytics and alerts."
                ),

                required_fields=[
                    "animal_id",
                    "total_yield",
                ],

                optional_fields=[
                    "morning_yield",
                    "afternoon_yield",
                    "evening_yield",
                    "milking_session",
                ],

                field_aliases={
                    "total_yield": [
                        "litres",
                        "milk_litres",
                        "yield",
                    ],
                },

                analytics_enabled=True,

                notification_enabled=True,

                governance_required=True,

                normalization_enabled=True,
            ),



            OperationalInputDefinition(
                input_type=OperationalInputType.FEEDING.value,
                name="Feed Consumption Entry",
                description="Animal feeding operational records.",

                required_fields=[
                    "feed_type",
                    "quantity_kg",
                ],

                field_aliases={
                    "quantity_kg": [
                        "quantity",
                        "qty",
                        "feed_quantity",
                    ],
                },
            ),



            OperationalInputDefinition(
                input_type=OperationalInputType.ANIMAL_HEALTH.value,
                name="Animal Health Entry",
                description="Animal health observations and treatments.",

                required_fields=[
                    "animal_id",
                    "observation",
                ],
            ),



            OperationalInputDefinition(
                input_type=OperationalInputType.BREEDING.value,
                name="Breeding Entry",
                description="Breeding and reproduction records.",

                required_fields=[
                    "animal_id",
                    "event_type",
                ],
            ),



            OperationalInputDefinition(
                input_type=OperationalInputType.WORKFORCE.value,
                name="Workforce Entry",
                description="Farm workforce operational records.",

                required_fields=[
                    "worker_id",
                    "activity",
                ],
            ),



            OperationalInputDefinition(
                input_type=OperationalInputType.INVENTORY.value,
                name="Inventory Entry",
                description="Inventory movement records.",

                required_fields=[
                    "item",
                    "quantity",
                ],

                field_aliases={
                    "quantity": [
                        "qty",
                        "amount",
                    ],
                },
            ),



            OperationalInputDefinition(
                input_type=OperationalInputType.FINANCIAL.value,
                name="Financial Entry",
                description="Operational financial records.",

                required_fields=[
                    "transaction_type",
                    "amount",
                ],
            ),



            OperationalInputDefinition(
                input_type=OperationalInputType.EQUIPMENT.value,
                name="Equipment Entry",
                description="Equipment operational records.",

                required_fields=[
                    "equipment_id",
                    "activity",
                ],
            ),



            OperationalInputDefinition(
                input_type=OperationalInputType.TREATMENT.value,
                name="Treatment Entry",
                description=(
                    "Veterinary treatment records driving the "
                    "milk-withdrawal safety check."
                ),

                required_fields=[
                    "animal_id",
                    "medicine",
                ],

                analytics_enabled=True,

                notification_enabled=True,

                governance_required=True,
            ),

        ]
