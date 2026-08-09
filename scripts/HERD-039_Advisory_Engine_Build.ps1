$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-039 Advisory Engine Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class Advisory:


    category: str

    situation: str

    supporting_knowledge: str

    confidence: int

    recommended_action: str
'@ | Set-Content `
"dairyos\herd\dashboard\models\advisory.py"



@'
from ..models.advisory import Advisory



class AdvisoryService:



    def generate(

        self,

        category,

        situation,

        knowledge=None

    ):


        if knowledge:

            confidence = knowledge.confidence

            supporting = knowledge.observation

        else:

            confidence = 50

            supporting = "No historical knowledge available"



        actions = {

            "HERD STRATEGY":

                "Begin replacement acquisition planning",

            "HEALTH":

                "Review animal health intervention",

            "REPRODUCTION":

                "Review breeding performance",

            "PRODUCTION":

                "Review production performance",

            "FINANCE":

                "Review financial indicators"

        }



        action = actions.get(

            category,

            "Review farm condition"

        )



        return Advisory(

            category,

            situation,

            supporting,

            confidence,

            action

        )



    def compare_confidence(

        self,

        advisory_a,

        advisory_b

    ):


        return (

            advisory_a

            if advisory_a.confidence >= advisory_b.confidence

            else advisory_b

        )
'@ | Set-Content `
"dairyos\herd\dashboard\services\advisory_service.py"



@'
from dairyos.herd.dashboard.services.advisory_service import AdvisoryService

from dairyos.herd.dashboard.models.knowledge_entry import KnowledgeEntry



def test_advisory_creation():

    advisory = AdvisoryService().generate(

        "HERD STRATEGY",

        "Replacement shortage"

    )

    assert advisory.category == "HERD STRATEGY"



def test_default_confidence():

    advisory = AdvisoryService().generate(

        "HEALTH",

        "Health issue"

    )

    assert advisory.confidence == 50



def test_knowledge_based_advice():

    knowledge = KnowledgeEntry(

        "KB001",

        "HERD STRATEGY",

        "Early replacement planning improved stability",

        "History",

        85,

        "Planning"

    )


    advisory = AdvisoryService().generate(

        "HERD STRATEGY",

        "Replacement shortage",

        knowledge

    )


    assert advisory.confidence == 85



def test_supporting_knowledge():

    knowledge = KnowledgeEntry(

        "KB002",

        "HEALTH",

        "Vaccination reduced disease",

        "History",

        90,

        "Health"

    )


    advisory = AdvisoryService().generate(

        "HEALTH",

        "Disease risk",

        knowledge

    )


    assert "Vaccination" in advisory.supporting_knowledge



def test_replacement_action():

    advisory = AdvisoryService().generate(

        "HERD STRATEGY",

        "Issue"

    )


    assert advisory.recommended_action == "Begin replacement acquisition planning"



def test_health_action():

    advisory = AdvisoryService().generate(

        "HEALTH",

        "Issue"

    )


    assert advisory.recommended_action == "Review animal health intervention"



def test_production_action():

    advisory = AdvisoryService().generate(

        "PRODUCTION",

        "Issue"

    )


    assert advisory.recommended_action == "Review production performance"



def test_finance_action():

    advisory = AdvisoryService().generate(

        "FINANCE",

        "Issue"

    )


    assert advisory.recommended_action == "Review financial indicators"



def test_compare_confidence():

    service = AdvisoryService()


    low = service.generate(

        "HEALTH",

        "Issue"

    )


    high = AdvisoryService().generate(

        "HEALTH",

        "Issue",

        KnowledgeEntry(

            "KB003",

            "HEALTH",

            "Known pattern",

            "History",

            90,

            "Use"

        )

    )


    assert service.compare_confidence(high, low) == high



def test_advisory_model():

    advisory = AdvisoryService().generate(

        "REPRODUCTION",

        "Open cows"

    )


    assert advisory.situation == "Open cows"
'@ | Set-Content `
"tests\core\test_advisory_engine.py"



Write-Host "HERD-039 Advisory Engine Build Complete"