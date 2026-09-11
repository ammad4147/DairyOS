"""Forensic checks for AI Assistant live read-only evidence paths."""

import json
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from dairyos.api.dependencies import get_container
from dairyos.api.tmr import DAILY_COST_SNAPSHOT_GROUP
from dairyos.assistant.operational import (
    _with_read_only,
    read_cop_metrics,
    read_database_schema,
    read_health_insight,
    read_operational_data,
    read_operational_logs,
)
from dairyos.data.database.models.breeding_record_model import BreedingRecordModel
from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.models.feed_ration import FeedRation
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.feed_record import FeedRecord
from dairyos.data.models.health_observation import HealthObservation
from dairyos.data.models.milk_disposition import MilkDisposition
from dairyos.data.models.milk_production import MilkProduction
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)


def _seed_read_fixture(animal_id: str) -> None:
    session = get_container().repository_factory.session
    for day, litres, feed_cost, opex in (
        (date(2026, 9, 1), 100.0, 100.0, 10.0),
        (date(2026, 9, 2), 200.0, 200.0, 20.0),
        (date(2026, 9, 3), 50.0, 30.0, 0.0),
    ):
        session.add(
            MilkProduction(
                animal_id=animal_id,
                production_date=datetime.combine(day, datetime.min.time()),
                recorded_at=datetime.combine(day, datetime.min.time()),
                total_yield=litres,
                status="RECORDED",
            )
        )
        session.add(
            FeedRation(
                name=f"Forensic TMR {day.isoformat()}",
                animal_group=DAILY_COST_SNAPSHOT_GROUP,
                ingredients_json=json.dumps(
                    {
                        "kind": "TMR_DAILY_COST_SNAPSHOT",
                        "operational_date": day.isoformat(),
                        "total_herd_feed_cost_per_day": feed_cost,
                    }
                ),
                effective_date=day.isoformat(),
                operator="FORENSIC_TEST",
            )
        )
        if opex:
            session.add(
                FinancialTransaction(
                    transaction_type="EXPENSE",
                    category="Grid Electricity (WAPDA)",
                    amount=opex,
                    transaction_date=datetime.combine(day, datetime.min.time()),
                    master_category="OPEX",
                    sub_category="Grid Electricity (WAPDA)",
                    cop_classification="OPEX",
                    cop_attribution_method="DIRECT",
                    cop_service_date=day,
                    status="RECORDED",
                )
            )

    session.add(
        BreedingRecordModel(
            record_id=f"CALVING-{uuid4().hex}",
            animal_id=animal_id,
            event_type="calving",
            result="LIVE",
            technician="FORENSIC_TEST",
            timestamp=datetime(2026, 9, 3, tzinfo=UTC),
        )
    )
    session.add(
        HealthObservation(
            animal_id=animal_id,
            observed_at=datetime(2026, 9, 3, tzinfo=UTC).replace(tzinfo=None),
            observation="fever and reduced appetite",
            symptom="fever",
            severity="ATTENTION",
            status="OPEN",
        )
    )
    session.add(
        EventJournalModel(
            event_id=f"MORTALITY-{uuid4().hex}",
            event_type="OperationalInputReceived",
            timestamp=datetime(2026, 9, 3, tzinfo=UTC).replace(tzinfo=None),
            payload={
                "input_type": "animal_disposition",
                "animal_id": animal_id,
                "disposition": "DECEASED",
                "effective_date": "2026-09-03",
                "cause": "forensic test only",
            },
        )
    )
    session.add(
        EventJournalModel(
            event_id=f"VACCINATION-{uuid4().hex}",
            event_type="OperationalInputReceived",
            timestamp=datetime(2026, 9, 2, tzinfo=UTC).replace(tzinfo=None),
            payload={
                "input_type": "vaccination",
                "animal_id": animal_id,
                "vaccine": "Forensic test vaccine",
                "administered_date": "2026-09-02",
                "next_due_date": "2027-09-02",
                "status": "COMPLETED",
            },
        )
    )
    session.add(
        MilkDisposition(
            production_date=date(2026, 9, 2),
            disposition_type="SOLD",
            quantity_litres=120.0,
            sale_id=f"FORENSIC-SALE-{uuid4().hex}",
            counterparty="Forensic test buyer",
            selling_price_per_litre=2.5,
            amount_due=300.0,
            amount_received=200.0,
            recorded_by="FORENSIC_TEST",
            status="RECORDED",
        )
    )
    session.add(
        FinancialTransaction(
            transaction_type="EXPENSE",
            category="Forensic voided expense",
            amount=999.0,
            transaction_date=datetime(2026, 9, 3),
            status="VOID",
        )
    )
    session.add(
        FeedRecord(
            feed_type="Forensic cancelled feed",
            quantity_kg=999.0,
            feeding_date=datetime(2026, 9, 3),
            total_feed_cost=999.0,
            status="CANCELLED",
        )
    )
    session.commit()


