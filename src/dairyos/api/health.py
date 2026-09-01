from datetime import date, datetime
from fastapi import APIRouter, Depends
from dairyos.api.dependencies import get_container
from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority

router = APIRouter(tags=["Health"])

def _as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None

@router.get("/health")
def health():
    return {"system":"DairyOS","status":"healthy","runtime":"active"}

@router.get("/farm/health/summary")
def get_health_summary(container=Depends(get_container)):
    factory=container.repository_factory
    today=OperationalDateAuthority(repository_factory=factory).current_date()
    cases=factory.health_cases().get_all()
    active=[c for c in cases if str(getattr(c,"status","") or "").upper()!="RESOLVED"]
    active_animals={str(getattr(c,"animal_id","")) for c in active if getattr(c,"animal_id",None)}
    treatments=factory.treatment().get_all()
    withdrawal_count=sum(1 for r in treatments if str(getattr(r,"animal_id","")) in active_animals and float(getattr(r,"milk_withdrawal_days",0) or 0)>0)
    completed=0; due=0; upcoming=[]
    for event in container.event_journal.all_events():
        if event.name!="OperationalInputReceived": continue
        payload=dict(event.payload or {})
        if str(payload.get("input_type") or "").lower()!="vaccination": continue
        if str(payload.get("status") or "COMPLETED").upper()=="VOID": continue
        completed+=1
        nd=_as_date(payload.get("next_due_date"))
        if nd is not None:
            if nd<=today: due+=1
            upcoming.append({"animal_id":payload.get("animal_id"),"vaccine":payload.get("vaccine") or payload.get("vaccination"),"next_due_date":nd.isoformat()})
    upcoming.sort(key=lambda x:x["next_due_date"])
    return {"activeClinicalCases":len(active),"withdrawalCount":withdrawal_count,"vaccinationsRecorded":completed,"vaccinationsDue":due,"upcomingVaccinations":upcoming[:25],"data_status":"LIVE_PERSISTED_DATA"}
