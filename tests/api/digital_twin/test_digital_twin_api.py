from fastapi.testclient import TestClient


from fastapi import FastAPI


from dairyos.api.digital_twin.router import (
    router,
)



app = FastAPI()


app.include_router(router)



client = TestClient(app)



def test_state_endpoint():


    response = client.get(

        "/digital-twin/state"

    )


    assert response.status_code == 200


    assert response.json()["farm_id"] == "farm001"




def test_simulation_endpoint():


    response = client.post(

        "/digital-twin/simulate",

        json={

            "farm_id":"farm001",

            "metric":"feed_cost",

            "current_value":100000,

            "change_percent":15

        }

    )


    assert response.status_code == 200


    assert response.json()["change"] == 15

