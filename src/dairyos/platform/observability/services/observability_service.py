from dairyos.platform.observability.models.metric import Metric
from dairyos.platform.observability.models.health_indicator import HealthIndicator
from dairyos.platform.observability.models.platform_event import PlatformEvent


class ObservabilityService:

    def __init__(self):
        self.metrics = []
        self.health = []
        self.events = []

    def record_metric(self, metric: Metric):
        self.metrics.append(metric)
        return metric

    def record_health(self, indicator: HealthIndicator):
        self.health.append(indicator)
        return indicator

    def publish_event(self, event: PlatformEvent):
        self.events.append(event)
        return event

    def summary(self):
        return {
            "metrics": len(self.metrics),
            "health_checks": len(self.health),
            "events": len(self.events),
        }
