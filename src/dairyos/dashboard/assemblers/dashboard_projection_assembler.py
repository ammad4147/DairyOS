from dairyos.dashboard.models.dashboard_layout import (
    DashboardLayout,
)

from dairyos.dashboard.models.dashboard_view import (
    DashboardView,
)

from dairyos.dashboard.models.dashboard_widget import (
    DashboardWidget,
)

from dairyos.dashboard.models.dashboard_zone import (
    DashboardZone,
)


class DashboardProjectionAssembler:
    """
    Builds the owner-facing dashboard.

    Presentation mapping only.

    No business rules.

    No calculations.
    """


    def assemble(
        self,
    ):

        layout = DashboardLayout(

            zones=[

                self._milk_zone(),

                self._herd_zone(),

                self._health_zone(),

                self._finance_zone(),

                self._analytics_zone(),

                self._alerts_zone(),

            ]

        )


        return DashboardView(

            layout=layout,

            owner_attention=[],

            farm_timeline=[],

            quick_actions=[],

            animal_spotlight=[],

        )



    def _owner_attention_zone(self):

        return DashboardZone(

            zone_id="owner_attention",

            title="Owner Attention",

            widgets=[

                DashboardWidget(

                    widget_id="owner.attention",

                    title="Owner Attention",

                    subtitle=(
                        "Items requiring review or action"
                    ),

                    value=[],

                    importance="CRITICAL",

                    actionability="ACTION",

                    zone="owner_attention",

                    size="LARGE",

                    has_alert=True,

                    has_action=True,

                    click_target="/command-center",

                )

            ],

        )

    def _milk_zone(self):

        return DashboardZone(

            zone_id="milk",

            title="Milk",

            widgets=[

                DashboardWidget(

                    widget_id="milk.today",

                    title="Milk Today",

                    value="--",

                    importance="HIGH",

                    zone="milk",

                ),

                DashboardWidget(

                    widget_id="milk.shift",

                    title="Current Shift",

                    value="--",

                    importance="HIGH",

                    zone="milk",

                ),

                DashboardWidget(

                    widget_id="milk.operator",

                    title="Latest Operator",

                    value="--",

                    importance="NORMAL",

                    zone="milk",

                ),

            ],

        )


    def _herd_zone(self):

        return DashboardZone(

            zone_id="herd",

            title="Herd",

            widgets=[

                DashboardWidget(

                    widget_id="herd.summary",

                    title="Herd Summary",

                    value="--",

                    importance="HIGH",

                    zone="herd",

                ),

                DashboardWidget(

                    widget_id="herd.lactating",

                    title="Lactating",

                    value="--",

                    importance="HIGH",

                    zone="herd",

                ),

                DashboardWidget(

                    widget_id="herd.attention",

                    title="Needs Attention",

                    value="--",

                    importance="CRITICAL",

                    zone="herd",

                ),

            ],

        )


    def _health_zone(self):

        return DashboardZone(

            zone_id="health",

            title="Health",

            widgets=[

                DashboardWidget(

                    widget_id="health.alerts",

                    title="Health Alerts",

                    value="--",

                    importance="CRITICAL",

                    zone="health",

                ),

                DashboardWidget(

                    widget_id="health.treatments",

                    title="Treatments",

                    value="--",

                    importance="HIGH",

                    zone="health",

                ),

                DashboardWidget(

                    widget_id="health.vaccinations",

                    title="Vaccinations",

                    value="--",

                    importance="NORMAL",

                    zone="health",

                ),

            ],

        )


    def _finance_zone(self):

        return DashboardZone(

            zone_id="finance",

            title="Finance",

            widgets=[

                DashboardWidget(

                    widget_id="finance.cash",

                    title="Cash Position",

                    value="--",

                    importance="CRITICAL",

                    zone="finance",

                ),

                DashboardWidget(

                    widget_id="finance.revenue",

                    title="Revenue",

                    value="--",

                    importance="HIGH",

                    zone="finance",

                ),

                DashboardWidget(

                    widget_id="finance.expenses",

                    title="Expenses",

                    value="--",

                    importance="HIGH",

                    zone="finance",

                ),

            ],

        )


    def _analytics_zone(self):

        return DashboardZone(

            zone_id="analytics",

            title="Analytics",

            widgets=[

                DashboardWidget(

                    widget_id="analytics.production",

                    title="Production",

                    value="--",

                    importance="NORMAL",

                    zone="analytics",

                ),

                DashboardWidget(

                    widget_id="analytics.feed",

                    title="Feed Efficiency",

                    value="--",

                    importance="NORMAL",

                    zone="analytics",

                ),

                DashboardWidget(

                    widget_id="analytics.kpis",

                    title="KPIs",

                    value="--",

                    importance="NORMAL",

                    zone="analytics",

                ),

            ],

        )


    def _alerts_zone(self):

        return DashboardZone(

            zone_id="alerts",

            title="Alerts",

            widgets=[

                DashboardWidget(

                    widget_id="alerts.critical",

                    title="Critical Alerts",

                    value="--",

                    importance="CRITICAL",

                    zone="alerts",

                ),

                DashboardWidget(

                    widget_id="alerts.reminders",

                    title="Reminders",

                    value="--",

                    importance="HIGH",

                    zone="alerts",

                ),

                DashboardWidget(

                    widget_id="alerts.system",

                    title="System",

                    value="--",

                    importance="NORMAL",

                    zone="alerts",

                ),

            ],

        )

