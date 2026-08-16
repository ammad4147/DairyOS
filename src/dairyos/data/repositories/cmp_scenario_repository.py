from __future__ import annotations


class CMPScenarioRepository:
    def __init__(self, session, model):
        self.session = session
        self.model = model

    def get_all(self):
        return (
            self.session.query(self.model)
            .order_by(self.model.created_at.desc())
            .all()
        )

    def get_by_scenario_id(self, scenario_id: str):
        return (
            self.session.query(self.model)
            .filter(
                self.model.scenario_id == scenario_id
            )
            .first()
        )
