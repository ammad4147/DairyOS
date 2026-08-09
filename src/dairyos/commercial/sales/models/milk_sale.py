from dataclasses import dataclass



@dataclass
class MilkSale:


    sale_id: str

    milk_quantity_litres: float

    selling_price_per_litre: float

    daily_revenue: float

    status: str

    action: str
