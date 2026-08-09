from ..models.herd_snapshot import HerdSnapshot

from dairyos.herd.models import AnimalStatus



class HerdMetricsService:


    def calculate(
        self,
        animals
    ):

        milking = 0

        dry = 0

        heifers = 0

        calves = 0


        for animal in animals:


            if animal.status == AnimalStatus.MILKING_COW:

                milking += 1


            elif animal.status == AnimalStatus.DRY_COW:

                dry += 1


            elif animal.status in [

                AnimalStatus.HEIFER,

                AnimalStatus.PREGNANT_HEIFER

            ]:

                heifers += 1


            elif animal.status == AnimalStatus.CALF:

                calves += 1



        return HerdSnapshot(

            total_animals=len(animals),

            milking_cows=milking,

            dry_cows=dry,

            heifers=heifers,

            calves=calves

        )
