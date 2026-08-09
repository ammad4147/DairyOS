from dairyos.herd.intelligence.models.herd_decision import HerdDecision

from dairyos.herd.intelligence.services.decision_service import DecisionService



class Context:


    def __init__(

        self,

        health_alerts=0,

        open_cows=0,

        replacement_shortage=False,

        production_status="STABLE",

        financial_status="POSITIVE"

    ):

        self.health_alerts = health_alerts

        self.open_cows = open_cows

        self.replacement_shortage = replacement_shortage

        self.production_status = production_status

        self.financial_status = financial_status



def test_decision_model_extension():

    decision = HerdDecision(

        "LOW",

        False,

        []

    )

    assert decision.priority_level == "NORMAL"



def test_context_decision_low_risk():

    decision = DecisionService().evaluate_context(

        Context()

    )

    assert decision.risk_level == "LOW"



def test_health_priority():

    decision = DecisionService().evaluate_context(

        Context(health_alerts=2)

    )

    assert decision.decision_score == 20



def test_finance_priority():

    decision = DecisionService().evaluate_context(

        Context(financial_status="WARNING")

    )

    assert "financial" in decision.recommendations[-1].lower()



def test_production_priority():

    decision = DecisionService().evaluate_context(

        Context(production_status="INACTIVE")

    )

    assert decision.decision_score == 15



def test_high_risk_score():

    decision = DecisionService().evaluate_context(

        Context(

            health_alerts=2,

            replacement_shortage=True

        )

    )

    assert decision.risk_level == "HIGH"

    assert decision.priority_level == "URGENT"



def test_low_risk_score():

    decision = DecisionService().evaluate_context(

        Context()

    )

    assert decision.decision_score == 0
