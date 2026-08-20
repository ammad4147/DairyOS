# -*- coding: utf-8 -*-
from dairyos.data.database.session import engine
from sqlalchemy import text

print("=== APPLYING FK CONSTRAINT & TRIGGER MIGRATION (STEP-BY-STEP) ===")

statements = [
    # 1. Clean up orphaned foreign keys
    (
        "1. Clean orphaned records",
        """
        UPDATE treatment_record
        SET health_case_id = NULL
        WHERE health_case_id IS NOT NULL
          AND health_case_id NOT IN (SELECT id FROM health_cases);
        """
    ),
    # 2. Drop existing FK constraint if any
    (
        "2. Drop existing constraint",
        """
        ALTER TABLE treatment_record
        DROP CONSTRAINT IF EXISTS fk_treatment_record_health_case_id;
        """
    ),
    # 3. Create FK constraint
    (
        "3. Add FK constraint",
        """
        ALTER TABLE treatment_record
        ADD CONSTRAINT fk_treatment_record_health_case_id
        FOREIGN KEY (health_case_id)
        REFERENCES health_cases (id)
        ON UPDATE CASCADE
        ON DELETE SET NULL;
        """
    ),
    # 4. Create Index
    (
        "4. Create Index on health_case_id",
        """
        CREATE INDEX IF NOT EXISTS ix_treatment_record_health_case_id
        ON treatment_record (health_case_id);
        """
    ),
    # 5. Create Trigger Function
    (
        "5. Create Trigger Function",
        """
        CREATE OR REPLACE FUNCTION sync_health_case_withdrawal_deadline()
        RETURNS TRIGGER AS $func$
        DECLARE
            target_case_id INTEGER;
            max_withdrawal TIMESTAMP WITHOUT TIME ZONE;
        BEGIN
            IF (TG_OP = 'DELETE') THEN
                target_case_id := OLD.health_case_id;
            ELSE
                target_case_id := NEW.health_case_id;
            END IF;

            IF (TG_OP = 'UPDATE' AND OLD.health_case_id IS DISTINCT FROM NEW.health_case_id AND OLD.health_case_id IS NOT NULL) THEN
                SELECT MAX(milk_withdrawal_until)
                INTO max_withdrawal
                FROM treatment_record
                WHERE health_case_id = OLD.health_case_id;

                UPDATE health_cases
                SET withdrawal_until = max_withdrawal
                WHERE id = OLD.health_case_id;
            END IF;

            IF (target_case_id IS NOT NULL) THEN
                SELECT MAX(milk_withdrawal_until)
                INTO max_withdrawal
                FROM treatment_record
                WHERE health_case_id = target_case_id;

                UPDATE health_cases
                SET withdrawal_until = max_withdrawal
                WHERE id = target_case_id;
            END IF;

            RETURN NULL;
        END;
        $func$ LANGUAGE plpgsql;
        """
    ),
    # 6. Bind Trigger
    (
        "6. Bind Trigger to treatment_record",
        """
        DROP TRIGGER IF EXISTS trg_sync_treatment_withdrawal ON treatment_record;
        CREATE TRIGGER trg_sync_treatment_withdrawal
        AFTER INSERT OR UPDATE OF milk_withdrawal_until, health_case_id OR DELETE
        ON treatment_record
        FOR EACH ROW
        EXECUTE FUNCTION sync_health_case_withdrawal_deadline();
        """
    ),
    # 7. One-time backfill
    (
        "7. Sync existing historical records",
        """
        UPDATE health_cases hc
        SET withdrawal_until = sub.max_until
        FROM (
            SELECT health_case_id, MAX(milk_withdrawal_until) AS max_until
            FROM treatment_record
            WHERE health_case_id IS NOT NULL
            GROUP BY health_case_id
        ) sub
        WHERE hc.id = sub.health_case_id
          AND (hc.withdrawal_until IS DISTINCT FROM sub.max_until);
        """
    )
]

with engine.begin() as conn:
    for title, stmt in statements:
        try:
            conn.execute(text(stmt))
            print(f"[OK] {title}")
        except Exception as e:
            print(f"[ERROR] {title}: {e}")
            raise

print("\n>>> ALL MIGRATION STEPS APPLIED SUCCESSFULLY <<<")