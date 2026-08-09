from __future__ import annotations

from sqlalchemy.orm import Session

from dairyos.data.repositories.animal_repository import (
    AnimalRepository,
)

from dairyos.data.repositories.farm_repository import (
    FarmRepository,
)

from dairyos.data.repositories.milk_production_repository import (
    MilkProductionRepository,
)

from dairyos.data.repositories.financial_repository import (
    FinancialRepository,
)

from dairyos.farm.operations.repositories.adapters.database_breeding_repository import (
    DatabaseBreedingRepository,
)

from dairyos.data.repositories.operational_event_repository import (
    OperationalEventRepository,
)

from dairyos.data.repositories.feed_record_repository import (
    FeedRecordRepository,
)

from dairyos.data.repositories.health_observation_repository import (
    HealthObservationRepository,
)

from dairyos.data.repositories.database_operational_state_repository import (
    DatabaseOperationalStateRepository,
)

from dairyos.data.database.session import (
    get_session,
)


class RepositoryFactory:
    """
    Application persistence composition boundary.

    Owns construction of persistence adapters.

    The class-level API is intentionally retained for
    compatibility with existing DairyOS callers.

    New runtime composition should prefer:

        factory = RepositoryFactory.create(session)

    and then:

        factory.animal()
        factory.milk()
        factory.operational_state()
    """

    def __init__(
        self,
        session: Session,
    ):
        if session is None:
            raise ValueError(
                "RepositoryFactory requires a database session."
            )

        self._session = session


    @property
    def session(self) -> Session:
        return self._session


    def animal(self):
        return AnimalRepository(
            session=self._session,
        )


    def farm(self):
        return FarmRepository(
            session=self._session,
        )


    def milk(self):
        return MilkProductionRepository(
            session=self._session,
        )


    def finance(self):
        return FinancialRepository(
            session=self._session,
        )


    def operational_events(self):
        return OperationalEventRepository(
            session=self._session,
        )


    def feed(self):
        return FeedRecordRepository(
            session=self._session,
        )


    def health(self):
        return HealthObservationRepository(
            session=self._session,
        )


    def breeding(self):
        return DatabaseBreedingRepository(
            session=self._session,
        )

    def operational_state(self):
        return DatabaseOperationalStateRepository(
            session=self._session,
        )


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
        """
        Create the application's database session.

        The caller owns the session lifecycle.
        """

        return next(
            get_session()
        )


    @classmethod
    def create(
        cls,
        session: Session | None = None,
    ) -> "RepositoryFactory":
        """
        Explicit composition constructor.
        """

        if session is None:
            session = cls._create_session()

        return cls(
            session=session,
        )


    @classmethod
    def _legacy(
        cls,
    ) -> "RepositoryFactory":
        """
        Compatibility factory for existing class-level callers.
        """

        return cls.create()


    # ------------------------------------------------------------------
    # Legacy class-level repository construction
    # ------------------------------------------------------------------

    @classmethod
    def animal_legacy(
        cls,
    ):
        return cls._legacy().animal()


    @classmethod
    def farm_legacy(
        cls,
    ):
        return cls._legacy().farm()


    @classmethod
    def milk_legacy(
        cls,
    ):
        return cls._legacy().milk()


    @classmethod
    def finance_legacy(
        cls,
    ):
        return cls._legacy().finance()


    @classmethod
    def operational_events_legacy(
        cls,
    ):
        return cls._legacy().operational_events()


    @classmethod
    def feed_legacy(
        cls,
    ):
        return cls._legacy().feed()


    @classmethod
    def health_legacy(
        cls,
    ):
        return cls._legacy().health()


    @classmethod
    def operational_state_legacy(
        cls,
    ):
        return cls._legacy().operational_state()
