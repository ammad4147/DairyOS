from ..models.operational_health_snapshot import OperationalHealthSnapshot


class OperationsHealthService:
    """Compute a truthful operational health score from current state and active signals."""

    def generate_snapshot(
        self,
        operational_score=None,
        active_decisions=0,
        pending_actions=0,
        tracked_outcomes=0,
        learning_signals=0,
        *,
        operational_state=None,
        attention_items=None,
        decisions=None,
    ):
        attention_items = list(attention_items or [])
        decisions = list(decisions or [])

        if operational_score is None:
            operational_score = self.calculate_score(
                attention_items=attention_items,
                decisions=decisions,
            )
        else:
            operational_score = float(operational_score)

        operational_score = max(0.0, min(100.0, operational_score))

        priorities = [
            str(item.get("priority", "NORMAL")).upper()
            if isinstance(item, dict)
            else str(getattr(item, "priority", "NORMAL")).upper()
            for item in attention_items
        ]
        priorities.extend(
            str(item.get("priority", "NORMAL")).upper()
            for item in decisions
            if isinstance(item, dict)
        )

        if "CRITICAL" in priorities:
            status = "RED"
            attention = True
        elif any(priority in {"HIGH", "MEDIUM", "ELEVATED"} for priority in priorities):
            status = "AMBER"
            attention = True
        else:
            status = "GREEN"
            attention = False

        return OperationalHealthSnapshot(
            health_status=status,
            operational_score=operational_score,
            active_decisions=active_decisions,
            pending_actions=pending_actions,
            tracked_outcomes=tracked_outcomes,
            learning_signals=learning_signals,
            owner_attention_required=attention,
        )

    def calculate_score(self, *, attention_items=None, decisions=None):
        """Score active operational conditions; never default to 100."""
        score = 100.0
        seen = set()

        def apply_penalty(priority, key):
            nonlocal score
            if key in seen:
                return
            seen.add(key)
            penalty = {
                "CRITICAL": 35.0,
                "HIGH": 20.0,
                "ELEVATED": 20.0,
                "MEDIUM": 10.0,
                "WARNING": 10.0,
                "LOW": 5.0,
                "NORMAL": 0.0,
            }.get(str(priority).upper(), 5.0)
            score -= penalty

        for item in attention_items or []:
            if isinstance(item, dict):
                priority = item.get("priority", "NORMAL")
                key = (item.get("area"), item.get("animal_id"), item.get("message"))
            else:
                priority = getattr(item, "priority", "NORMAL")
                key = (getattr(item, "area", None), getattr(item, "animal_id", None), getattr(item, "message", None))
            apply_penalty(priority, key)

        represented = {
            (str(item.get("area", "")).upper(), str(item.get("animal_id", "")))
            for item in attention_items
            if isinstance(item, dict)
        }

        for decision in decisions or []:
            if not isinstance(decision, dict):
                continue
            area = {
                "health": "HEALTH",
                "production": "MILK",
                "feeding": "FEEDING",
                "workforce": "WORKFORCE",
            }.get(str(decision.get("type", "")).lower(), "")
            animal_id = str(decision.get("animal_id", ""))
            if area and (area, animal_id) in represented:
                continue
            key = (
                "DECISION",
                decision.get("type"),
                decision.get("action"),
                decision.get("animal_id"),
                str(decision.get("details")),
            )
            apply_penalty(decision.get("priority", "NORMAL"), key)

        return round(max(0.0, min(100.0, score)), 1)
