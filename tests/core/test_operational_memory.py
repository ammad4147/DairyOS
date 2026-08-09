from dairyos.herd.dashboard.services.operational_memory_service import OperationalMemoryService



def test_memory_creation():

    record = OperationalMemoryService().record_intervention(

        "HEALTH",

        "Health alert",

        "Treatment review",

        outcome="Animal recovered"

    )

    assert record.category == "HEALTH"



def test_memory_storage():

    service = OperationalMemoryService()

    service.record_intervention(

        "REPRODUCTION",

        "Open cows",

        "Breeding review"

    )

    assert service.history_count() == 1



def test_history_retrieval():

    service = OperationalMemoryService()

    service.record_intervention(

        "FINANCE",

        "Cost increase",

        "Review expenses"

    )

    assert len(service.get_history()) == 1



def test_completed_filter():

    service = OperationalMemoryService()

    service.record_intervention(

        "HERD",

        "Replacement shortage",

        "Purchase animals"

    )

    assert len(service.completed_actions()) == 1



def test_memory_status():

    record = OperationalMemoryService().record_intervention(

        "PRODUCTION",

        "Milk reduction",

        "Review production"

    )

    assert record.status == "COMPLETED"



def test_memory_outcome():

    record = OperationalMemoryService().record_intervention(

        "HEALTH",

        "Disease event",

        "Treatment",

        outcome="Recovered"

    )

    assert record.outcome == "Recovered"



def test_memory_priority():

    record = OperationalMemoryService().record_intervention(

        "HERD",

        "Replacement issue",

        "Secure animals",

        priority="HIGH"

    )

    assert record.priority == "HIGH"



def test_multiple_history_records():

    service = OperationalMemoryService()

    service.record_intervention(

        "HEALTH",

        "Issue",

        "Action"

    )

    service.record_intervention(

        "FINANCE",

        "Issue",

        "Action"

    )

    assert service.history_count() == 2



def test_memory_action_trace():

    record = OperationalMemoryService().record_intervention(

        "REPRODUCTION",

        "Low conception",

        "Review breeding"

    )

    assert len(record.action) > 0



def test_memory_issue_trace():

    record = OperationalMemoryService().record_intervention(

        "PRODUCTION",

        "Milk drop",

        "Investigate"

    )

    assert len(record.issue) > 0
