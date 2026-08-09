from dairyos.herd.dashboard.services.knowledge_base_service import KnowledgeBaseService



def create_service():

    return KnowledgeBaseService()



def test_knowledge_creation():

    service = create_service()

    entry = service.add(

        "KB001",

        "HERD STRATEGY",

        "Early replacement planning improves stability",

        "Historical decisions",

        85,

        "Future herd planning"

    )

    assert entry.knowledge_id == "KB001"



def test_storage():

    service = create_service()

    service.add(

        "KB001",

        "HEALTH",

        "Vaccination reduced disease",

        "History",

        90,

        "Health planning"

    )

    assert len(service.get_all()) == 1



def test_search_category():

    service = create_service()

    service.add(

        "KB001",

        "REPRODUCTION",

        "Breeding review improves conception",

        "History",

        80,

        "Breeding"

    )

    assert len(service.search("REPRODUCTION")) == 1



def test_search_observation():

    service = create_service()

    service.add(

        "KB001",

        "HERD",

        "Replacement planning improved herd stability",

        "History",

        85,

        "Planning"

    )

    assert len(service.search("stability")) == 1



def test_confidence():

    service = create_service()

    service.add(

        "KB001",

        "A",

        "Observation",

        "History",

        80,

        "Use"

    )

    service.add(

        "KB002",

        "B",

        "Observation",

        "History",

        100,

        "Use"

    )

    assert service.average_confidence() == 90



def test_empty_confidence():

    assert create_service().average_confidence() == 0



def test_multiple_entries():

    service = create_service()

    service.add(

        "KB001",

        "A",

        "First",

        "History",

        80,

        "Use"

    )

    service.add(

        "KB002",

        "B",

        "Second",

        "History",

        90,

        "Use"

    )

    assert len(service.get_all()) == 2



def test_future_usage():

    service = create_service()

    entry = service.add(

        "KB003",

        "FINANCE",

        "Cash planning improves resilience",

        "History",

        75,

        "Future decisions"

    )

    assert entry.usage == "Future decisions"



def test_knowledge_retrieval():

    service = create_service()

    service.add(

        "KB004",

        "HERD STRATEGY",

        "Replacement planning is critical",

        "History",

        85,

        "Planning"

    )

    result = service.search("Replacement")

    assert result[0].confidence == 85



def test_model():

    entry = create_service().add(

        "KB005",

        "PRODUCTION",

        "Milk monitoring",

        "History",

        70,

        "Analysis"

    )

    assert entry.category == "PRODUCTION"
