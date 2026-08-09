from fastapi import APIRouter

from dairyos.api.dependencies import get_container
from dairyos.domain.commands import Command


router = APIRouter(
    tags=["Command Center"],
)


@router.get("/command-center")
def command_center():

    container = get_container()

    operational_command_center = (
        container
        .operational_command_center_service
        .snapshot()
    )

    return (
        container
        .command_center_projection_service
        .build_view(
            operational_command_center=operational_command_center
        )
    )


@router.post("/animals")
def create_animal(payload: dict):

    container = get_container()

    container.operations.handle_command(
        Command(
            name="CreateAnimal",
            payload=payload,
        )
    )

    return {
        "status": "ok"
    }



@router.post("/milk")
def record_milk(payload: dict):

    container = get_container()

    container.operations.handle_command(
        Command(
            name="RecordMilk",
            payload=payload,
        )
    )

    return {
        "status": "ok"
    }



@router.post("/feed")
def feed_animal(payload: dict):

    container = get_container()

    container.operations.handle_command(
        Command(
            name="FeedAnimal",
            payload=payload,
        )
    )

    return {
        "status": "ok"
    }
