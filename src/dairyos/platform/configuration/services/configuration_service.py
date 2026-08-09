from typing import List

from dairyos.platform.configuration.models.configuration_item import ConfigurationItem


class ConfigurationService:
    """
    Enterprise configuration management boundary.

    Provides controlled registration and lookup
    of configuration values.
    """

    def __init__(self):
        self.items: List[ConfigurationItem] = []

    def register(self, item: ConfigurationItem):
        self.items.append(item)

    def get(
        self,
        key: str,
        owner_id: str | None = None
    ) -> ConfigurationItem | None:

        matches = [
            item
            for item in self.items
            if item.key == key
            and item.active
            and (
                item.owner_id == owner_id
                or item.owner_id is None
            )
        ]

        if matches:
            return matches[-1]

        return None

    def count(self) -> int:
        return len(self.items)
