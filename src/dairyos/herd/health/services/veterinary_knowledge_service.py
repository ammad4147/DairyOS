from ..models.disease_profile import DiseaseProfile
from ..models.symptom_reference import SymptomReference


class VeterinaryKnowledgeService:


    def __init__(self):

        self.diseases = []

        self.symptoms = []

        self._load_default_database()



    def _load_default_database(self):

        self.diseases.extend(

            [

                DiseaseProfile(
                    "Mastitis",
                    "Udder Infection",
                    "Cattle",
                    [
                        "Milk yield reduction",
                        "Udder swelling",
                        "Abnormal milk",
                        "Fever"
                    ],
                    [
                        "Clinical examination",
                        "California Mastitis Test",
                        "Milk culture"
                    ],
                    "Maintain hygiene and proper milking procedures",
                    "Veterinary mastitis treatment protocol",
                    "DairyOS Veterinary Knowledge Base"
                ),


                DiseaseProfile(
                    "Ketosis",
                    "Metabolic Disorder",
                    "Cattle",
                    [
                        "Reduced feed intake",
                        "Milk production decline",
                        "Weight loss",
                        "Depression"
                    ],
                    [
                        "Clinical examination",
                        "Ketone testing"
                    ],
                    "Balanced transition feeding",
                    "Veterinary metabolic disorder protocol",
                    "DairyOS Veterinary Knowledge Base"
                ),


                DiseaseProfile(
                    "Metritis",
                    "Reproductive Disease",
                    "Cattle",
                    [
                        "Fever",
                        "Abnormal uterine discharge",
                        "Reduced appetite",
                        "Milk drop"
                    ],
                    [
                        "Clinical examination",
                        "Reproductive examination"
                    ],
                    "Good calving hygiene",
                    "Veterinary reproductive health protocol",
                    "DairyOS Veterinary Knowledge Base"
                )

            ]

        )


        self.symptoms.extend(

            [

                SymptomReference(
                    "Milk yield reduction",
                    [
                        "Mastitis",
                        "Ketosis",
                        "Metritis"
                    ],
                    [
                        "Check udder",
                        "Check feed intake",
                        "Clinical examination"
                    ]
                ),


                SymptomReference(
                    "Reduced feed intake",
                    [
                        "Ketosis",
                        "Rumen disorder",
                        "Disease onset"
                    ],
                    [
                        "Temperature check",
                        "Rumen observation"
                    ]
                ),


                SymptomReference(
                    "Udder swelling",
                    [
                        "Mastitis"
                    ],
                    [
                        "Milk quality test",
                        "Veterinary examination"
                    ]
                )

            ]

        )



    def find_disease(self, name):

        return [

            disease

            for disease in self.diseases

            if disease.disease_name.lower() == name.lower()

        ]



    def search_symptom(self, symptom):

        aliases = {

            "milk reduction": "milk yield reduction",

            "reduced appetite": "reduced feed intake"

        }


        normalized = symptom.lower().strip()


        normalized = aliases.get(

            normalized,

            normalized

        )


        return [

            item

            for item in self.symptoms

            if item.symptom.lower() == normalized

        ]



    def find_by_symptom(self, symptom):

        matches = self.search_symptom(symptom)


        results = []


        for match in matches:

            for condition in match.related_conditions:

                results.extend(

                    self.find_disease(condition)

                )


        return results



    def disease_count(self):

        return len(self.diseases)



    def symptom_count(self):

        return len(self.symptoms)
