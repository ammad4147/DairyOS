from __future__ import annotations

from sqlalchemy.orm import Session

from dairyos.data.repositories.animal_repository import AnimalRepository
from dairyos.data.repositories.farm_repository import FarmRepository
from dairyos.data.repositories.milk_production_repository import MilkProductionRepository
from dairyos.data.repositories.milk_disposition_repository import MilkDispositionRepository
from dairyos.data.repositories.milking_session_record_repository import (
    MilkingSessionRecordRepository,
)
from dairyos.data.repositories.financial_repository import FinancialRepository
from dairyos.data.repositories.inventory_repository import InventoryRepository
from dairyos.data.repositories.user_repository import UserRepository
from dairyos.farm.operations.repositories.adapters.database_breeding_repository import DatabaseBreedingRepository
from dairyos.data.repositories.operational_event_repository import OperationalEventRepository
from dairyos.data.repositories.feed_record_repository import FeedRecordRepository
from dairyos.data.repositories.feed_ration_repository import FeedRationRepository
from dairyos.data.repositories.health_observation_repository import HealthObservationRepository
from dairyos.data.repositories.health_case_repository import HealthCaseRepository
from dairyos.data.repositories.database_operational_state_repository import DatabaseOperationalStateRepository
from dairyos.data.repositories.treatment_repository import TreatmentRepository
from dairyos.data.repositories.drug_withdrawal_reference_repository import DrugWithdrawalReferenceRepository
from dairyos.data.database.session import create_application_session


class RepositoryFactory:
    """Application persistence composition boundary."""

    def __init__(self, session: Session, owns_session: bool = False):
        if session is None:
            raise ValueError("RepositoryFactory requires a database session.")
        self._session = session
        self._owns_session = bool(owns_session)
        self._closed = False

    @property
    def session(self) -> Session:
        return self._session

    @property
    def owns_session(self) -> bool:
        return self._owns_session

    @property
    def closed(self) -> bool:
        return self._closed

    def animal(self):
        return AnimalRepository(session=self._session)

    def farm(self):
        return FarmRepository(session=self._session)

    def milk(self):
        return MilkProductionRepository(
            session=self._session,
            animal_repository=self.animal(),
        )

    def milk_dispositions(self):
        return MilkDispositionRepository(session=self._session)

    def milking_session_ledger(self):
        return MilkingSessionRecordRepository(session=self._session)

    def finance(self):
        return FinancialRepository(session=self._session)

    def inventory(self):
        return InventoryRepository(session=self._session)

    def users(self):
        return UserRepository(session=self._session)

    def operational_events(self):
        return OperationalEventRepository(session=self._session)

    def feed(self):
        return FeedRecordRepository(session=self._session)

    def feed_rations(self):
        return FeedRationRepository(session=self._session)

    def health(self):
        return HealthObservationRepository(session=self._session)

    def health_cases(self):
        return HealthCaseRepository(session=self._session)

    def breeding(self):
        return DatabaseBreedingRepository(session=self._session)

    def operational_state(self):
        return DatabaseOperationalStateRepository(session=self._session)

    def treatment(self):
        return TreatmentRepository(session=self._session)

    def drug_reference(self):
        return DrugWithdrawalReferenceRepository(session=self._session)

    def milk_production(self):
        return self.milk()

    def financial(self):
        return self.finance()

    def feed_records(self):
        return self.feed()

    def health_observations(self):
        return self.health()

    @staticmethod
    def _create_session() -> Session:
        return create_application_session()

    @classmethod
    def create(cls, session: Session | None = None) -> "RepositoryFactory":
        if session is None:
            return cls(session=cls._create_session(), owns_session=True)
        return cls(session=session, owns_session=False)

    def close(self) -> None:
        if self._closed:
            return
        if self._owns_session:
            self._session.close()
        self._closed = True

    def rollback(self) -> None:
        self._session.rollback()

    @classmethod
    def _legacy(cls) -> "RepositoryFactory":
        return cls.create()

    @classmethod
    def animal_legacy(cls):
        return cls._legacy().animal()

    @classmethod
    def farm_legacy(cls):
        return cls._legacy().farm()

    @classmethod
    def milk_legacy(cls):
        return cls._legacy().milk()

    @classmethod
    def finance_legacy(cls):
        return cls._legacy().finance()

    @classmethod
    def operational_events_legacy(cls):
        return cls._legacy().operational_events()

    @classmethod
    def feed_legacy(cls):
        return cls._legacy().feed()

    @classmethod
    def health_legacy(cls):
        return cls._legacy().health()

    @classmethod
    def operational_state_legacy(cls):
        return cls._legacy().operational_state()
