
from ..models.checklist_item import ChecklistItem


class ChecklistService:
    """
    Manages operational checklist items.
    """

    def __init__(self):
        self.items: list[ChecklistItem] = []


    def add_item(
        self,
        item: ChecklistItem,
    ) -> ChecklistItem:

        self.items.append(item)

        return item


    def get_items(self):

        return list(self.items)
