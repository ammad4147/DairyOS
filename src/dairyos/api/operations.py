from fastapi import APIRouter, Depends

from dairyos.api.dependencies import get_container


router = APIRouter(
    prefix="/operations",
    tags=["Operations"],
)



def get_state(container):

    return (
        container
        .farm_operational_state_service
        .get_state()
    )



def health_state(container):

    state = get_state(container)

    if state.exceptions:

        return "AMBER"

    return "GREEN"



def attention_count(container):

    return len(
        get_state(container).exceptions
    )



@router.get("/commands/status")
def command_status(
    container = Depends(get_container),
):

    attention = attention_count(container)

    return {

        "health_status":
            health_state(container),


        "runtime":
            "ACTIVE",


        "events":
            container.event_journal.count(),


        "active_attention_count":
            attention,


        "has_critical_attention":
            False,

    }



@router.get("/dashboard")
def operations_dashboard(
    container = Depends(get_container),
):

    state = get_state(container)

    issues = attention_count(container)


    return {

        "health":
            health_state(container),


        "farm_status":
            state.operational_status(),


        "milk_today":
            state.milk_total(),


        "feed_today":
            state.feed_total(),


        "total_events":
            container.event_journal.count(),


        "open_issues":
            issues,


        "resolution_rate":
            100.0
            if issues == 0
            else 0.0,


        "effectiveness_score":
            100.0
            if issues == 0
            else 80.0,

    }



@router.get("/executive")
def executive(
    container = Depends(get_container),
):

    state = get_state(container)

    attention = attention_count(container)


    return {

        "health_status":
            health_state(container),


        "operational_status":
            state.operational_status(),


        "management_attention_required":
            attention > 0,


        "owner_action_required":
            attention > 0,


        "attention_count":
            attention,


        "critical_issue_count":
            0,


        "recommended_focus":
            "Continue normal operations"
            if attention == 0
            else "Resolve active exceptions",


        "operational_priority_score":
            100.0
            if attention == 0
            else 70.0,


        "total_events":
            container.event_journal.count(),

    }



@router.get("/health")
def operations_health(
    container = Depends(get_container),
):

    attention = attention_count(container)

    return {

        "health_status":
            health_state(container),


        "operational_score":
            100.0
            if attention == 0
            else 80.0,


        "owner_attention_required":
            attention > 0,


        "runtime":
            "ACTIVE",

    }
