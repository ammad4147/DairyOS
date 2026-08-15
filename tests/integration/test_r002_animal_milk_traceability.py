from datetime import date, timedelta

from dairyos.app import container
from dairyos.data.models.milk_production import MilkProduction


def test_animal_milk_traceability_chain(client, registered_animal):
    """Verify Animal -> Milk Record -> Passport -> Intelligence."""

    # 1. The existing fixture creates a real persisted animal.
    animal_id = registered_animal

    assert animal_id

    # 2. Use the application's authoritative repository factory.
    repository_factory = container.repository_factory

    # 3. Get the authoritative milk-production repository.
    milk_repo = repository_factory.milk_production()

    # 4. Persist a distinctive milk record inside the intelligence window.
    production_date = date.today() - timedelta(days=2)

    milk_record = MilkProduction(
        animal_id=animal_id,
        production_date=production_date,
        morning_yield=15.5,
        afternoon_yield=12.0,
        evening_yield=9.75,
        total_yield=37.25,
        status="NORMAL",
        session_ledger=True,
        milking_session="EVENING",
    )

    saved_record = milk_repo.add(milk_record)

    assert saved_record.animal_id == animal_id
    assert saved_record.total_yield == 37.25

    # 5. Verify persistence through the repository.
    retrieved_records = milk_repo.get_by_animal_id(animal_id)

    assert len(retrieved_records) == 1
    assert retrieved_records[0].animal_id == animal_id
    assert retrieved_records[0].total_yield == 37.25

    # 6. Verify the passport endpoint exposes the persisted milk record.
    response = client.get(f"/farm/animals/{animal_id}/passport")

    assert response.status_code == 200, response.text

    passport_data = response.json()

    assert passport_data["animal"]["animal_id"] == animal_id

    assert len(passport_data["history"]["milk"]) == 1
    assert passport_data["record_counts"]["milk"] == 1

    milk_entry = passport_data["history"]["milk"][0]

    assert milk_entry["animal_id"] == animal_id
    assert milk_entry["total_yield"] == 37.25
    assert milk_entry["production_date"].startswith(
        production_date.isoformat()
    )

    # 7. Verify the milk intelligence endpoint sees the persisted record.
    response = client.get("/farm/milk/intelligence")

    assert response.status_code == 200, response.text

    intelligence_data = response.json()

    assert "seven_day_average_litres" in intelligence_data
    assert "seven_day_total_litres" in intelligence_data
    assert "yield_drop_alerts" in intelligence_data
    assert "animal_ranking" in intelligence_data
    assert "daily_trend" in intelligence_data

    # The distinctive 37.25 L record must contribute to the seven-day
    # intelligence window.
    assert intelligence_data["seven_day_total_litres"] >= 37.25
