from __future__ import annotations

from sqlalchemy.orm import Session

from dairyos.data.database.models.farm_model import FarmModel
from dairyos.data.models.farm import Farm


class FarmRepository:
    """
    PostgreSQL-backed farm repository.

    Sprint-038 persistence hardening:
    - No in-memory record store.
    - Persistence is performed through the injected SQLAlchemy Session.
    - Repository does not create or own database sessions.
    - RepositoryFactory remains the application composition boundary.
    """

    def __init__(
        self,
        session: Session,
    ):
        if session is None:
            raise ValueError(
                "FarmRepository requires a database session."
            )

        self.session = session

    def add(
        self,
        farm: Farm | FarmModel,
    ):
        """
        Persist a farm.

        Domain Farm objects are translated into FarmModel before
        persistence. FarmModel instances may also be supplied by
        existing persistence-layer callers.
        """

        if isinstance(farm, FarmModel):
            model = farm

        elif isinstance(farm, Farm):
            model = FarmModel(
                farm_id=farm.farm_id,
                farm_name=farm.farm_name,
                location=farm.location,
            )

        else:
            raise TypeError(
                "FarmRepository.add() requires Farm or FarmModel."
            )

        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)

        return model

    def save(
        self,
        farm: Farm | FarmModel,
    ):
        """
        Compatibility persistence contract.
        """

        return self.add(farm)

    def get_by_farm_id(
        self,
        farm_id: str,
    ) -> FarmModel | None:
        """
        Return a farm by primary identifier.
        """

        return (
            self.session.query(FarmModel)
            .filter(
                FarmModel.farm_id == farm_id
            )
            .first()
        )

    def get_all(
        self,
    ) -> list[FarmModel]:
        """
        Return all persisted farms.
        """

        return (
            self.session.query(FarmModel)
            .order_by(FarmModel.farm_id.asc())
            .all()
        )

    def exists(
        self,
        farm_id: str,
    ) -> bool:
        """
        Return whether a farm exists.
        """

        return (
            self.get_by_farm_id(farm_id)
            is not None
        )

    def count(
        self,
    ) -> int:
        """
        Return the number of persisted farms.
        """

        return (
            self.session.query(FarmModel)
            .count()
        )
