from ..models.knowledge_entry import KnowledgeEntry



class KnowledgeBaseService:



    def __init__(self):

        self.entries = []



    def add(

        self,

        knowledge_id,

        category,

        observation,

        source,

        confidence,

        usage

    ):


        entry = KnowledgeEntry(

            knowledge_id,

            category,

            observation,

            source,

            confidence,

            usage

        )


        self.entries.append(entry)


        return entry



    def get_all(self):

        return self.entries



    def search(

        self,

        keyword

    ):


        keyword = keyword.lower()


        return [

            entry

            for entry in self.entries

            if keyword in entry.observation.lower()

            or keyword in entry.category.lower()

        ]



    def average_confidence(self):


        if not self.entries:

            return 0


        return round(

            sum(

                entry.confidence

                for entry in self.entries

            )

            /

            len(self.entries)

        )
