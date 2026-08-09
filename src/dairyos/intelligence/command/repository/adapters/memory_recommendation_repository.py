class MemoryRecommendationRepository:


    def __init__(self):

        self.items = []


    def save(self, recommendation):

        self.items.append(
            recommendation
        )

        return recommendation
