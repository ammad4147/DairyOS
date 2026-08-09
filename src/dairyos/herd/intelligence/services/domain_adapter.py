from ..models.domain_snapshot import DomainSnapshot



class DomainIntelligenceAdapter:



    def collect(

        self,

        health_service,

        production_service,

        nutrition_service,

        reproduction_service,

        finance_service

    ):


        return DomainSnapshot(

            health_events=health_service.health_event_count(),

            vaccinations=health_service.vaccination_count(),

            milk_records=production_service.milk_record_count(),

            production_groups=production_service.group_count(),

            feed_plans=nutrition_service.feed_plan_count(),

            consumptions=nutrition_service.consumption_count(),

            pregnancies=reproduction_service.pregnancy_count(),

            costs=finance_service.cost_count(),

            revenues=finance_service.revenue_count()

        )
