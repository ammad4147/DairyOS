from dairyos.platform.drilldown.models.navigation_context import (
    NavigationContext,
)



class NavigationService:
    """
    Enterprise dashboard drill-down context manager.
    """



    def create_context(
        self,
        level,
        entity_type,
        entity_id=None,
        parent_id=None,
    ):


        return NavigationContext(

            level=level,

            entity_type=entity_type,

            entity_id=entity_id,

            parent_id=parent_id,

        )



    def next_level(
        self,
        context,
    ):


        hierarchy = {

            "executive": "farm",

            "farm": "domain",

            "domain": "entity",

            "entity": "event",

        }


        return hierarchy.get(

            context.level

        )

