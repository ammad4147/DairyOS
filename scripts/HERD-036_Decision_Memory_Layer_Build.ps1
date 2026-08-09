$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-036 Decision Memory Layer Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class DecisionMemory:


    decision_id: str

    category: str

    decision: str

    reason: str

    priority: str

    owner: str

    status: str

    outcome: str
'@ | Set-Content `
"dairyos\herd\dashboard\models\decision_memory.py"



@'
from ..models.decision_memory import DecisionMemory



class DecisionMemoryService:



    def __init__(self):

        self.memory = []



    def record(

        self,

        decision_id,

        category,

        decision,

        reason,

        priority,

        owner,

        status="PENDING",

        outcome=""

    ):


        item = DecisionMemory(

            decision_id,

            category,

            decision,

            reason,

            priority,

            owner,

            status,

            outcome

        )


        self.memory.append(item)


        return item



    def get_all(self):

        return self.memory



    def find_by_category(

        self,

        category

    ):


        return [

            item

            for item in self.memory

            if item.category == category

        ]



    def completed_decisions(self):

        return [

            item

            for item in self.memory

            if item.status == "COMPLETED"

        ]
'@ | Set-Content `
"dairyos\herd\dashboard\services\decision_memory_service.py"



@'
from dairyos.herd.dashboard.services.decision_memory_service import DecisionMemoryService



def create_memory():

    return DecisionMemoryService()



def test_decision_record_creation():

    service = create_memory()

    record = service.record(

        "DM001",

        "HERD STRATEGY",

        "Purchase replacement heifers",

        "Replacement shortage",

        "HIGH",

        "OWNER"

    )

    assert record.decision == "Purchase replacement heifers"



def test_memory_storage():

    service = create_memory()

    service.record(

        "DM001",

        "HEALTH",

        "Vaccination",

        "Disease prevention",

        "MEDIUM",

        "MANAGER"

    )

    assert len(service.get_all()) == 1



def test_category_search():

    service = create_memory()

    service.record(

        "DM001",

        "HEALTH",

        "Treatment",

        "Issue",

        "HIGH",

        "OWNER"

    )

    assert len(service.find_by_category("HEALTH")) == 1



def test_completed_filter():

    service = create_memory()

    service.record(

        "DM001",

        "PRODUCTION",

        "Feed adjustment",

        "Milk drop",

        "MEDIUM",

        "MANAGER",

        "COMPLETED",

        "Production improved"

    )

    assert len(service.completed_decisions()) == 1



def test_outcome_tracking():

    service = create_memory()

    record = service.record(

        "DM002",

        "HERD STRATEGY",

        "Animal purchase",

        "Replacement need",

        "HIGH",

        "OWNER",

        "COMPLETED",

        "Herd stabilized"

    )

    assert record.outcome == "Herd stabilized"



def test_owner_tracking():

    service = create_memory()

    record = service.record(

        "DM003",

        "FINANCE",

        "Approve budget",

        "Cash planning",

        "HIGH",

        "OWNER"

    )

    assert record.owner == "OWNER"



def test_pending_status():

    service = create_memory()

    record = service.record(

        "DM004",

        "HEALTH",

        "Review alerts",

        "Health issue",

        "HIGH",

        "MANAGER"

    )

    assert record.status == "PENDING"



def test_multiple_records():

    service = create_memory()

    service.record(

        "DM001",

        "HEALTH",

        "A",

        "B",

        "LOW",

        "MANAGER"

    )

    service.record(

        "DM002",

        "FINANCE",

        "C",

        "D",

        "HIGH",

        "OWNER"

    )

    assert len(service.get_all()) == 2



def test_memory_history():

    service = create_memory()

    service.record(

        "DM005",

        "REPRODUCTION",

        "Breeding review",

        "Open cows",

        "HIGH",

        "OWNER",

        "COMPLETED",

        "Improved conception"

    )

    history = service.get_all()

    assert history[0].category == "REPRODUCTION"



def test_memory_model():

    service = create_memory()

    record = service.record(

        "DM006",

        "PRODUCTION",

        "Milk review",

        "Decline",

        "MEDIUM",

        "MANAGER"

    )

    assert record.decision_id == "DM006"
'@ | Set-Content `
"tests\core\test_decision_memory.py"



Write-Host "HERD-036 Decision Memory Layer Build Complete"