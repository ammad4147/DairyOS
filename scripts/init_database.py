from dairyos.data.database.session import engine
from dairyos.data.database.base import Base

from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.animal import Animal
from dairyos.data.models.farm import Farm



def initialize_database():

    print("[*] Creating database tables...")

    Base.metadata.create_all(
        bind=engine
    )

    print("[+] Database initialization completed")



if __name__ == "__main__":

    initialize_database()
