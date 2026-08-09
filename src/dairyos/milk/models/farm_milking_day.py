from dataclasses import dataclass, field


@dataclass
class FarmMilkingDay:


    date: str

    farm_id: str

    workers: list[str] = field(
        default_factory=list
    )

    sessions_completed: list[str] = field(
        default_factory=list
    )


    def assign_worker(
        self,
        worker: str
    ):

        if worker not in self.workers:

            self.workers.append(
                worker
            )


    def complete_session(
        self,
        session: str
    ):

        if session not in self.sessions_completed:

            self.sessions_completed.append(
                session
            )


    def operational_status(self):

        required = [
            "MORNING",
            "AFTERNOON",
            "EVENING",
        ]

        return all(
            s in self.sessions_completed
            for s in required
        )
