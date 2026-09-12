"""Database-level protection for the authoritative Milk daily ledger."""

from sqlalchemy.exc import IntegrityError

from dairyos.app import container
from dairyos.data.models.milk_production import MilkProduction


def test_direct_orm_write_cannot_leave_a_stale_daily_total(
    client,
    registered_animal,
):
    response = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "milking_session": "MORNING",
            "morning_yield": 10.0,
        },
    )
    assert response.status_code == 200, response.text

    session = container.repository_factory.session
    row = session.query(MilkProduction).one()
    row.morning_yield = 11.0

    try:
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError(
                "The database accepted a direct Milk write with a stale total."
            )

        session.expire_all()
        persisted = session.query(MilkProduction).one()
        assert persisted.morning_yield == 10.0
        assert persisted.total_yield == 10.0
    finally:
        session.rollback()
