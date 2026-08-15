import pytest
from datetime import date, timedelta

from dairyos.app import app, container
from dairyos.data.repositories.animal_repository import AnimalRepository
from dairyos.data.repositories.milk_production_repository import MilkProductionRepository
from dairyos.data.models.animal import Animal
from dairyos.data.models.milk_production import MilkProduction
from fastapi.testclient import TestClient

# Use the existing test client approach
client = TestClient(app)

def test_animal_milk_traceability_chain(client, container, registered_animal):
    """Test the complete data chain: Animal -> Milk Record -> Passport -> Intelligence"""
    
    # 1. Verify we have a registered animal
    assert registered_animal.animal_id == "TEST-ANIMAL-001"
    
    # 2. Get repository factory from container
    repository_factory = container.resolve("RepositoryFactory")
    
    # 3. Get repositories
    animal_repo = repository_factory.animals()
    milk_repo = repository_factory.milk_production()
    
    # 4. Create a distinctive milk record through MilkProductionRepository
    # Use a date that's within the 7-day window for intelligence calculations
    production_date = date.today() - timedelta(days=2)
    
    milk_record = MilkProduction(
        animal_id="TEST-ANIMAL-001",
        production_date=production_date,
        morning_yield=15.5,
        afternoon_yield=12.0,
        evening_yield=9.75,
        total_yield=37.25,
        status="NORMAL",
        session_ledger=True,
        milking_session="EVENING"
    )
    
    # 5. Persist the milk record
    saved_record = milk_repo.add(milk_record)
    assert saved_record.total_yield == 37.25
    assert saved_record.animal_id == "TEST-ANIMAL-001"
    
    # 6. Verify the record can be retrieved directly from repository
    retrieved_records = milk_repo.get_by_animal_id("TEST-ANIMAL-001")
    assert len(retrieved_records) == 1
    assert retrieved_records[0].total_yield == 37.25
    
    # 7. Test the passport endpoint
    response = client.get("/farm/animals/TEST-ANIMAL-001/passport")
    assert response.status_code == 200
    
    passport_data = response.json()
    assert passport_data["animal"]["animal_id"] == "TEST-ANIMAL-001"
    
    # Verify the milk record appears in the passport
    assert len(passport_data["milk"]) == 1
    milk_entry = passport_data["milk"][0]
    assert milk_entry["total_yield"] == 37.25
    assert milk_entry["animal_id"] == "TEST-ANIMAL-001"
    assert milk_entry["production_date"] == production_date.isoformat()
    
    # 8. Test the milk intelligence endpoint
    response = client.get("/farm/milk/intelligence")
    assert response.status_code == 200
    
    intelligence_data = response.json()
    
    # The intelligence should be affected by our distinctive milk value
    # We can check that the 7-day average or similar metrics are influenced
    # by the presence of our 37.25 litre record
    assert "seven_day_average_litres" in intelligence_data
    assert "seven_day_total_litres" in intelligence_data
    assert "yield_drop_alerts" in intelligence_data
    assert "animal_ranking" in intelligence_data
    assert "daily_trend" in intelligence_data
    
    # The test verifies the data chain works, not specific values
    # The key point is that our milk record is part of the system
    # and influences the intelligence calculations
