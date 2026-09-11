"""Close confirmed Health, Milk and TMR integrity gaps from the 2026-09 audit."""

from alembic import op
import sqlalchemy as sa


revision = "20260912_01"
down_revision = "20260911_01"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _tables() -> set[str]:
    return set(_inspector().get_table_names())


def _columns(table: str) -> set[str]:
    return {column["name"] for column in _inspector().get_columns(table)}


def _foreign_key_names(table: str) -> set[str]:
    return {
        foreign_key.get("name")
        for foreign_key in _inspector().get_foreign_keys(table)
    }


def _assert_case_links_match_animal(connection, table: str) -> None:
    if table not in _tables() or "health_case_id" not in _columns(table):
        return

    mismatches = connection.execute(
        sa.text(
            f"""
            SELECT count(*)
            FROM {table} child
            LEFT JOIN health_cases parent
              ON parent.id = child.health_case_id
            WHERE child.health_case_id IS NOT NULL
              AND (
                    parent.id IS NULL
                    OR parent.animal_id IS DISTINCT FROM child.animal_id
                  )
            """
        )
    ).scalar_one()

    if mismatches:
        raise RuntimeError(
            f"Cannot add same-animal HealthCase constraint to {table}: "
            f"{mismatches} existing linked row(s) have no matching case "
            "or belong to a different animal. Repair the data before "
            "applying this migration."
        )


def _ensure_case_target_unique() -> None:
    if "health_cases" not in _tables():
        return

    existing = {
        constraint.get("name")
        for constraint in _inspector().get_unique_constraints("health_cases")
    }
    if "uq_health_cases_id_animal" not in existing:
        op.create_unique_constraint(
            "uq_health_cases_id_animal",
            "health_cases",
            ["id", "animal_id"],
        )


def _ensure_animal_parentage_fk(column: str, constraint_name: str) -> None:
    if "animal" not in _tables() or column not in _columns("animal"):
        return

    connection = op.get_bind()
    invalid = connection.execute(
        sa.text(
            f"""
            SELECT count(*)
            FROM animal child
            LEFT JOIN animal parent ON parent.animal_id = child.{column}
            WHERE child.{column} IS NOT NULL
              AND parent.animal_id IS NULL
            """
        )
    ).scalar_one()
    if invalid:
        raise RuntimeError(
            f"Cannot add {column} parentage constraint: {invalid} "
            "existing link(s) reference no registered animal."
        )

    for foreign_key in _inspector().get_foreign_keys("animal"):
        if (
            foreign_key.get("referred_table") == "animal"
            and foreign_key.get("constrained_columns") == [column]
            and foreign_key.get("referred_columns") == ["animal_id"]
        ):
            return

    op.create_foreign_key(
        constraint_name,
        "animal",
        "animal",
        [column],
        ["animal_id"],
        ondelete="RESTRICT",
    )


