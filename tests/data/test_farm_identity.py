from dairyos.data.farm_identity import (
    FARM_INSTANCE_ID_KEY,
    get_or_create_farm_instance_id,
    set_farm_instance_id,
)


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _Session:
    def __init__(self, existing=None):
        self.existing = existing
        self.statements = []
        self.commits = 0

    def execute(self, statement, params):
        self.statements.append((str(statement), params))
        if len(self.statements) == 1:
            return _Result(self.existing)
        return _Result(None)

    def commit(self):
        self.commits += 1


def test_new_farm_identity_upsert_supplies_required_updated_at():
    session = _Session()

    farm_id = get_or_create_farm_instance_id(session)

    statement, params = session.statements[1]
    assert farm_id == params["value"]
    assert params["key"] == FARM_INSTANCE_ID_KEY
    assert params["updated_at"] is not None
    assert "updated_at" in statement
    assert session.commits == 1


def test_imported_farm_identity_upsert_supplies_required_updated_at():
    session = _Session()

    set_farm_instance_id(session, "imported-farm-id")

    statement, params = session.statements[0]
    assert params == {
        "key": FARM_INSTANCE_ID_KEY,
        "value": "imported-farm-id",
        "updated_at": params["updated_at"],
    }
    assert params["updated_at"] is not None
    assert "updated_at" in statement
    assert session.commits == 1
