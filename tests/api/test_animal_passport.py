from datetime import date, datetime, timedelta, timezone
import uuid

from dairyos.app import container
from dairyos.data.database.models.breeding_record_model import BreedingRecordModel
from dairyos.data.models.health_case import HealthCase
from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.treatment_record import TreatmentRecord


def _register_animal(client, *, animal_type="COW", dam_id=None, sire_id=None):
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": animal_type,
            "breed": "Holstein",
            "sex": "FEMALE" if animal_type != "BULL" else "MALE",
            "lifecycle_status": "LACTATING" if animal_type == "COW" else animal_type,
            "is_currently_milking": animal_type == "COW",
            "milking_frequency": "THRICE_DAILY" if animal_type == "COW" else None,
            "ear_tag": f"BIO-{uuid.uuid4().hex[:10].upper()}",
            "dam_id": dam_id,
            "sire_id": sire_id,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["animal_id"]


def _add_breeding_event(animal_id, event_type, when, result="positive"):
    session = container.repository_factory.session
    session.add(
        BreedingRecordModel(
            record_id=str(uuid.uuid4()),
            animal_id=animal_id,
            event_type=event_type,
            result=result,
            technician="Passport Test",
            timestamp=datetime.combine(
                when,
                datetime.min.time(),
                tzinfo=timezone.utc,
            ),
        )
    )
    session.commit()


def test_lifetime_animal_passport_aggregates_persisted_history(
    client,
    registered_animal,
):
    milk = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 8.0,
            "milking_session": "MORNING",
            "operator": "Milking Operator",
        },
    )

    assert milk.status_code == 200, milk.text

    passport = client.get(
        f"/farm/animals/{registered_animal}/passport"
    )

    assert passport.status_code == 200, passport.text

    data = passport.json()

    assert data["animal"]["animal_id"] == registered_animal
    assert data["history"]["milk"]

    milk_record = data["history"]["milk"][0]
    assert milk_record["animal_id"] == registered_animal
    assert milk_record["milking_session"] == "MORNING"
    assert milk_record["total_yield"] == 8.0

    assert data["record_counts"]["milk"] >= 1
    assert any(item["domain"] == "milk" for item in data["timeline"])


def test_lifetime_animal_passport_exposes_recursive_lineage(
    client,
):
    dam = _register_animal(client)
    daughter = _register_animal(client, animal_type="HEIFER", dam_id=dam)
    granddaughter = _register_animal(client, animal_type="CALF", dam_id=daughter)

    passport = client.get(
        f"/farm/animals/{dam}/passport"
    )

    assert passport.status_code == 200, passport.text
    data = passport.json()

    descendants = data["lineage"]["descendants"]
    descendant_ids = {item["animal_id"] for item in descendants}

    assert daughter in descendant_ids
    assert granddaughter in descendant_ids

    granddaughter_row = next(
        item for item in descendants if item["animal_id"] == granddaughter
    )
    assert granddaughter_row["depth"] == 2

    descendant_history = data["history"]["lineage_descendants"]
    assert any(
        item["animal_id"] == granddaughter and item["depth"] == 2
        for item in descendant_history
    )


def test_lifetime_animal_passport_tracks_lifetime_production_and_lactations(
    client,
    registered_animal,
):
    today = date.today()
    first_calving = today - timedelta(days=120)
    second_calving = today - timedelta(days=40)

    _add_breeding_event(registered_animal, "calving", first_calving, "calved")
    _add_breeding_event(registered_animal, "calving", second_calving, "calved")

    session = container.repository_factory.session
    for production_date, litres in (
        (today - timedelta(days=100), 20.0),
        (today - timedelta(days=90), 25.0),
        (today - timedelta(days=30), 30.0),
        (today - timedelta(days=10), 35.0),
    ):
        session.add(
            MilkProduction(
                animal_id=registered_animal,
                production_date=datetime.combine(production_date, datetime.min.time()),
                recorded_at=datetime.combine(production_date, datetime.min.time()),
                milking_session="MORNING",
                session_ledger=False,
                morning_yield=litres,
                total_yield=litres,
            )
        )
    session.commit()

    passport = client.get(
        f"/farm/animals/{registered_animal}/passport"
    )

    assert passport.status_code == 200, passport.text
    data = passport.json()

    lifetime = data["production"]["lifetime"]
    assert lifetime["lactation_count"] == 2
    assert lifetime["lifetime_milk_liters"] == 110.0
    assert lifetime["peak_daily_yield_liters"] == 35.0

    lactations = data["production"]["lactations"]
    assert len(lactations) == 2
    assert lactations[0]["lactation_number"] == 1
    assert lactations[0]["milk_liters"] == 45.0
    assert lactations[0]["status"] == "COMPLETED"
    assert lactations[1]["lactation_number"] == 2
    assert lactations[1]["milk_liters"] == 65.0
    assert lactations[1]["status"] == "CURRENT"

    biological = data["biological_summary"]
    assert biological["lifetime_milk_liters"] == 110.0
    assert biological["lactation_count"] == 2
    assert biological["lifetime_calvings"] == 2


