from dataclasses import dataclass



@dataclass
class MonitoringEvent:


    event_id: str

    category: str

    observation: str

    severity: str

    recommended_action: str
