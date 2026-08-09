from dairyos.data.database.unit_of_work import UnitOfWork

from dairyos.data.repositories.repository_factory import RepositoryFactory


def get_unit_of_work():

    with UnitOfWork() as unit:

        yield unit



def get_milk_repository():

    unit = UnitOfWork()

    try:

        yield RepositoryFactory.milk(
            session=unit.connection
        )

    finally:

        unit.session.close()



def get_finance_repository():

    unit = UnitOfWork()

    try:

        yield RepositoryFactory.finance(
            session=unit.connection
        )

    finally:

        unit.session.close()



def get_event_repository():

    unit = UnitOfWork()

    try:

        yield RepositoryFactory.operational_events(
            session=unit.connection
        )

    finally:

        unit.session.close()
