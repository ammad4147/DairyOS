from fastapi import FastAPI

from fastapi.testclient import TestClient


from dairyos.api.knowledge.router import (
    router,
)



app = FastAPI()


app.include_router(router)



client = TestClient(app)




def test_entity_endpoint():


    response = client.get(

        "/knowledge/entity/cow102"

    )


    assert response.status_code == 200


    assert (

        response.json()["entity_id"]

        ==

        "cow102"

    )




def test_reason_endpoint():


    response = client.post(

        "/knowledge/reason",

        json={

            "observation":

                "milk decline"

        }

    )


    assert response.status_code == 200


    assert (

        response.json()["observation"]

        ==

        "milk decline"

    )

