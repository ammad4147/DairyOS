$root = "C:\DairyOS"

Write-Host "Starting HERD-018 Herd Intelligence Decision Engine Build..." -ForegroundColor Cyan


# Update HerdDecision model

@'
from dataclasses import dataclass



@dataclass
class HerdDecision:


    risk_level: str

    attention_required: bool

    recommendations: list

    priority_level: str = "NORMAL"

    decision_score: int = 0
'@ | Set-Content `
"$root\dairyos\herd\intelligence\models\herd_decision.py"



# Update Decision Service

@'
from dairyos.herd.intelligence.models.herd_decision import HerdDecision



class DecisionService:



    def evaluate(

        self,

        open_cows=0,

        health_alerts=0,

        replacement_shortage=False

    ):


        recommendations = []

        risk = "LOW"

        attention = False


        if health_alerts > 0:

            attention = True

            recommendations.append(

                "Review animal health alerts"

            )


        if open_cows > 3:

            attention = True

            recommendations.append(

                "Review reproductive performance"

            )


        if replacement_shortage:

            risk = "HIGH"

            attention = True

            recommendations.append(

                "Replacement pipeline shortage detected"

            )


        elif attention:

            risk = "MEDIUM"



        return HerdDecision(

            risk_level=risk,

            attention_required=attention,

            recommendations=recommendations

        )



    def evaluate_context(

        self,

        context

    ):


        score = 0

        recommendations = []



        if getattr(context, "health_alerts", 0) > 0:

            score += 20

            recommendations.append(

                "Review animal health alerts"

            )



        if getattr(context, "open_cows", 0) > 3:

            score += 15

            recommendations.append(

                "Review reproductive performance"

            )



        if getattr(context, "replacement_shortage", False):

            score += 40

            recommendations.append(

                "Review replacement pipeline"

            )



        if getattr(context, "production_status", "") == "INACTIVE":

            score += 15

            recommendations.append(

                "Review milk production activity"

            )



        if getattr(context, "financial_status", "") == "WARNING":

            score += 10

            recommendations.append(

                "Review financial position"

            )



        if score >= 51:

            risk = "HIGH"

            priority = "URGENT"


        elif score >= 21:

            risk = "MEDIUM"

            priority = "HIGH"


        else:

            risk = "LOW"

            priority = "NORMAL"



        return HerdDecision(

            risk_level=risk,

            attention_required=(score > 0),

            recommendations=recommendations,

            priority_level=priority,

            decision_score=score

        )
'@ | Set-Content `
"$root\dairyos\herd\intelligence\services\decision_service.py"



# HERD-018 tests

@'
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
'@ | Set-Content `
"$root\tests\core\test_herd_decision_engine.py"



Write-Host ""
Write-Host "HERD-018 Build Completed Successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Run validation:"
Write-Host "pytest tests/core/test_herd_decision_engine.py -v"
Write-Host "pytest -q"