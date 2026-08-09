from typing import List


class ResolutionManagementService:
    """
    Manages operational resolutions.
    """


    def __init__(self):

        self.resolutions: List = []


    def create_resolution(
        self,
        resolution,
    ):

        self.resolutions.append(resolution)

        return resolution


    def active_resolutions(self):

        return [
            item
            for item in self.resolutions
            if item.status.value != "VERIFIED"
        ]
