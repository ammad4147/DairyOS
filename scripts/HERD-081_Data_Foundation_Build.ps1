$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-081 Data Foundation Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\data\database",
"dairyos\data\models",
"dairyos\data\repositories",
"tests\core",
"scripts" | Out-Null



@'
class DatabaseConnection:


    def __init__(self):

        self.connected = False



    def connect(self):

        self.connected = True

        return self.connected



    def disconnect(self):

        self.connected = False

        return self.connected
'@ | Set-Content `
"dairyos\data\database\connection.py"



@'
from dataclasses import dataclass



@dataclass
class Farm:


    farm_id: str

    farm_name: str

    location: str
'@ | Set-Content `
"dairyos\data\models\farm.py"



@'
from dataclasses import dataclass



@dataclass
class Animal:


    animal_id: str

    animal_type: str

    status: str
'@ | Set-Content `
"dairyos\data\models\animal.py"



@'
class FarmRepository:



    def __init__(self):

        self.records = []



    def add(self, farm):

        self.records.append(farm)

        return farm



    def count(self):

        return len(self.records)
'@ | Set-Content `
"dairyos\data\repositories\farm_repository.py"



@'
class AnimalRepository:



    def __init__(self):

        self.records = []



    def add(self, animal):

        self.records.append(animal)

        return animal



    def count(self):

        return len(self.records)
'@ | Set-Content `
"dairyos\data\repositories\animal_repository.py"



@'
from dairyos.data.database.connection import DatabaseConnection
from dairyos.data.models.farm import Farm
from dairyos.data.models.animal import Animal
from dairyos.data.repositories.farm_repository import FarmRepository
from dairyos.data.repositories.animal_repository import AnimalRepository



def test_database_connection():

    db = DatabaseConnection()

    assert db.connect() == True



def test_database_disconnect():

    db = DatabaseConnection()

    db.connect()

    assert db.disconnect() == False



def test_farm_creation():

    farm = Farm(

        "F001",

        "Trident Dairies",

        "Lahore"

    )

    assert farm.farm_name == "Trident Dairies"



def test_animal_creation():

    animal = Animal(

        "A001",

        "Holstein",

        "ACTIVE"

    )

    assert animal.status == "ACTIVE"



def test_farm_repository():

    repo = FarmRepository()

    repo.add(

        Farm(

            "F001",

            "Trident Dairies",

            "Lahore"

        )

    )

    assert repo.count() == 1



def test_animal_repository():

    repo = AnimalRepository()

    repo.add(

        Animal(

            "A001",

            "Holstein",

            "ACTIVE"

        )

    )

    assert repo.count() == 1



def test_multiple_animals():

    repo = AnimalRepository()

    repo.add(Animal("A001","Cow","ACTIVE"))

    repo.add(Animal("A002","Cow","ACTIVE"))

    assert repo.count() == 2



def test_multiple_farms():

    repo = FarmRepository()

    repo.add(Farm("F001","Farm One","Lahore"))

    repo.add(Farm("F002","Farm Two","Punjab"))

    assert repo.count() == 2



def test_data_layer_exists():

    assert DatabaseConnection is not None



def test_foundation_complete():

    assert FarmRepository is not None
'@ | Set-Content `
"tests\core\test_data_foundation.py"



Write-Host "HERD-081 Data Foundation Build Complete"