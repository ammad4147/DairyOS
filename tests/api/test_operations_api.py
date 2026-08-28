from dairyos.app import container


class FakeOperationalDecisionService:
    def __init__(self):
        self._decisions = [
            {
                "type": "production",
                "priority": "high",
                "action": "record_milk_activity",
                "title": "Complete milk production recording",
                "details": "Milk production has not been recorded.",
                "source": "missing_input",
                "escalation_level": "HIGH",
                "owner_action_required": True,
            }
        ]

    def evaluate(self):
        return list(self._decisions)

    def active_decisions(self):
        return self.evaluate()

    def count(self):
        return len(self._decisions)

    def priority_summary(self):
        summary = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "normal": 0,
            "low": 0,
            "warning": 0,
        }

        for decision in self._decisions:
            priority = str(
                decision.get(
                    "priority",
                    "normal",
                )
            ).lower()

            if priority in summary:
                summary[priority] += 1

        return summary


def test_operations_health_reflects_active_operational_decisions(
    client,
):
    original_service = container.operational_decision_service

    try:
        container.operational_decision_service = (
            FakeOperationalDecisionService()
        )

        response = client.get(
            "/operations/health"
        )

        assert response.status_code == 200

        body = response.json()

        assert body["health_status"] == "AMBER"
        assert body["operational_score"] == 80.0
        assert body["owner_attention_required"] is True
        assert body["runtime"] == "ACTIVE"

    finally:
        container.operational_decision_service = (
            original_service
        )


def test_operations_dashboard_counts_active_operational_decisions(
    client,
):
    original_service = container.operational_decision_service

    try:
        container.operational_decision_service = (
            FakeOperationalDecisionService()
        )

        response = client.get(
            "/operations/dashboard"
        )

        assert response.status_code == 200

        body = response.json()

        assert body["health"] == "AMBER"
        assert body["open_issues"] == 1
        assert body["effectiveness_score"] == 80.0

    finally:
        container.operational_decision_service = (
            original_service
        )


def test_operations_executive_reports_decision_driven_attention(
    client,
):
    original_service = container.operational_decision_service

    try:
        container.operational_decision_service = (
            FakeOperationalDecisionService()
        )

        response = client.get(
            "/operations/executive"
        )

        assert response.status_code == 200

        body = response.json()

        assert body["health_status"] == "AMBER"
        assert body["management_attention_required"] is True
        assert body["owner_action_required"] is True
        assert body["attention_count"] == 1
        assert body["critical_issue_count"] == 0
        assert (
            body["recommended_focus"]
            == "Resolve active operational decisions"
        )
        assert body["operational_priority_score"] == 80.0

    finally:
        container.operational_decision_service = (
            original_service
        )