def test_ai_assistant_answers_live_metrics_and_health_from_persisted_rows(
    client,
    registered_animal,
    monkeypatch,
):
    monkeypatch.setattr(
        OperationalDateAuthority,
        "current_date",
        lambda self: date(2026, 9, 4),
    )
    _seed_read_fixture(registered_animal)
    session = get_container().repository_factory.session
    milk_count_before = session.query(MilkProduction).count()
    journal_count_before = session.query(EventJournalModel).count()

    cop = read_cop_metrics(
        question="What was the average and maximum COP/L in September 2026?"
    )
    assert cop["status"] == "OK"
    assert cop["period_cop_per_litre"] == 1.0286
    assert cop["average_daily_cop_per_litre"] == 0.9333
    assert cop["maximum_daily_cop_per_litre"] == 1.1
    assert cop["valid_daily_days"] == 3

    milk = read_operational_data(question="What was milk production in September 2026?")
    assert milk["evidence"]["total_litres"] == 350.0
    assert milk["read_only"] is True

    reproduction = read_operational_data(
        question="How many calves have been delivered in September 2026?"
    )
    assert reproduction["evidence"]["actual_calving_events"] == 1

    mortality = read_operational_data(
        question="How many mortalities were recorded in September 2026?"
    )
    assert mortality["evidence"]["mortality_events"] == 1

    vaccination = read_operational_data(
        question="How many vaccinations were recorded in September 2026?"
    )
    assert vaccination["evidence"]["input_type"] == "vaccination"
    assert vaccination["evidence"]["record_count"] == 1

    dispositions = read_operational_data(
        question="How many litres of milk were sold in September 2026?"
    )
    assert dispositions["evidence"]["metric"] == "milk_dispositions"
    assert dispositions["evidence"]["quantity_litres"] == 120.0

    finance = read_operational_data(
        question="Show finance transactions and expenses in September 2026."
    )
    assert finance["evidence"]["transaction_count"] == 2
    assert finance["evidence"]["expense_total"] == 30.0
    assert all(
        row.get("status") not in {"VOID", "CANCELLED", "DELETED"}
        for row in finance["evidence"]["transactions"]
    )

    feed = read_operational_data(
        question="Show feed records and feeding cost in September 2026."
    )
    assert feed["evidence"]["feed_record_count"] == 0
    assert feed["evidence"]["recorded_feed_cost"] == 0.0

    future = read_operational_data(
        question="What was milk production?",
        start_date="2027-01-01",
        end_date="2027-01-31",
    )
    assert future["data_status"] == "NO_DATA_IN_REQUESTED_PERIOD"
    assert future["evidence"]["metric"] == "operational_period_empty"

    health = read_health_insight(
        question="A cow has fever and reduced appetite. What probable diagnosis and treatment should be assessed?",
        animal_id=registered_animal,
    )
    assert health["probable_conditions"]
    condition_names = [item["condition"] for item in health["probable_conditions"]]
    assert "Metritis and endometritis" in condition_names
    assert "Ketosis" in condition_names
    assert "Lameness and foot disease" not in condition_names
    assert all(item["treatment_guidance"] for item in health["probable_conditions"])
    assert health["assessment_boundary"]
    assert health["read_only"] is True

    udder_health = read_health_insight(
        question="The cow has a hot swollen udder and abnormal milk."
    )
    assert [item["condition"] for item in udder_health["probable_conditions"]] == [
        "Mastitis"
    ]
    assert udder_health["probable_conditions"][0]["treatment_guidance"]

    postpartum_health = read_health_insight(
        question=(
            "A recently calved cow is weak and recumbent with cold extremities. "
            "What probable condition should be assessed?"
        )
    )
    assert [item["condition"] for item in postpartum_health["probable_conditions"]] == [
        "Hypocalcemia (milk fever)"
    ]

    named_health = read_health_insight(question="What is milk fever?")
    assert [item["condition"] for item in named_health["probable_conditions"]] == [
        "Hypocalcemia (milk fever)"
    ]

    from dairyos.assistant.knowledge import GroundedAssistant

    def fail_irrelevant_reference_lookup(*args, **kwargs):
        raise AssertionError("live health history must not query disease reference")

    with monkeypatch.context() as history_patch:
        history_patch.setattr(
            GroundedAssistant,
            "search_health",
            fail_irrelevant_reference_lookup,
        )
        health_history = read_health_insight(
            question="How many health cases were recorded in September 2026?"
        )
    assert health_history["probable_conditions"] == []
    assert health_history["history_requested"] is True
    assert health_history["matching_observation_count"] == 1

    sick_animals = read_health_insight(
        question="Which sick animals have persisted health evidence?"
    )
    assert sick_animals["probable_conditions"] == []
    assert registered_animal in sick_animals["animal_ids_with_health_evidence"]

    schema = read_database_schema(table_name="milk_production", limit=2)
    assert schema["read_only"] is True
    assert schema["metric"] == "database_schema"
    assert schema["selected_table"]["table"] == "milk_production"
    assert len(schema["rows"]) == 2

    inferred_schema = read_database_schema(
        question="Show the milk production table rows for this database."
    )
    assert inferred_schema["selected_table"]["table"] == "milk_production"

    schema_response = client.post(
        "/ai-assistant/ask",
        json={"question": "Show the current database tables and schema."},
    )
    assert schema_response.status_code == 200, schema_response.text
    schema_payload = schema_response.json()
    assert schema_payload["answer_type"] == "LIVE_OPERATIONAL_DATA_SCHEMA"
    assert schema_payload["read_only"] is True
    assert schema_payload["tool_results"]["read_database_schema"]["read_only"] is True
    assert schema_payload["tool_results"]["read_database_schema"]["table_count"] >= 1

    system_health_response = client.post(
        "/ai-assistant/ask",
        json={"question": "How can I run a read-only system health check safely?"},
    )
    assert system_health_response.status_code == 200, system_health_response.text
    system_health_payload = system_health_response.json()
    assert system_health_payload["answer_type"] == "LIVE_SYSTEM_HEALTH"
    assert system_health_payload["read_only"] is True
    assert "read_system_health" in system_health_payload["plan"]
    assert "read_health_insight" not in system_health_payload["plan"]
    assert system_health_payload["tool_results"]["read_system_health"]["read_only"] is True

    logs = read_operational_logs(question="show event history and logs", limit=20)
    assert logs["read_only"] is True
    assert logs["database_logs"]["event_journal"]

    assistant_response = client.post(
        "/ai-assistant/ask",
        json={"question": "What was the average and maximum COP/L in September 2026?"},
    )
    assert assistant_response.status_code == 200, assistant_response.text
    assistant_payload = assistant_response.json()
    assert assistant_payload["assistant_name"] == "AI Assistant"
    assert assistant_payload["read_only"] is True
    assert assistant_payload["answer_type"] == "LIVE_OPERATIONAL_DATA"
    assert "1.1" in assistant_payload["answer"]
    assert "read_cop_metrics" in assistant_payload["plan"]

    health_response = client.post(
        "/ai-assistant/ask",
        json={
            "question": (
                "A cow has fever and reduced appetite. What probable diagnosis "
                "and treatment should be assessed?"
            ),
            "role": "Veterinary / Health",
        },
    )
    assert health_response.status_code == 200, health_response.text
    health_payload = health_response.json()
    assert health_payload["read_only"] is True
    assert health_payload["answer_type"] == "LIVE_HEALTH_INSIGHT"
    assert "veterinary" in health_payload["answer"].lower()
    assert "diagnostic path" in health_payload["expanded_explanation"].lower()

    descriptive_health_response = client.post(
        "/ai-assistant/ask",
        json={
            "question": (
                "A cow has a hot swollen quarter, flakes in milk, and reduced "
                "yield. What are probable conditions and safe next steps?"
            )
        },
    )
    assert descriptive_health_response.status_code == 200, descriptive_health_response.text
    descriptive_health_payload = descriptive_health_response.json()
    assert descriptive_health_payload["read_only"] is True
    assert descriptive_health_payload["answer_type"] == "LIVE_HEALTH_INSIGHT"
    assert "Mastitis" in descriptive_health_payload["answer"]
    assert "read_health_insight" in descriptive_health_payload["plan"]

    health_history_response = client.post(
        "/ai-assistant/ask",
        json={"question": "How many health cases were recorded in September 2026?"},
    )
    assert health_history_response.status_code == 200, health_history_response.text
    health_history_payload = health_history_response.json()
    assert health_history_payload["answer_type"] == "LIVE_OPERATIONAL_DATA"
    assert "0 persisted health case" in health_history_payload["answer"]
    assert "1 health observation" in health_history_payload["answer"]

    vaccination_response = client.post(
        "/ai-assistant/ask",
        json={"question": "How many vaccinations were recorded in September 2026?"},
    )
    assert vaccination_response.status_code == 200, vaccination_response.text
    vaccination_payload = vaccination_response.json()
    assert vaccination_payload["answer_type"] == "LIVE_OPERATIONAL_DATA"
    assert "1 persisted vaccination input event" in vaccination_payload["answer"]

    combined_response = client.post(
        "/ai-assistant/ask",
        json={
            "question": (
                "How many calves have been delivered and how many mortalities "
                "were recorded in September 2026?"
            )
        },
    )
    assert combined_response.status_code == 200, combined_response.text
    combined_payload = combined_response.json()
    assert combined_payload["answer_type"] == "LIVE_OPERATIONAL_DATA"
    assert "calving event" in combined_payload["answer"]
    assert "mortality event" in combined_payload["answer"]

    follow_up = client.post(
        "/ai-assistant/ask",
        json={
            "question": "What about August 2026?",
            "conversation_id": assistant_payload["conversation_id"],
        },
    )
    assert follow_up.status_code == 200, follow_up.text
    follow_up_payload = follow_up.json()
    assert "read_cop_metrics" in follow_up_payload["plan"]
    assert (
        follow_up_payload["tool_results"]["read_cop_metrics"]["period"][
            "effective_start"
        ]
        == "2026-08-01"
    )

    assert session.query(MilkProduction).count() == milk_count_before
    assert session.query(EventJournalModel).count() == journal_count_before


