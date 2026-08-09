from dataclasses import dataclass



@dataclass
class MilkQuality:


    batch_id: str

    volume_litres: float

    fat_percentage: float

    protein_percentage: float

    quality_status: str

    quality_grade: str
