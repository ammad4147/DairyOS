from dataclasses import dataclass


@dataclass
class SystemSetting:

    key: str

    value: str

    category: str = "SYSTEM"