def test_ai_assistant_does_not_treat_an_empty_future_period_as_unbounded():
    from dairyos.assistant.operational import _period_filter, _resolve_window

    window = _resolve_window(
        "milk production",
        operational_date=date(2026, 9, 4),
        start_date="2027-01-01",
        end_date="2027-01-31",
    )

    assert window.is_empty is True
    assert _period_filter(window, date(2026, 9, 1)) is False


def test_ai_assistant_database_guard_rejects_writes_in_read_only_tool_transaction(
    client,
):
    with pytest.raises(SQLAlchemyError):
        _with_read_only(
            lambda factory: factory.session.execute(
                text(
                    "INSERT INTO app_settings (key, value) "
                    "VALUES ('ai_assistant_write_probe', 'blocked')"
                )
            )
        )

    session = get_container().repository_factory.session
    assert (
        session.execute(
            text(
                "SELECT count(*) FROM app_settings WHERE key='ai_assistant_write_probe'"
            )
        ).scalar_one()
        == 0
    )


def test_ai_assistant_clinical_aliases_and_modal_may_are_unambiguous():
    from dairyos.assistant.knowledge import GroundedAssistant
    from dairyos.assistant.operational import _resolve_window

    grounded = GroundedAssistant()
    assert [item.title for item in grounded.search_health("What is BRD?")] == [
        "Bovine respiratory disease"
    ]
    assert [item.title for item in grounded.search_health("What is FMD?")] == [
        "Foot-and-mouth disease (FMD)"
    ]

    window = _resolve_window(
        "What may cause fever?",
        operational_date=date(2026, 9, 4),
    )
    assert window.requested_start is None
    assert window.requested_end is None


def test_ai_assistant_resolves_explicit_month_year_and_redacts_nested_credentials():
    from dairyos.assistant.operational import _json_safe, _resolve_window

    window = _resolve_window(
        "What was milk production in September 2025?",
        operational_date=date(2026, 9, 4),
    )
    assert window.requested_start == date(2025, 9, 1)
    assert window.requested_end == date(2025, 9, 30)

    safe = _json_safe(
        {
            "connection": {"url": "postgresql://dairyos:secret@127.0.0.1/db"},
            "notes": "token=abc123 and password=hidden",
        }
    )
    assert safe["connection"]["url"] == "[REDACTED]"
    assert "secret" not in str(safe)
    assert "hidden" not in str(safe)
