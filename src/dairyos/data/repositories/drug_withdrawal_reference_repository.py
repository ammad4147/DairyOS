"""Repository for the maintained drug withdrawal reference table.

The table ships EMPTY by design (see the model docstring for why: this
session has no authoritative source for per-product withdrawal times,
and shipping guessed veterinary values in a food-safety system would
be worse than shipping nothing). The farm's manager/vet populates it
via `POST /farm/drug-reference` from the actual product labels in use.
"""

from ..models.drug_withdrawal_reference import DrugWithdrawalReference


class DrugWithdrawalReferenceRepository:

    def __init__(self, session=None):

        self.session = session
        self.records = []

    def add(self, record):

        if self.session:
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
            return record

        self.records.append(record)
        return record

    def get_all(self):

        if self.session:
            return (
                self.session.query(DrugWithdrawalReference)
                .order_by(DrugWithdrawalReference.medicine.asc())
                .all()
            )

        return self.records

    def find_by_medicine(self, medicine):
        """Case-insensitive exact-name lookup."""

        if not medicine:
            return None

        needle = str(medicine).strip().lower()

        if not needle:
            return None

        if self.session:
            for row in self.session.query(DrugWithdrawalReference).all():
                if str(row.medicine).strip().lower() == needle:
                    return row
            return None

        for row in self.records:
            if str(row.medicine).strip().lower() == needle:
                return row

        return None

    def upsert(
        self,
        *,
        medicine,
        milk_withdrawal_days,
        meat_withdrawal_days=None,
        notes=None,
        verified=False,
        updated_by=None,
    ):
        """Create or update a reference entry by medicine name."""

        existing = self.find_by_medicine(medicine)

        if existing is not None:
            existing.milk_withdrawal_days = milk_withdrawal_days
            existing.meat_withdrawal_days = meat_withdrawal_days
            existing.notes = notes
            existing.verified = bool(verified)
            existing.updated_by = updated_by

            if self.session:
                self.session.add(existing)
                self.session.commit()
                self.session.refresh(existing)

            return existing

        record = DrugWithdrawalReference(
            medicine=medicine,
            milk_withdrawal_days=milk_withdrawal_days,
            meat_withdrawal_days=meat_withdrawal_days,
            notes=notes,
            verified=bool(verified),
            updated_by=updated_by,
        )

        return self.add(record)

    def count(self):

        if self.session:
            return self.session.query(DrugWithdrawalReference).count()

        return len(self.records)