def test_lifetime_animal_passport_exposes_reproductive_lifecycle_state(
    client,
    registered_animal,
):
    today = date.today()
    _add_breeding_event(
        registered_animal,
        "insemination",
        today - timedelta(days=25),
        "bred",
    )
    _add_breeding_event(
        registered_animal,
        "pregnancy_confirmed",
        today - timedelta(days=10),
        "positive",
    )

    passport = client.get(
        f"/farm/animals/{registered_animal}/passport"
    )

    assert passport.status_code == 200, passport.text
    current = passport.json()["reproduction"]["current"]

    assert current["current_api_status"] == "PREGNANT"
    assert current["pregnancy_status"] == "PREGNANT"
    assert "lifetime_heat_events" not in current
    assert current["lifetime_inseminations"] == 1
    assert current["pregnancy_confirmations"] == 1

    events = passport.json()["reproduction"]["lifetime_events"]
    assert [event["event_type"] for event in events] == [
        "PREGNANCY_CONFIRMED",
        "INSEMINATION",
    ]


def test_lifetime_animal_passport_exposes_current_health_case_and_withdrawal(
    client,
    registered_animal,
):
    today = date.today()
    persisted_date = today - timedelta(days=2)
    session = container.repository_factory.session

    case = HealthCase(
        case_id=f"HL-{today.strftime('%y%m%d')}-999",
        animal_id=registered_animal,
        severity="HIGH",
        diagnosis="Mastitis",
        status="OPEN",
        opened_at=datetime.combine(persisted_date, datetime.min.time()),
    )
    session.add(case)
    session.flush()

    withdrawal_until = datetime.combine(
        today + timedelta(days=5),
        datetime.min.time(),
    )
    session.add(
        TreatmentRecord(
            animal_id=registered_animal,
            diagnosis="Mastitis",
            medicine="Test Medicine",
            treated_by="Vet",
            treated_at=datetime.combine(persisted_date, datetime.min.time()),
            milk_withdrawal_days=5,
            milk_withdrawal_until=withdrawal_until,
            withdrawal_source="reference_table",
            health_case_id=case.id,
        )
    )
    session.commit()

    passport = client.get(
        f"/farm/animals/{registered_animal}/passport"
    )

    assert passport.status_code == 200, passport.text
    data = passport.json()

    health_state = data["health_state"]
    assert health_state["summary"]["open_case_count"] == 1
    assert health_state["summary"]["active_withdrawal"] is True
    assert health_state["open_cases"][0]["case_id"] == case.case_id
    assert health_state["active_withdrawals"]
    assert health_state["active_withdrawals"][0]["withdrawal_until"] == (
        today + timedelta(days=5)
    ).isoformat()


def test_lifetime_animal_passport_supports_historical_cutoff(
    client,
    registered_animal,
):
    today = date.today()
    past = today - timedelta(days=10)
    future = today + timedelta(days=2)

    session = container.repository_factory.session
    for when, litres in ((past, 12.0), (future, 22.0)):
        session.add(
            MilkProduction(
                animal_id=registered_animal,
                production_date=datetime.combine(when, datetime.min.time()),
                recorded_at=datetime.combine(when, datetime.min.time()),
                milking_session="MORNING",
                session_ledger=False,
                morning_yield=litres,
                total_yield=litres,
            )
        )
    session.commit()

    passport = client.get(
        f"/farm/animals/{registered_animal}/passport",
        params={"as_of_date": today.isoformat()},
    )

    assert passport.status_code == 200, passport.text
    data = passport.json()
    assert data["date_context"]["mode"] == "HISTORICAL_STATE"
    assert data["production"]["lifetime"]["lifetime_milk_liters"] == 12.0


def test_lifetime_animal_passport_returns_404_for_unknown_animal(
    client,
):
    response = client.get(
        "/farm/animals/AN-DOES-NOT-EXIST/passport"
    )

    assert response.status_code == 404
