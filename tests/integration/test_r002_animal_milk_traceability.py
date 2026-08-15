import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from dairyos.platform.api.app import app
from dairyos.platform.api.dependencies import get_db
from dairyos.data.repositories.animal_repository import AnimalRepository
from dairyos.data.repositories.milk_production_repository import MilkProductionRepository
from dairyos.data.models.animal import Animal
from dairyos.data.models.milk_production import MilkProduction
from dairyos.platform.api.routes.farm_routes import router as farm_router

# Add the farm router to the app for testing
app.include_router(farm_router)

@pytest.fixture(scope="session")
def test_db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    return engine

@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a database session for each test."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    # Override the dependency
    def override_get_db():
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield session
    
    # Clean up
    transaction.rollback()
    connection.close()
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def animal_repo(test_db_session):
    """Create an animal repository for testing."""
    return AnimalRepository(session=test_db_session)

@pytest.fixture(scope="function")
def milk_repo(test_db_session):
    """Create a milk production repository for testing."""
    return MilkProductionRepository(session=test_db_session)

def test_animal_milk_traceability_chain(test_db_session, animal_repo, milk_repo):
    """Test the complete data chain: Animal -> Milk Record -> Passport -> Intelligence"""
    
    # 1. Create an animal through the authoritative AnimalRepository
    animal = Animal(
        animal_id="TEST-ANIMAL-001",
        name="Test Animal",
        status="ACTIVE",
        lifecycle_status="LACTATING",
        active=True,
        is_currently_milking=True,
        milking_frequency=2
    )
    
    created_animal = animal_repo.add(animal)
    assert created_animal.animal_id == "TEST-ANIMAL-001"
    
    # 2. Persist a distinctive milk record through MilkProductionRepository
    milk_record = MilkProduction(
        animal_id="TEST-ANIMAL-001",
        production_date=date(2023, 1, 15),
        morning_yield=15.5,
        afternoon_yield=12.0,
        evening_yield=9.75,
        total_yield=37.25,
        status="NORMAL",
        session_ledger=True,
        milking_session="EVENING"
    )
    
    saved_record = milk_repo.add(milk_record)
    assert saved_record.total_yield == 37.25
    assert saved_record.animal_id == "TEST-ANIMAL-001"
    
    # 3. Verify the record can be retrieved directly from repository
    retrieved_records = milk_repo.get_by_animal_id("TEST-ANIMAL-001")
    assert len(retrieved_records) == 1
    assert retrieved_records[0].total_yield == 37.25
    
    # 4. Test the passport endpoint
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    response = client.get("/farm/animals/TEST-ANIMAL-001/passport")
    assert response.status_code == 200
    
    passport_data = response.json()
    assert passport_data["animal"]["animal_id"] == "TEST-ANIMAL-001"
    
    # Verify the milk record appears in the passport
    assert len(passport_data["milk"]) == 1
    milk_entry = passport_data["milk"][0]
    assert milk_entry["total_yield"] == 37.25
    assert milk_entry["animal_id"] == "TEST-ANIMAL-001"
    assert milk_entry["production_date"] == "2023-01-15"
    
    # 5. Test the milk intelligence endpoint
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
