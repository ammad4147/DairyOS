from dairyos.farm.command_center.models.attention_item import AttentionItem


class AttentionQueueService:
    """Build a unique queue of current, actionable operational conditions."""

    _SEVERITY_PRIORITY = {
        "CRITICAL": "CRITICAL",
        "SEVERE": "HIGH",
        "HIGH": "HIGH",
        "ELEVATED": "MEDIUM",
        "WARNING": "MEDIUM",
        "MEDIUM": "MEDIUM",
        "LOW": "LOW",
        "NORMAL": "NORMAL",
        "INFO": "NORMAL",
    }

    def __init__(self, *, missing_input_detection_service=None):
        self.missing_input_detection_service = missing_input_detection_service

    def build(self, *, farm_state):
        """Return one attention item per current condition, not per history row."""
        items = []
        seen = set()

        current_health = getattr(farm_state, "health_state", {}) or {}
        if current_health:
            health_records = current_health.values()
        else:
            latest = {}
            for record in getattr(farm_state, "health_alerts", []) or []:
                key = record.get("animal_id") or "__farm__"
                previous = latest.get(key)
                if previous is None or str(record.get("timestamp")) > str(previous.get("timestamp")):
                    latest[key] = record
            health_records = latest.values()

        for alert in health_records:
            severity = str(alert.get("severity", "NORMAL")).upper()
            observation = str(alert.get("observation", "Health observation")).strip() or "Health observation"
            animal_id = alert.get("animal_id")
            priority = self._SEVERITY_PRIORITY.get(severity, "MEDIUM")
            action_required = priority != "NORMAL"

            key = self._condition_key("HEALTH", animal_id, observation)
            if key in seen:
                continue
            seen.add(key)

            if not action_required:
                continue

            items.append(
                AttentionItem(
                    priority=priority,
                    area="HEALTH",
                    message=observation,
                    action_required=True,
                    animal_id=animal_id,
                )
            )

        if self.missing_input_detection_service:
            gaps = self.missing_input_detection_service.detect(farm_state)
            for gap in gaps:
                key = self._condition_key(gap.area, None, gap.message)
                if key in seen:
                    continue
                seen.add(key)
                items.append(
                    AttentionItem(
                        priority=str(gap.severity).upper(),
                        area=gap.area,
                        message=gap.message,
                        action_required=True,
                    )
                )

        return items

    @staticmethod
    def _condition_key(area, animal_id, message):
        return (
            str(area or "").upper(),
            str(animal_id or "").strip().upper(),
            " ".join(str(message or "").strip().lower().split()),
        )
