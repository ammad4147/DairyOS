from dairyos.platform.command_center.drilldown.models.drilldown_path import (
    DrilldownPath,
)



class DrilldownService:
    """
    Provides entity navigation across Command Center.
    """



    def build_path(
        self,
        levels,
    ):


        return DrilldownPath(

            levels=levels

        )



    def entity_history_reference(
        self,
        entity_type,
        entity_id,
    ):


        return {

            "entity_type": entity_type,

            "entity_id": entity_id,

            "timeline_available": True,

        }

