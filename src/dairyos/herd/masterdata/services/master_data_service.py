class MasterDataService:


    def __init__(self):

        self.breeds = []

        self.classes = []

        self.production_groups = []



    def add_breed(

        self,

        breed

    ):

        self.breeds.append(breed)

        return breed



    def get_breeds(self):

        return self.breeds
