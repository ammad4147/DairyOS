from dairyos.dashboard.models.dashboard_widget import (
    DashboardWidget,
)


class OwnerAttentionWidget:
    """
    Builds the owner attention dashboard widget.

    Presentation only.

    Uses already-generated operational signals.
    Does not create decisions.
    """

    def build(
        self,
        *,
        attention=None,
    ):

        attention = attention or []

        return DashboardWidget(

            widget_id="owner.attention",

            title="Owner Attention",

            subtitle=(
                "Items requiring review or action"
            ),

            value=attention,

            status=(
                "CRITICAL"
                if attention
                else "NORMAL"
            ),

            importance="CRITICAL",

            actionability="ACTION",

            zone="owner_attention",

            size="LARGE",

            has_alert=bool(attention),

            has_action=bool(attention),

            click_target="/command-center",

        )