from ..models.operational_finding import OperationalFinding


class OperationalFindingRepository:
    """Persistence for OperationalFinding (AA-013 §4, D-UI-5)."""

    def __init__(self, session=None):
        self.session = session
        self.records = []

    def add(self, finding):
        if self.session:
            self.session.add(finding)
            self.session.commit()
            self.session.refresh(finding)
            return finding

        self.records.append(finding)
        return finding

    def get_all(self):
        if self.session:
            return self.session.query(OperationalFinding).all()

        return self.records

    def get_by_id(self, record_id):
        if self.session:
            return (
                self.session.query(OperationalFinding)
                .filter(OperationalFinding.id == record_id)
                .first()
            )

        for item in self.records:
            if getattr(item, "id", None) == record_id:
                return item

        return None

    def get_by_finding_id(self, finding_id):
        if self.session:
            return (
                self.session.query(OperationalFinding)
                .filter(OperationalFinding.finding_id == finding_id)
                .first()
            )

        for item in self.records:
            if getattr(item, "finding_id", None) == finding_id:
                return item

        return None

    def get_open(self):
        """Every finding not yet RESOLVED -- RAISED and ACKNOWLEDGED both
        count as open per §4.4 ("removed from the bell only when resolved,
        never on view")."""

        return [f for f in self.get_all() if f.status != "RESOLVED"]

    def get_open_by_module(self, module):
        return [f for f in self.get_open() if f.source_module == module]

    def find_open_by_dedupe_key(self, dedupe_key):
        """The finding a detection engine should update instead of
        duplicating, per §4.4. Only considers open findings -- if the same
        underlying condition was previously resolved and recurs, that is a
        new finding, not a reopening of the old one."""

        if not dedupe_key:
            return None

        for finding in self.get_open():
            if finding.dedupe_key == dedupe_key:
                return finding

        return None

    def count_opened_on(self, date_prefix: str) -> int:
        """How many findings already carry this date prefix in their
        finding_id (e.g. "AL-260814") -- used to derive the next sequence
        number. Never guesses at a count independent of what's persisted."""

        return sum(
            1
            for finding in self.get_all()
            if str(finding.finding_id or "").startswith(date_prefix)
        )

    def count_open_by_module(self) -> dict:
        """Per-module unresolved counts for the dashboard nav badges (§4.5)."""

        counts: dict[str, int] = {}
        for finding in self.get_open():
            counts[finding.source_module] = counts.get(finding.source_module, 0) + 1
        return counts
