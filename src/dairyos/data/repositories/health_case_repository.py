from ..models.health_case import HealthCase


class HealthCaseRepository:
    """Persistence for HealthCase (G5.1)."""

    def __init__(self, session=None):

        self.session = session
        self.records = []

    def add(self, case):

        if self.session:
            self.session.add(case)
            self.session.commit()
            self.session.refresh(case)
            return case

        self.records.append(case)
        return case

    def get_all(self):

        if self.session:
            return self.session.query(HealthCase).all()

        return self.records

    def get_by_id(self, record_id):

        if self.session:
            return (
                self.session.query(HealthCase)
                .filter(HealthCase.id == record_id)
                .first()
            )

        for item in self.records:
            if getattr(item, "id", None) == record_id:
                return item

        return None

    def get_by_case_id(self, case_id):

        if self.session:
            return (
                self.session.query(HealthCase)
                .filter(HealthCase.case_id == case_id)
                .first()
            )

        for item in self.records:
            if getattr(item, "case_id", None) == case_id:
                return item

        return None

    def get_by_animal(self, animal_id):

        return [
            case for case in self.get_all()
            if case.animal_id == animal_id
        ]

    def count_opened_on(self, date_prefix: str) -> int:
        """How many cases were already opened whose case_id carries this
        date prefix (e.g. "HL-260814") -- used to derive the next sequence
        number for a new case_id. Never guesses at a count independent of
        what's actually persisted.
        """

        return sum(
            1
            for case in self.get_all()
            if str(case.case_id or "").startswith(date_prefix)
        )
