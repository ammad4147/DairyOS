from dairyos.platform.knowledge_graph.entities.animal_entity import (
    AnimalEntity,
)
from dairyos.platform.knowledge_graph.services.knowledge_service import (
    KnowledgeService,
)


def test_knowledge_entity_registration():


    service = KnowledgeService()



    animal = AnimalEntity(

        animal_id="cow102",

        name="Cow 102",

        breed="Holstein",

        status="lactating",

    )



    result = service.register_entity(

        "cow102",

        animal,

    )



    assert result.animal_id == "cow102"


    assert (

        service.graph.get_entity("cow102")

        == animal

    )

