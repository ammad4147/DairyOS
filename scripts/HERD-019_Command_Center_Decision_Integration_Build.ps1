$root = "C:\DairyOS"

Write-Host "Starting HERD-019 Command Center Decision Integration Build..." -ForegroundColor Cyan


# Extend HerdCommand model

@'
from dataclasses import dataclass, field



@dataclass
class HerdCommand:


    farm_name: str

    total_animals: int

    production_status: str

    health_status: str

    reproduction_status: str

    financial_status: str

    overall_risk: str

    owner_attention: str

    decision_priority: str = "NORMAL"

    decision_score: int = 0

    recommended_actions: list = field(default_factory=list)
'@ | Set-Content `
"$root\dairyos\herd\dashboard\models\herd_command.py"



# Create command decision adapter

@'
from ..models.herd_command import HerdCommand



class CommandDecisionService:



    def apply_decision(

        self,

        command,

        decision

    ):


        command.decision_priority = decision.priority_level

        command.decision_score = decision.decision_score

        command.recommended_actions = decision.recommendations


        if decision.attention_required:

            command.owner_attention = (

                decision.recommendations[0]

                if decision.recommendations

                else "Review herd status"

            )


        command.overall_risk = decision.risk_level


        return command
'@ | Set-Content `
"$root\dairyos\herd\dashboard\services\command_decision_service.py"



# Extend HerdCommandService

@'
from ..models.herd_command import HerdCommand



class HerdCommandService:



    def generate_from_context(self, context):


        return self.generate(

            farm_name=context.farm_name,

            total_animals=context.total_animals,

            health_alerts=context.health_alerts,

            open_cows=context.open_cows,

            replacement_shortage=context.replacement_shortage,

            production_status=context.production_status,

            financial_status=context.financial_status

        )



    def generate_from_decision(

        self,

        context,

        decision

    ):


        from .command_decision_service import CommandDecisionService


        command = self.generate_from_context(

            context

        )


        return CommandDecisionService().apply_decision(

            command,

            decision

        )



    def generate(

        self,

        farm_name,

        total_animals,

        health_alerts=0,

        open_cows=0,

        replacement_shortage=False,

        production_status="STABLE",

        financial_status="POSITIVE"

    ):


        health_status = "NORMAL"

        reproduction_status = "NORMAL"

        risk = "LOW"

        attention = "No immediate action required"



        if health_alerts > 0:

            health_status = "ATTENTION REQUIRED"

            risk = "MEDIUM"

            attention = "Review animal health alerts"



        if open_cows > 3:

            reproduction_status = "MONITOR"

            if risk == "LOW":

                risk = "MEDIUM"

                attention = "Review reproductive performance"



        if replacement_shortage:

            risk = "HIGH"

            attention = "Review replacement pipeline"



        return HerdCommand(

            farm_name=farm_name,

            total_animals=total_animals,

            production_status=production_status,

            health_status=health_status,

            reproduction_status=reproduction_status,

            financial_status=financial_status,

            overall_risk=risk,

            owner_attention=attention

        )
'@ | Set-Content `
"$root\dairyos\herd\dashboard\services\herd_command_service.py"



# Create HERD-019 tests

@'
from dairyos.herd.dashboard.models.herd_command import HerdCommand

from dairyos.herd.dashboard.services.command_decision_service import CommandDecisionService

from dairyos.herd.dashboard.services.herd_command_service import HerdCommandService

from dairyos.herd.intelligence.models.herd_decision import HerdDecision



class Context:


    farm_name = "Trident Dairies"

    total_animals = 100

    health_alerts = 2

    open_cows = 5

    replacement_shortage = True

    production_status = "ACTIVE"

    financial_status = "WARNING"



def test_command_decision_creation():

    command = HerdCommand(

        "Farm",

        10,

        "ACTIVE",

        "NORMAL",

        "NORMAL",

        "POSITIVE",

        "LOW",

        ""

    )

    assert command.decision_score == 0



def test_decision_bridge():

    command = HerdCommandService().generate(

        "Farm",

        10

    )


    decision = HerdDecision(

        "HIGH",

        True,

        ["Review health"],

        "URGENT",

        80

    )


    result = CommandDecisionService().apply_decision(

        command,

        decision

    )


    assert result.decision_score == 80



def test_high_priority_command():

    decision = HerdDecision(

        "HIGH",

        True,

        ["Action"],

        "URGENT",

        90

    )


    assert decision.priority_level == "URGENT"



def test_low_priority_command():

    decision = HerdDecision(

        "LOW",

        False,

        [],

        "NORMAL",

        0

    )


    assert decision.risk_level == "LOW"



def test_command_contains_actions():

    command = HerdCommandService().generate(

        "Farm",

        10

    )


    decision = HerdDecision(

        "MEDIUM",

        True,

        ["Check health"],

        "HIGH",

        30

    )


    result = CommandDecisionService().apply_decision(

        command,

        decision

    )


    assert len(result.recommended_actions) == 1



def test_command_score():

    decision = HerdDecision(

        "MEDIUM",

        True,

        [],

        "HIGH",

        30

    )


    assert decision.decision_score == 30



def test_context_to_command_flow():

    decision = HerdDecision(

        "HIGH",

        True,

        ["Review replacement"],

        "URGENT",

        70

    )


    command = HerdCommandService().generate_from_decision(

        Context(),

        decision

    )


    assert command.overall_risk == "HIGH"



def test_full_intelligence_to_dashboard_flow():

    decision = HerdDecision(

        "HIGH",

        True,

        ["Review herd"],

        "URGENT",

        100

    )


    command = HerdCommandService().generate_from_decision(

        Context(),

        decision

    )


    assert command.decision_priority == "URGENT"

    assert command.decision_score == 100
'@ | Set-Content `
"$root\tests\core\test_herd_command_decision.py"



Write-Host ""
Write-Host "HERD-019 Build Completed Successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Validation:"
Write-Host "pytest tests/core/test_herd_command_decision.py -v"
Write-Host "pytest -q"