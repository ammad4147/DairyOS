from dataclasses import dataclass



@dataclass
class Relationship:

    source_id: str

    relation_type: str

    target_id: str