def _ensure_vaccination_table() -> None:
    if "vaccinations" in _tables():
        return

    op.create_table(
        "vaccinations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "animal_id",
            sa.String(),
            sa.ForeignKey("animal.animal_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("vaccine", sa.String(), nullable=False),
        sa.Column("dose", sa.String(), nullable=True),
        sa.Column("administered_date", sa.Date(), nullable=False),
        sa.Column("next_due_date", sa.Date(), nullable=True),
        sa.Column(
            "schedule_status",
            sa.String(),
            nullable=False,
            server_default="UNKNOWN_NEXT_DUE",
        ),
        sa.Column("batch_number", sa.String(), nullable=True),
        sa.Column("veterinarian", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("operator", sa.String(), nullable=False, server_default="API"),
        sa.Column("status", sa.String(), nullable=False, server_default="COMPLETED"),
        sa.Column("source_event_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_vaccinations_animal_id", "vaccinations", ["animal_id"])
    op.create_index("ix_vaccinations_vaccine", "vaccinations", ["vaccine"])
    op.create_index(
        "ix_vaccinations_administered_date",
        "vaccinations",
        ["administered_date"],
    )
    op.create_index(
        "ix_vaccinations_next_due_date",
        "vaccinations",
        ["next_due_date"],
    )
    op.create_index("ix_vaccinations_status", "vaccinations", ["status"])
    op.create_index(
        "uq_vaccinations_source_event_id",
        "vaccinations",
        ["source_event_id"],
        unique=True,
        postgresql_where=sa.text("source_event_id IS NOT NULL"),
    )


def _ensure_same_animal_case_fk(table: str, constraint_name: str) -> None:
    if "health_cases" not in _tables():
        return
    if table not in _tables() or "health_case_id" not in _columns(table):
        return

    if constraint_name not in _foreign_key_names(table):
        op.create_foreign_key(
            constraint_name,
            table,
            "health_cases",
            ["health_case_id", "animal_id"],
            ["id", "animal_id"],
            ondelete="RESTRICT",
        )


def _ensure_tmr_snapshot_uniqueness(connection) -> None:
    if "feed_ration" not in _tables():
        return

    duplicate = connection.execute(
        sa.text(
            """
            SELECT animal_group, effective_date, count(*)
            FROM feed_ration
            WHERE animal_group = 'TMR_DAILY_COST_SNAPSHOT'
            GROUP BY animal_group, effective_date
            HAVING count(*) > 1
            LIMIT 1
            """
        )
    ).first()

    if duplicate is not None:
        raise RuntimeError(
            "Cannot create exactly-once TMR snapshot authority: duplicate "
            f"snapshot rows already exist for {duplicate[1]!s}. Repair the "
            "data before applying this migration."
        )

    existing = {
        index.get("name")
        for index in _inspector().get_indexes("feed_ration")
    }
    if "uq_tmr_daily_cost_snapshot_date" not in existing:
        op.create_index(
            "uq_tmr_daily_cost_snapshot_date",
            "feed_ration",
            ["animal_group", "effective_date"],
            unique=True,
            postgresql_where=sa.text(
                "animal_group = 'TMR_DAILY_COST_SNAPSHOT'"
            ),
        )


def _ensure_correction_history_table() -> None:
    if "milk_production_corrections" in _tables():
        return

    op.create_table(
        "milk_production_corrections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "production_id",
            sa.Integer(),
            sa.ForeignKey("milk_production.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("operator", sa.String(), nullable=False),
        sa.Column("before_json", sa.JSON(), nullable=False),
        sa.Column("after_json", sa.JSON(), nullable=False),
        sa.Column("source_request_id", sa.String(), nullable=True),
        sa.Column("corrected_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_milk_production_corrections_production_id",
        "milk_production_corrections",
        ["production_id"],
    )
    op.create_index(
        "ix_milk_production_corrections_source_request_id",
        "milk_production_corrections",
        ["source_request_id"],
    )


def upgrade() -> None:
    connection = op.get_bind()

    # Validate before DDL: the migration never silently reassigns or drops
    # historical Health links in order to make the new invariant fit.
    if "health_cases" in _tables():
        _assert_case_links_match_animal(connection, "health_observation")
        _assert_case_links_match_animal(connection, "treatment_record")
        _ensure_case_target_unique()
        _ensure_same_animal_case_fk(
            "health_observation",
            "fk_health_observation_case_same_animal",
        )
        _ensure_same_animal_case_fk(
            "treatment_record",
            "fk_treatment_record_case_same_animal",
        )

    _ensure_tmr_snapshot_uniqueness(connection)
    _ensure_correction_history_table()
    _ensure_animal_parentage_fk("dam_id", "fk_animal_dam_same_animal")
    _ensure_animal_parentage_fk("sire_id", "fk_animal_sire_same_animal")
    _ensure_vaccination_table()


def downgrade() -> None:
    raise RuntimeError(
        "Downgrade would remove Milk correction history and integrity "
        "constraints. Restore a verified compatible backup instead."
    )
