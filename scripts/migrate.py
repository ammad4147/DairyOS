import argparse

from dairyos.data.database.session import engine
from dairyos.data.database.base import Base

from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.animal import Animal
from dairyos.data.models.farm import Farm



def initialize():

    print("[*] Running database initialization")

    Base.metadata.create_all(
        bind=engine
    )

    print("[+] Database schema ready")



def status():

    print("[*] Database connection status")

    try:

        connection = engine.connect()

        connection.close()

        print("[+] DATABASE ONLINE")


    except Exception as error:

        print("[X] DATABASE ERROR")

        print(error)



def main():

    parser = argparse.ArgumentParser(
        description="DairyOS Database Migration Utility"
    )


    parser.add_argument(
        "command",
        choices=[
            "init",
            "status"
        ]
    )


    args = parser.parse_args()



    if args.command == "init":

        initialize()



    elif args.command == "status":

        status()



if __name__ == "__main__":

    main()
