from dairyos.platform.command_center.models.operational_summary import (
    OperationalSummary,
)



class CommandAggregator:
    """
    Enterprise operational command aggregation service.
    """



    def __init__(self):

        self.providers = {}



    def register_provider(
        self,
        domain: str,
        provider,
    ):

        self.providers[domain] = provider



    def collect(self):

        summaries = []


        for domain, provider in self.providers.items():

            data = provider.summary()


            summaries.append(

                OperationalSummary(

                    domain=domain,

                    status=data.get(
                        "status",
                        "unknown",
                    ),

                    metrics=data,

                )

            )


        return summaries



    def executive_view(self):

        results = self.collect()


        return {

            "platform": "DairyOS",

            "operational_status": "healthy",

            "domains": [

                {

                    "domain": item.domain,

                    "status": item.status,

                    "metrics": item.metrics,

                }

                for item in results

            ]

        }
