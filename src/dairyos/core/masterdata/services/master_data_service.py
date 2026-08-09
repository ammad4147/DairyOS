class MasterDataService:


    def __init__(self):

        self.farms = []

        self.locations = []

        self.breeds = []

        self.animal_types = []



    def add_farm(self, farm):

        self.farms.append(farm)

        return farm



    def add_location(self, location):

        self.locations.append(location)

        return location



    def add_breed(self, breed):

        self.breeds.append(breed)

        return breed



    def add_animal_type(self, animal_type):

        self.animal_types.append(animal_type)

        return animal_type
