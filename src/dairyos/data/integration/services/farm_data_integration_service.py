from ..models.farm_event import FarmEvent



class FarmDataIntegrationService:



    def create_event(

        self,

        event_id,

        event_type,

        source_module,

        entity_id,

        value

    ):


        return FarmEvent(

            event_id,

            event_type,

            source_module,

            entity_id,

            value,

            "SYNCED"

        )
