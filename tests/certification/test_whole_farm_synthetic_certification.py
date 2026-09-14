"""
DairyOS whole-farm synthetic certification.

CERTIFICATION PURPOSE ONLY.

This scenario deliberately exercises production application/API/service
boundaries through the normal pytest application fixture and its governed
disposable PostgreSQL database.

It must never:
- target the installed farm database;
- construct its own production database URL;
- write directly to domain tables to manufacture a PASS;
- bypass semen inventory for insemination;
- fabricate TMR historical authority;
- use Dashboard output as the arithmetic oracle.

Independent expectations are calculated in this test before comparison
with DairyOS projections.

The scenario is intentionally staged. Additional whole-farm stages are
added only after their exact production contracts have been inspected.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest

from dairyos.app import container
from dairyos.farm.reproduction.services.post_calving_return_service import (
    reconcile_due_post_calving_returns,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)

pytestmark = pytest.mark.usefixtures("client")


@dataclass(frozen=True)
class HerdOracle:
    milking: int
    dry: int
    heifer: int
    female_calf: int
    male_calf: int
    bull: int

    @property
    def total(self) -> int:
        return (
            self.milking
            + self.dry
            + self.heifer
            + self.female_calf
            + self.male_calf
            + self.bull
        )



@dataclass(frozen=True)
class SyntheticAnimalSpec:
    key: str
    animal_type: str
    sex: str
    lifecycle_status: str
    expected_category: str
    is_currently_milking: bool = False
    milking_frequency: str | None = None
    breed: str = "Sahiwal"


SYNTHETIC_ANIMALS = (
    SyntheticAnimalSpec(
        key="MILK-THRICE-01",
        animal_type="COW",
        sex="FEMALE",
        lifecycle_status="LACTATING",
        expected_category="Milking",
        is_currently_milking=True,
        milking_frequency="THRICE_DAILY",
    ),
    SyntheticAnimalSpec(
        key="MILK-THRICE-02",
        animal_type="COW",
        sex="FEMALE",
        lifecycle_status="LACTATING",
        expected_category="Milking",
        is_currently_milking=True,
        milking_frequency="THRICE_DAILY",
    ),
    SyntheticAnimalSpec(
        key="MILK-TWICE-01",
        animal_type="COW",
        sex="FEMALE",
        lifecycle_status="LACTATING",
        expected_category="Milking",
        is_currently_milking=True,
        milking_frequency="TWICE_DAILY",
    ),
    SyntheticAnimalSpec(
        key="MILK-THRICE-03",
        animal_type="COW",
        sex="FEMALE",
        lifecycle_status="LACTATING",
        expected_category="Milking",
        is_currently_milking=True,
        milking_frequency="THRICE_DAILY",
    ),
    SyntheticAnimalSpec(
        key="DRY-01",
        animal_type="COW",
        sex="FEMALE",
        lifecycle_status="DRY",
        expected_category="Dry",
    ),
    SyntheticAnimalSpec(
        key="HEIFER-01",
        animal_type="HEIFER",
        sex="FEMALE",
        lifecycle_status="HEIFER",
        expected_category="Heifer",
    ),
    SyntheticAnimalSpec(
        key="FEMALE-CALF-01",
        animal_type="CALF",
        sex="FEMALE",
        lifecycle_status="CALF",
        expected_category="Female Calf",
    ),
    SyntheticAnimalSpec(
        key="MALE-CALF-01",
        animal_type="CALF",
        sex="MALE",
        lifecycle_status="CALF",
        expected_category="Male Calf",
    ),
    SyntheticAnimalSpec(
        key="BULL-01",
        animal_type="BULL",
        sex="MALE",
        lifecycle_status="BULL",
        expected_category="Bull",
    ),
)


def _create_synthetic_herd(client):
    """
    Create the certification herd exclusively through the production
    animal-registration HTTP boundary.

    Returned DairyOS permanent IDs are authoritative. Synthetic labels are
    only test-local handles and are never supplied as permanent animal IDs.
    """

    created_by_key = {}

    for spec in SYNTHETIC_ANIMALS:
        payload = {
            "animal_type": spec.animal_type,
            "breed": spec.breed,
            "sex": spec.sex,
            "lifecycle_status": spec.lifecycle_status,
            "is_currently_milking": spec.is_currently_milking,
        }

        if spec.milking_frequency is not None:
            payload["milking_frequency"] = spec.milking_frequency

        response = client.post(
            "/farm/animals",
            json=payload,
        )

        assert response.status_code in {200, 201}, response.text

        persisted = response.json()

        animal_id = persisted["animal_id"]

        assert animal_id
        assert animal_id not in created_by_key.values()

        # Never accept the synthetic test-local key as DairyOS identity.
        assert animal_id != spec.key

        readback = client.get(
            f"/farm/animals/{animal_id}"
        )

        assert readback.status_code == 200, readback.text

        projected = readback.json()

        assert projected["animal_id"] == animal_id
        assert projected["lifecycle_status"] == spec.lifecycle_status
        assert projected["animal_category"] == spec.expected_category
        assert (
            projected["is_currently_milking"]
            is spec.is_currently_milking
        )

        if spec.is_currently_milking:
            assert (
                projected["milking_frequency"]
                == spec.milking_frequency
            )
        else:
            assert projected["milking_frequency"] is None

        passport = client.get(
            f"/farm/animals/{animal_id}/passport"
        )

        assert passport.status_code == 200, passport.text

        passport_payload = passport.json()

        assert (
            passport_payload["animal"]["animal_id"]
            == animal_id
        )

        created_by_key[spec.key] = animal_id

        _print_reconciliation(
            label=f"ANIMAL {spec.key}",
            input_value=payload,
            expected=spec.expected_category,
            persisted={
                "animal_id": animal_id,
                "lifecycle_status": persisted.get(
                    "lifecycle_status"
                ),
            },
            projected={
                "animal_category": projected.get(
                    "animal_category"
                ),
                "milking_frequency": projected.get(
                    "milking_frequency"
                ),
            },
            calculated=projected["animal_category"],
        )

    assert len(created_by_key) == HERD_ORACLE.total
    assert len(set(created_by_key.values())) == HERD_ORACLE.total

    return created_by_key


def _assert_synthetic_herd_projection(client, created_by_key):
    response = client.get("/farm/animals")

    assert response.status_code == 200, response.text

    animals = response.json()

    created_ids = set(created_by_key.values())

    synthetic_rows = [
        animal
        for animal in animals
        if animal["animal_id"] in created_ids
    ]

    assert len(synthetic_rows) == HERD_ORACLE.total

    counts = {
        "Milking": 0,
        "Dry": 0,
        "Heifer": 0,
        "Female Calf": 0,
        "Male Calf": 0,
        "Bull": 0,
    }

    for animal in synthetic_rows:
        category = animal["animal_category"]

        assert category in counts

        counts[category] += 1

    expected = {
        "Milking": HERD_ORACLE.milking,
        "Dry": HERD_ORACLE.dry,
        "Heifer": HERD_ORACLE.heifer,
        "Female Calf": HERD_ORACLE.female_calf,
        "Male Calf": HERD_ORACLE.male_calf,
        "Bull": HERD_ORACLE.bull,
    }

    assert counts == expected
    assert sum(counts.values()) == HERD_ORACLE.total

    _print_reconciliation(
        label="WHOLE-FARM HERD CATEGORY RECONCILIATION",
        input_value=list(created_by_key.keys()),
        expected=expected,
        persisted={
            "created_animal_ids": sorted(created_ids),
        },
        projected=counts,
        calculated=counts,
    )


@dataclass(frozen=True)
class MilkOracle:
    thrice_daily_liters: tuple[Decimal, ...]
    twice_daily_liters: tuple[Decimal, ...]
    withdrawal_liters: Decimal

    @property
    def total_liters(self) -> Decimal:
        return sum(
            self.thrice_daily_liters + self.twice_daily_liters,
            Decimal("0"),
        )

    @property
    def saleable_liters(self) -> Decimal:
        return self.total_liters - self.withdrawal_liters

    @property
    def milking_animals(self) -> int:
        return (
            len(self.thrice_daily_liters)
            + len(self.twice_daily_liters)
        )

    @property
    def average_per_milking_animal(self) -> Decimal:
        if self.milking_animals == 0:
            raise AssertionError(
                "Synthetic milk oracle requires milking animals."
            )

        return (
            self.total_liters
            / Decimal(self.milking_animals)
        )

    @property
    def thrice_average_liters(self) -> Decimal:
        return (
            sum(self.thrice_daily_liters, Decimal("0"))
            / Decimal(len(self.thrice_daily_liters))
        )

    @property
    def twice_average_liters(self) -> Decimal:
        return (
            sum(self.twice_daily_liters, Decimal("0"))
            / Decimal(len(self.twice_daily_liters))
        )


@dataclass(frozen=True)
class CostOracle:
    feed_cost: Decimal
    opex: Decimal
    milk_liters: Decimal

    @property
    def feed_cost_per_liter(self) -> Decimal:
        if self.milk_liters <= 0:
            raise AssertionError(
                "COP denominator must be authoritative positive milk."
            )

        return self.feed_cost / self.milk_liters

    @property
    def opex_per_liter(self) -> Decimal:
        if self.milk_liters <= 0:
            raise AssertionError(
                "COP denominator must be authoritative positive milk."
            )

        return self.opex / self.milk_liters

    @property
    def cop_per_liter(self) -> Decimal:
        return (
            self.feed_cost + self.opex
        ) / self.milk_liters


HERD_ORACLE = HerdOracle(
    milking=4,
    dry=1,
    heifer=1,
    female_calf=1,
    male_calf=1,
    bull=1,
)


MILK_ORACLE = MilkOracle(
    # Frozen independent complete-day production oracle.
    thrice_daily_liters=(
        Decimal("30"),
        Decimal("27"),
        Decimal("22"),
    ),
    twice_daily_liters=(
        Decimal("21"),
    ),
    withdrawal_liters=Decimal("22"),
)


def _print_reconciliation(
    *,
    label: str,
    input_value,
    expected,
    persisted,
    projected,
    calculated,
):
    delta = None

    if (
        isinstance(expected, (int, float, Decimal))
        and isinstance(calculated, (int, float, Decimal))
    ):
        delta = Decimal(str(calculated)) - Decimal(str(expected))

    print("")
    print(f"=== {label} ===")
    print(f"INPUT      : {input_value}")
    print(f"EXPECTED   : {expected}")
    print(f"PERSISTED  : {persisted}")
    print(f"PROJECTED  : {projected}")
    print(f"CALCULATED : {calculated}")
    print(f"DELTA      : {delta}")
    print(
        "RESULT     : "
        + ("PASS" if expected == calculated else "FAIL")
    )


def _assert_decimal_equal(
    *,
    label: str,
    expected,
    actual,
    places: str = "0.000001",
):
    expected_decimal = Decimal(str(expected))
    actual_decimal = Decimal(str(actual))

    expected_quantized = expected_decimal.quantize(
        Decimal(places)
    )
    actual_quantized = actual_decimal.quantize(
        Decimal(places)
    )

    _print_reconciliation(
        label=label,
        input_value="independent synthetic oracle",
        expected=expected_quantized,
        persisted="see production API state",
        projected="see production projection",
        calculated=actual_quantized,
    )

    assert actual_quantized == expected_quantized


def _assert_disposable_database_contract() -> None:
    """
    Defense in depth.

    tests/conftest.py owns the authoritative disposable-database gate.
    This test adds a visible certification assertion so a future reviewer
    cannot mistake this file for an installed-farm simulation.
    """

    engine = container.repository_factory.session.get_bind()
    url = str(engine.url).lower()

    print("")
    print("=== DATABASE SAFETY ===")
    print(f"Resolved database: {url}")

    assert "dairyos_test" in url
    assert "127.0.0.1" in url or "localhost" in url

    forbidden = (
        "/dairyos?",
        "/dairyos#",
        "/dairyos ",
    )

    assert not any(token in url for token in forbidden)

    print("RESULT     : PASS")



def _record_synthetic_milk_stage(
    client,
    created_animals: dict[str, str],
    operational_date,
) -> dict:
    """Record the frozen 100 L biological Milk oracle."""

    session_plan = {
        "MILK-THRICE-01": (
            ("MORNING", "morning_yield", Decimal("12")),
            ("AFTERNOON", "afternoon_yield", Decimal("10")),
            ("EVENING", "evening_yield", Decimal("8")),
        ),
        "MILK-THRICE-02": (
            ("MORNING", "morning_yield", Decimal("10")),
            ("AFTERNOON", "afternoon_yield", Decimal("9")),
            ("EVENING", "evening_yield", Decimal("8")),
        ),
        "MILK-TWICE-01": (
            ("MORNING", "morning_yield", Decimal("11")),
            ("EVENING", "evening_yield", Decimal("10")),
        ),
        "MILK-THRICE-03": (
            ("MORNING", "morning_yield", Decimal("8")),
            ("AFTERNOON", "afternoon_yield", Decimal("7")),
            ("EVENING", "evening_yield", Decimal("7")),
        ),
    }

    expected_frequencies = {
        "MILK-THRICE-01": "THRICE_DAILY",
        "MILK-THRICE-02": "THRICE_DAILY",
        "MILK-TWICE-01": "TWICE_DAILY",
        "MILK-THRICE-03": "THRICE_DAILY",
    }

    expected_totals = {
        "MILK-THRICE-01": Decimal("30"),
        "MILK-THRICE-02": Decimal("27"),
        "MILK-TWICE-01": Decimal("21"),
        "MILK-THRICE-03": Decimal("22"),
    }

    recorded_sessions = []
    calculated_totals = {}

    for synthetic_key, sessions in session_plan.items():
        animal_id = created_animals[synthetic_key]

        animal_response = client.get(
            f"/farm/animals/{animal_id}"
        )

        assert animal_response.status_code == 200, (
            animal_response.text
        )

        animal = animal_response.json()

        assert animal["animal_id"] == animal_id
        assert (
            animal["milking_frequency"]
            == expected_frequencies[synthetic_key]
        )
        assert animal["is_currently_milking"] is True

        animal_total = Decimal("0")

        for session, yield_field, litres in sessions:
            response = client.post(
                "/farm/milk",
                json={
                    "animal_id": animal_id,
                    "milking_session": session,
                    "production_date": operational_date.isoformat(),
                    "operator": "FC-SIM-08G",
                    yield_field: float(litres),
                },
            )

            assert response.status_code == 200, response.text

            recorded_sessions.append(
                {
                    "synthetic_key": synthetic_key,
                    "animal_id": animal_id,
                    "session": session,
                    "yield_field": yield_field,
                    "litres": litres,
                    "response": response.json(),
                }
            )

            animal_total += litres

        calculated_totals[synthetic_key] = animal_total

    calculated_biological_total = sum(
        calculated_totals.values(),
        Decimal("0"),
    )

    assert len(recorded_sessions) == 11
    assert calculated_totals == expected_totals
    assert calculated_biological_total == Decimal("100")

    ledger_response = client.get(
        "/farm/milk/ledger",
        params={
            "start_date": operational_date.isoformat(),
            "end_date": operational_date.isoformat(),
        },
    )
    assert ledger_response.status_code == 200, ledger_response.text

    summary_response = client.get(
        "/farm/milk/production-summary",
        params={"period": "7d"},
    )
    assert summary_response.status_code == 200, summary_response.text

    next_session = {}

    for synthetic_key in session_plan:
        response = client.get(
            "/farm/milk/next-session",
            params={
                "operational_date": operational_date.isoformat(),
                "animal_id": created_animals[
                    synthetic_key
                ],
            },
        )

        assert response.status_code == 200, response.text
        next_session[synthetic_key] = response.json()

    ledger = ledger_response.json()
    production_rows = ledger["production"]

    assert len(production_rows) == 4

    rows_by_animal = {
        row["animal_id"]: row
        for row in production_rows
    }

    persisted_totals = {}

    for synthetic_key, expected_total in expected_totals.items():
        animal_id = created_animals[synthetic_key]

        assert animal_id in rows_by_animal

        row = rows_by_animal[animal_id]
        persisted_total = Decimal(str(row["total_yield"]))

        assert persisted_total == expected_total
        assert row["status"] == "RECORDED"

        persisted_totals[synthetic_key] = persisted_total

    persisted_biological_total = sum(
        persisted_totals.values(),
        Decimal("0"),
    )

    assert persisted_biological_total == Decimal("100")

    production_summary = summary_response.json()

    assert (
        production_summary["data_status"]
        == "LIVE_PERSISTED_DATA"
    )

    summary_kpis = production_summary["kpis"]

    summary_total = Decimal(
        str(summary_kpis["total_production_liters"])
    )
    summary_average_per_cow = Decimal(
        str(summary_kpis["average_per_cow_liters"])
    )
    summary_morning = Decimal(
        str(summary_kpis["morning_liters"])
    )
    summary_afternoon = Decimal(
        str(summary_kpis["afternoon_liters"])
    )
    summary_evening = Decimal(
        str(summary_kpis["evening_liters"])
    )

    assert summary_total == Decimal("100")
    assert summary_average_per_cow == Decimal("25")
    assert summary_morning == Decimal("41")
    assert summary_afternoon == Decimal("26")
    assert summary_evening == Decimal("33")

    dashboard_response = client.get("/dashboard")
    assert dashboard_response.status_code == 200, (
        dashboard_response.text
    )

    dashboard = dashboard_response.json()
    dashboard_milk = dashboard["milk"]
    dashboard_animals = dashboard["animals"]
    dashboard_herd_metrics = dashboard_animals["herd_metrics"]

    dashboard_daily_total = Decimal(
        str(
            dashboard_milk["average_yield_per_cow"]
            * dashboard_milk["current_milking_count"]
        )
    )
    dashboard_average = Decimal(
        str(
            dashboard_herd_metrics[
                "average_yield_milking_animals_liters"
            ]
        )
    )

    assert dashboard_daily_total == Decimal("100")
    assert dashboard_average == Decimal("25")
    assert Decimal(
        str(dashboard_milk["average_yield_per_cow"])
    ) == Decimal("25")
    assert dashboard_milk["current_milking_count"] == 4

    extremes = dashboard_milk["production_extremes"]
    cohorts = extremes["cohorts"]

    assert extremes["population_count"] == 4
    assert (
        cohorts["THRICE_DAILY"]["population_count"]
        == 3
    )
    assert (
        cohorts["TWICE_DAILY"]["population_count"]
        == 1
    )

    thrice_highest = cohorts["THRICE_DAILY"]["highest"]
    thrice_lowest = cohorts["THRICE_DAILY"]["lowest"]
    twice_highest = cohorts["TWICE_DAILY"]["highest"]
    twice_lowest = cohorts["TWICE_DAILY"]["lowest"]

    assert [
        Decimal(str(row["total_litres"]))
        for row in thrice_highest
    ] == [Decimal("30")]

    assert [
        Decimal(str(row["total_litres"]))
        for row in thrice_lowest
    ] == [Decimal("22")]

    assert twice_highest == []
    assert twice_lowest == []

    thrice_ids = {
        row["animal_id"]
        for row in (
            thrice_highest
            + thrice_lowest
        )
    }

    twice_ids = {
        row["animal_id"]
        for row in (
            twice_highest
            + twice_lowest
        )
    }

    assert thrice_ids.isdisjoint(twice_ids)

    passport_totals = {}

    for synthetic_key in session_plan:
        animal_id = created_animals[
            synthetic_key
        ]

        passport_response = client.get(
            f"/farm/animals/{animal_id}/passport"
        )

        assert passport_response.status_code == 200, (
            passport_response.text
        )

        passport = passport_response.json()

        assert (
            passport["animal"]["animal_id"]
            == animal_id
        )

        milk_history = passport["history"]["milk"]

        assert len(milk_history) == 1
        assert passport["record_counts"]["milk"] == 1

        passport_total = Decimal(
            str(milk_history[0]["total_yield"])
        )

        assert (
            passport_total
            == expected_totals[synthetic_key]
        )

        passport_totals[synthetic_key] = passport_total

    return {
        "operational_date": operational_date.isoformat(),
        "expected_session_count": 11,
        "recorded_sessions": recorded_sessions,
        "expected_animal_totals": expected_totals,
        "calculated_animal_totals": calculated_totals,
        "persisted_animal_totals": persisted_totals,
        "passport_animal_totals": passport_totals,
        "expected_biological_total": Decimal("100"),
        "calculated_biological_total": (
            calculated_biological_total
        ),
        "persisted_biological_total": (
            persisted_biological_total
        ),
        "summary_total": summary_total,
        "summary_average_per_cow": (
            summary_average_per_cow
        ),
        "dashboard_daily_total": dashboard_daily_total,
        "dashboard_average": dashboard_average,
        "ledger": ledger,
        "production_summary": production_summary,
        "dashboard": dashboard,
        "production_extremes": extremes,
        "next_session": next_session,
    }


def _record_synthetic_feed_tmr_stage(
    client,
    *,
    operational_date: date,
):
    """
    SIM-F: exercise the real Feed/TMR production paths.

    Authorities proved here:
    - all six governed herd categories use the active Animal Register;
    - Milking and Dry category costs use their governed stage averages;
    - five timestamped feeding events satisfy daily feed supervision;
    - the daily TMR snapshot is immutable/idempotent;
    - veterinary review is not calculation authority.

    Finance feed-purchase price authority is intentionally deferred to SIM-$.
    Controlled MANUAL stage prices are used here so TMR arithmetic can be
    independently certified without fabricating Finance rows.
    """

    stage_oracle = {
        "early_milking": Decimal("400"),
        "mid_milking": Decimal("500"),
        "late_milking": Decimal("600"),
        "far_off": Decimal("250"),
        "close_up": Decimal("350"),
        "heifer_growth": Decimal("250"),
        "calf_starter": Decimal("150"),
        "bull": Decimal("350"),
    }

    # Read the governed catalog from the production API before saving any
    # synthetic stage. A stage save is merged against the governed catalog:
    # omitted ingredients retain their stage defaults. Therefore every
    # governed ingredient must be explicit for deterministic certification.
    initial_response = client.get("/farm/tmr")
    assert initial_response.status_code == 200, initial_response.text
    initial_tmr = initial_response.json()

    governed_ingredients = initial_tmr["ingredients"]

    assert governed_ingredients
    assert any(
        row["catalog_name"] == "Corn / Maize Silage"
        for row in governed_ingredients
    )

    # One controlled kg/head/day of Corn / Maize Silage carries the entire
    # synthetic stage cost. Every other governed ingredient is explicitly
    # zeroed so no production default can contribute hidden cost.
    for stage, expected_cost in stage_oracle.items():
        controlled_ingredients = []

        for ingredient in governed_ingredients:
            name = ingredient["catalog_name"]
            is_oracle_ingredient = (
                name == "Corn / Maize Silage"
            )

            controlled_ingredients.append(
                {
                    "catalog_name": name,
                    "quantity": (
                        1 if is_oracle_ingredient else 0
                    ),
                    "dose_unit": ingredient["dose_unit"],
                    "fallback_price_per_kg": (
                        float(expected_cost)
                        if is_oracle_ingredient
                        else 0.0
                    ),
                    "price_source": "MANUAL",
                }
            )

        response = client.post(
            "/farm/tmr/stages",
            json={
                "stage": stage,
                "ingredients": controlled_ingredients,
                "operator": "FC-SIM",
            },
        )

        assert response.status_code == 200, response.text

        body = response.json()

        assert body["saved"] is True
        assert body["stage"] == stage

        saved_stage = body["summary"]["stages"][stage]

        assert (
            Decimal(str(saved_stage["cost_per_head_day"]))
            == expected_cost
        )

        priced_rows = saved_stage["ingredients"]

        corn = next(
            row
            for row in priced_rows
            if row["catalog_name"] == "Corn / Maize Silage"
        )

        assert Decimal(str(corn["quantity"])) == Decimal("1")
        assert corn["selected_price_source"] == "MANUAL"
        assert corn["price_source"] == "MANUAL"
        assert (
            Decimal(str(corn["price_per_kg"]))
            == expected_cost
        )
        assert (
            Decimal(str(corn["cost_per_head_day"]))
            == expected_cost
        )

        for row in priced_rows:
            if row["catalog_name"] == "Corn / Maize Silage":
                continue

            assert Decimal(str(row["quantity"])) == Decimal("0")
            assert (
                Decimal(str(row["cost_per_head_day"]))
                == Decimal("0")
            )

    live_response = client.get("/farm/tmr")
    assert live_response.status_code == 200, live_response.text
    live = live_response.json()

    expected_counts = {
        "Milking": 4,
        "Dry": 1,
        "Heifer": 1,
        "Female Calf": 1,
        "Male Calf": 1,
        "Bull": 1,
    }

    assert live["herd_counts"] == expected_counts

    categories = {
        row["category"]: row
        for row in live["categories"]
    }

    expected_per_head = {
        "Milking": Decimal("500"),
        "Dry": Decimal("300"),
        "Heifer": Decimal("250"),
        "Female Calf": Decimal("150"),
        "Male Calf": Decimal("150"),
        "Bull": Decimal("350"),
    }

    expected_category_cost = {
        "Milking": Decimal("2000"),
        "Dry": Decimal("300"),
        "Heifer": Decimal("250"),
        "Female Calf": Decimal("150"),
        "Male Calf": Decimal("150"),
        "Bull": Decimal("350"),
    }

    for category, expected_count in expected_counts.items():
        row = categories[category]

        assert int(row["animal_count"]) == expected_count
        assert (
            row["population_authority"]
            == "ACTIVE_ANIMAL_REGISTER"
        )

        actual_per_head = Decimal(
            str(row["cost_per_head_day"])
        )
        actual_category_cost = Decimal(
            str(row["category_cost_per_day"])
        )

        assert actual_per_head == expected_per_head[category]
        assert (
            actual_category_cost
            == expected_category_cost[category]
        )

    expected_whole_herd_cost = Decimal("3200")

    live_whole_herd_cost = Decimal(
        str(live["total_herd_feed_cost_per_day"])
    )

    assert live_whole_herd_cost == expected_whole_herd_cost

    # Operational feeding supervision is deliberately separate from TMR
    # formulation/cost authority. Record exactly five timestamped events.
    feed_event_times = (6, 9, 12, 15, 18)

    for hour in feed_event_times:
        response = client.post(
            "/farm/feed/records",
            json={
                "group_or_pen": "WHOLE_HERD",
                "feed_type": "SILAGE",
                "quantity_kg": 1,
                "feeding_date": datetime.combine(
                    operational_date,
                    time(hour=hour),
                ).isoformat(),
                "notes": "FC-SIM five-event supervision",
            },
        )
        assert response.status_code == 200, response.text

    daily_status_response = client.get(
        "/farm/feed/daily-status"
    )
    assert (
        daily_status_response.status_code == 200
    ), daily_status_response.text

    daily_status = daily_status_response.json()

    assert daily_status["feeding_event_count"] == 5
    assert daily_status["minimum_required_events"] == 5
    assert daily_status["remaining_events"] == 0
    assert daily_status["complete"] is True
    assert daily_status["last_event_at"] is not None

    records_response = client.get("/farm/feed/records")
    assert records_response.status_code == 200, records_response.text

    feed_records = records_response.json()

    synthetic_records = [
        row
        for row in feed_records
        if row.get("group_or_pen") == "WHOLE_HERD"
        and row.get("notes") == "FC-SIM five-event supervision"
    ]

    assert len(synthetic_records) == 5

    # The operational event itself must not invent a historical price.
    # Finance feed-purchase authority is tested later in SIM-$.
    assert all(
        row.get("cost_basis") == "UNPRICED"
        for row in synthetic_records
    )

    # Use the same production locking function used by the scheduler. This is
    # not direct state fabrication: the function materialises a normal
    # FeedRation-backed immutable authority through the production service.
    from dairyos.api.tmr import lock_daily_tmr_cost_snapshot

    first_lock = lock_daily_tmr_cost_snapshot(
        container.repository_factory,
        operational_date=operational_date,
    )

    assert first_lock["locked"] is True
    assert first_lock["created"] is True
    assert (
        first_lock["operational_date"]
        == operational_date.isoformat()
    )
    assert first_lock["herd_counts"] == expected_counts
    assert Decimal(
        str(first_lock["total_herd_feed_cost_per_day"])
    ) == expected_whole_herd_cost

    first_record_id = first_lock["record_id"]

    second_lock = lock_daily_tmr_cost_snapshot(
        container.repository_factory,
        operational_date=operational_date,
    )

    assert second_lock["locked"] is True
    assert second_lock["created"] is False
    assert second_lock["record_id"] == first_record_id
    assert second_lock["herd_counts"] == expected_counts
    assert Decimal(
        str(second_lock["total_herd_feed_cost_per_day"])
    ) == expected_whole_herd_cost

    history_response = client.get("/farm/tmr/history?days=1")
    assert history_response.status_code == 200, history_response.text

    history = history_response.json()
    assert history["status"] == "HAS_DATA"

    matching_days = [
        row
        for row in history["records"]
        if row["date"] == operational_date.isoformat()
    ]

    assert len(matching_days) == 1

    persisted_day = matching_days[0]
    assert persisted_day["status"] == "CALCULATED"

    persisted_snapshot = persisted_day["calculation"]

    assert persisted_snapshot["record_id"] == first_record_id
    assert persisted_snapshot["herd_counts"] == expected_counts

    persisted_whole_herd_cost = Decimal(
        str(
            persisted_snapshot[
                "total_herd_feed_cost_per_day"
            ]
        )
    )

    assert persisted_whole_herd_cost == expected_whole_herd_cost

    # History must also retain the five operational feeding events.
    assert persisted_day["feed_consumed"]["records"] == 5
    assert Decimal(
        str(persisted_day["feed_consumed"]["quantity_kg"])
    ) == Decimal("5")

    return {
        "expected_counts": expected_counts,
        "expected_per_head": expected_per_head,
        "expected_category_cost": expected_category_cost,
        "expected_whole_herd_cost": expected_whole_herd_cost,
        "live_whole_herd_cost": live_whole_herd_cost,
        "persisted_whole_herd_cost": persisted_whole_herd_cost,
        "feeding_event_count": int(
            daily_status["feeding_event_count"]
        ),
        "snapshot_record_id": first_record_id,
    }


def _record_synthetic_finance_stage(
    client,
    *,
    operational_date: date,
):
    """
    SIM-$: exercise Finance through governed production APIs.

    No FinancialTransaction, SemenLot, or stock-movement row is
    manufactured directly by this certification harness.
    """

    transaction_date = operational_date.isoformat()

    def post_finance(payload):
        response = client.post(
            "/farm/finance-ledger",
            json=payload,
        )
        assert response.status_code == 200, response.text
        return response.json()

    milk_sale = post_finance(
        {
            "transaction_type": "INCOME",
            "category": "MILK_SALES",
            "quantity": 78,
            "unit": "L",
            "unit_rate": 150,
            "transaction_date": transaction_date,
            "payment_method": "CASH",
            "counterparty": "FC-SIM Milk Buyer",
            "reference": "FC-SIM-MILK-SALE",
            "notes": "FC-SIM governed milk sale",
            "status": "RECEIVED",
            "currency": "PKR",
        }
    )

    assert Decimal(str(milk_sale["quantity"])) == Decimal("78")
    assert Decimal(str(milk_sale["unit_rate"])) == Decimal("150")
    assert Decimal(str(milk_sale["amount"])) == Decimal("11700")
    assert milk_sale["status"] == "RECEIVED"

    opex = post_finance(
        {
            "transaction_type": "EXPENSE",
            "master_category": "OPEX",
            "sub_category": "Routine Vet Fees / Consultation",
            "amount": 2000,
            "transaction_date": transaction_date,
            "payment_method": "CASH",
            "counterparty": "FC-SIM Veterinarian",
            "reference": "FC-SIM-OPEX",
            "notes": "FC-SIM direct governed OPEX",
            "status": "PAID",
            "currency": "PKR",
            "cop_classification": "OPEX",
            "cop_attribution_method": "DIRECT",
            "cop_service_date": transaction_date,
        }
    )

    assert Decimal(str(opex["amount"])) == Decimal("2000")
    assert opex["master_category"] == "OPEX"
    assert opex["cop_classification"] == "OPEX"
    assert opex["cop_attribution_method"] == "DIRECT"

    equipment = post_finance(
        {
            "transaction_type": "EXPENSE",
            "master_category": "OPEX",
            "sub_category": "Equipment Purchase",
            "custom_specification": "FC-SIM Milk Pump",
            "amount": 50000,
            "transaction_date": transaction_date,
            "payment_method": "CASH",
            "counterparty": "FC-SIM Equipment Supplier",
            "reference": "FC-SIM-EQUIPMENT",
            "notes": "FC-SIM equipment purchase",
            "status": "PAID",
            "currency": "PKR",
        }
    )

    assert Decimal(str(equipment["amount"])) == Decimal("50000")
    assert equipment["sub_category"] == "Equipment Purchase"
    assert equipment["cop_classification"] == "NON_OPEX"

    owner_withdrawal = post_finance(
        {
            "transaction_type": "OWNER_WITHDRAWAL",
            "amount": 5000,
            "transaction_date": transaction_date,
            "payment_method": "CASH",
            "counterparty": "FC-SIM Owner",
            "reference": "FC-SIM-OWNER-WITHDRAWAL",
            "notes": "FC-SIM financing outflow",
            "status": "PAID",
            "currency": "PKR",
        }
    )

    assert (
        owner_withdrawal["transaction_type"]
        == "OWNER_WITHDRAWAL"
    )
    assert Decimal(
        str(owner_withdrawal["amount"])
    ) == Decimal("5000")

    owner_investment = post_finance(
        {
            "transaction_type": "OWNER_INVESTMENT",
            "category": "OWNER_INVESTMENT",
            "amount": 10000,
            "transaction_date": transaction_date,
            "payment_method": "CASH",
            "counterparty": "FC-SIM Owner",
            "reference": "FC-SIM-OWNER-INVESTMENT",
            "notes": "FC-SIM financing inflow",
            "status": "RECEIVED",
            "currency": "PKR",
        }
    )

    assert (
        owner_investment["transaction_type"]
        == "OWNER_INVESTMENT"
    )
    assert Decimal(
        str(owner_investment["amount"])
    ) == Decimal("10000")

    semen_purchase = post_finance(
        {
            "transaction_type": "EXPENSE",
            "master_category": "OPEX",
            "sub_category": "Semen Straws (Sexed / Conventional)",
            "quantity": 5,
            "unit": "straws",
            "unit_rate": 1000,
            "transaction_date": transaction_date,
            "payment_method": "CASH",
            "counterparty": "FC-SIM Genetics Supplier",
            "reference": "FC-SIM-SEMEN",
            "notes": "FC-SIM purchased semen authority",
            "status": "PAID",
            "currency": "PKR",
            "semen_type": "SEXED",
            "sire_code": "FC-SIM-SIRE-001",
            "semen_batch_number": "FC-SIM-BATCH-001",
        }
    )

    assert Decimal(
        str(semen_purchase["quantity"])
    ) == Decimal("5")

    assert Decimal(
        str(semen_purchase["unit_rate"])
    ) == Decimal("1000")

    assert Decimal(
        str(semen_purchase["amount"])
    ) == Decimal("5000")

    finance_response = client.get(
        "/farm/finance-ledger",
    )
    assert (
        finance_response.status_code == 200
    ), finance_response.text

    finance_payload = finance_response.json()

    if isinstance(finance_payload, dict):
        finance_rows = (
            finance_payload.get("transactions")
            or finance_payload.get("rows")
            or finance_payload.get("ledger")
            or finance_payload.get("data")
            or []
        )
    else:
        finance_rows = finance_payload

    assert isinstance(finance_rows, list), finance_payload

    expected_finance_ids = {
        int(milk_sale["id"]),
        int(opex["id"]),
        int(equipment["id"]),
        int(owner_withdrawal["id"]),
        int(owner_investment["id"]),
        int(semen_purchase["id"]),
    }

    projected_finance_ids = {
        int(row["id"])
        for row in finance_rows
        if row.get("id") is not None
    }

    assert expected_finance_ids <= projected_finance_ids, {
        "expected": sorted(expected_finance_ids),
        "projected": sorted(projected_finance_ids),
    }

    semen_response = client.get(
        "/farm/breeding/semen-stock",
    )
    assert (
        semen_response.status_code == 200
    ), semen_response.text

    semen_stock = semen_response.json()
    semen_lots = semen_stock.get("lots") or []

    matching_lots = [
        row
        for row in semen_lots
        if int(
            row.get("purchase_transaction_id") or 0
        ) == int(semen_purchase["id"])
    ]

    assert len(matching_lots) == 1, semen_stock

    semen_lot = matching_lots[0]

    assert semen_lot["semen_type"] == "SEXED"
    assert int(semen_lot["available_straws"]) == 5
    assert bool(semen_lot["active"]) is True

    semen_summary = semen_stock["summary"]

    assert int(
        semen_summary["available_straws"]
    ) == 5

    assert int(
        semen_summary["sexed_available"]
    ) == 5

    assert int(
        semen_summary["conventional_available"]
    ) == 0

    milk_ledger_response = client.get(
        "/farm/milk/ledger",
        params={
            "start_date": operational_date.isoformat(),
            "end_date": operational_date.isoformat(),
        },
    )

    assert (
        milk_ledger_response.status_code == 200
    ), milk_ledger_response.text

    milk_ledger = milk_ledger_response.json()

    dispositions = (
        milk_ledger.get("dispositions")
        or milk_ledger.get("milk_dispositions")
        or []
    )

    expected_sale_id = (
        "FIN-" + str(milk_sale["id"])
    )

    sold_rows = [
        row
        for row in dispositions
        if row.get("disposition_type") == "SOLD"
        and row.get("sale_id") == expected_sale_id
    ]

    assert len(sold_rows) == 1, milk_ledger

    sold = sold_rows[0]

    assert Decimal(
        str(sold["quantity_litres"])
    ) == Decimal("78")

    assert Decimal(
        str(sold["amount_due"])
    ) == Decimal("11700")

    assert Decimal(
        str(sold["amount_received"])
    ) == Decimal("11700")

    return {
        "milk_sale": milk_sale,
        "opex": opex,
        "equipment": equipment,
        "owner_withdrawal": owner_withdrawal,
        "owner_investment": owner_investment,
        "semen_purchase": semen_purchase,
    }


def _record_synthetic_health_stage(
    client,
    created_animals: dict[str, str],
    *,
    operational_clock: dict[str, date],
):
    """SIM-H: exercise a linked clinical case through resolution.

    The scenario uses only the governed health-case, observation, treatment,
    summary, and passport boundaries. Treatment timestamps remain production
    timestamps; the independent oracle is the requested three-day withdrawal
    interval and the explicit operator-entered follow-up date.
    """

    animal_id = created_animals["MILK-THRICE-01"]
    health_date = datetime.now().astimezone().date()
    operational_clock["value"] = health_date

    def get_json(path: str, **kwargs):
        response = client.get(path, **kwargs)
        assert response.status_code == 200, response.text
        return response.json()

    case_response = client.post(
        "/farm/health-cases",
        json={
            "animal_id": animal_id,
            "severity": "SEVERE",
            "diagnosis": "FC-SIM Mastitis",
            "notes": "FC-SIM linked clinical case",
            "follow_up_due_at": datetime.combine(
                health_date,
                time(hour=12),
            ).isoformat(),
            "operator": "FC-SIM Health Operator",
        },
    )
    assert case_response.status_code == 200, case_response.text
    case = case_response.json()
    case_id = int(case["id"])
    case_code = case["case_id"]
    assert case_code.startswith(f"HL-{health_date.strftime('%y%m%d')}-")
    assert case["animal_id"] == animal_id
    assert case["status"] == "OPEN"
    assert case["withdrawal_until"] is None

    observation_response = client.post(
        "/farm/health-observations",
        json={
            "animal_id": animal_id,
            "observation": "Elevated temperature and reduced appetite",
            "severity": "SEVERE",
            "health_case_id": case_id,
            "operator": "FC-SIM Health Operator",
        },
    )
    assert observation_response.status_code == 200, observation_response.text
    observation = observation_response.json()
    assert observation["animal_id"] == animal_id
    assert observation["health_case_id"] == case_id

    treatment_response = client.post(
        "/farm/treatments",
        json={
            "animal_id": animal_id,
            "medicine": "FC-SIM-MASTITIS-MEDICINE",
            "diagnosis": "FC-SIM Mastitis",
            "dose": "10 ml",
            "treated_by": "FC-SIM Veterinarian",
            "milk_withdrawal_days": 3,
            "health_case_id": case_id,
            "notes": "FC-SIM withdrawal-controlled treatment",
            "operator": "FC-SIM Health Operator",
        },
    )
    assert treatment_response.status_code == 200, treatment_response.text
    treatment = treatment_response.json()
    assert treatment["animal_id"] == animal_id
    assert int(treatment["health_case_id"]) == case_id
    assert treatment["withdrawal_source"] == "manual_override"
    assert float(treatment["milk_withdrawal_days"]) == 3.0

    treated_at = datetime.fromisoformat(
        str(treatment["treated_at"]).replace("Z", "+00:00")
    )
    withdrawal_until = datetime.fromisoformat(
        str(treatment["milk_withdrawal_until"]).replace("Z", "+00:00")
    )
    assert withdrawal_until - treated_at == timedelta(days=3)

    case_with_records = get_json(f"/farm/health-cases/{case_code}")
    assert case_with_records["status"] == "OPEN"
    assert len(case_with_records["observations"]) == 1
    assert case_with_records["observations"][0]["observation"] == (
        "Elevated temperature and reduced appetite"
    )
    assert len(case_with_records["treatments"]) == 1
    assert case_with_records["treatments"][0]["milk_withdrawal_until"]
    assert str(case_with_records["withdrawal_until"])[:10] == str(
        treatment["milk_withdrawal_until"]
    )[:10]

    summary_open = get_json("/farm/health/summary")
    assert summary_open["activeClinicalCases"] == 1
    assert summary_open["activeSickAnimals"] == 1
    assert summary_open["followupsDue"] == 1
    assert summary_open["withdrawalAnimals"] == 1

    passport_open = get_json(
        f"/farm/animals/{animal_id}/passport",
        params={"as_of_date": health_date.isoformat()},
    )
    health_state_open = passport_open["health_state"]
    assert health_state_open["summary"]["open_case_count"] == 1
    assert health_state_open["summary"]["active_withdrawal"] is True
    assert health_state_open["open_cases"][0]["case_id"] == case_code
    assert health_state_open["active_withdrawals"]

    resolve_response = client.post(
        f"/farm/health-cases/{case_code}/resolve",
        json={
            "resolution": "Recovered after FC-SIM treatment",
            "resolved_by": "FC-SIM Veterinarian",
            "operator": "FC-SIM Health Operator",
        },
    )
    assert resolve_response.status_code == 200, resolve_response.text
    resolved = resolve_response.json()
    assert resolved["status"] == "RESOLVED"
    assert resolved["resolution"] == "Recovered after FC-SIM treatment"
    assert resolved["resolved_by"] == "FC-SIM Veterinarian"
    assert resolved["resolved_at"] is not None

    case_after_resolution = get_json(f"/farm/health-cases/{case_code}")
    assert case_after_resolution["status"] == "RESOLVED"
    assert case_after_resolution["withdrawal_until"] == case_with_records[
        "withdrawal_until"
    ]

    summary_resolved = get_json("/farm/health/summary")
    assert summary_resolved["activeClinicalCases"] == 0
    assert summary_resolved["activeSickAnimals"] == 0
    assert summary_resolved["followupsDue"] == 0
    assert summary_resolved["withdrawalAnimals"] == 1

    passport_resolved = get_json(
        f"/farm/animals/{animal_id}/passport",
        params={"as_of_date": health_date.isoformat()},
    )
    health_state_resolved = passport_resolved["health_state"]
    assert health_state_resolved["summary"]["open_case_count"] == 0
    assert health_state_resolved["summary"]["active_withdrawal"] is True
    assert health_state_resolved["active_withdrawals"]

    return {
        "animal_id": animal_id,
        "case_id": case_id,
        "case_code": case_code,
        "health_date": health_date,
        "withdrawal_days": 3,
        "withdrawal_until": str(treatment["milk_withdrawal_until"]),
        "open_summary": {
            "active_cases": summary_open["activeClinicalCases"],
            "active_sick_animals": summary_open["activeSickAnimals"],
            "followups_due": summary_open["followupsDue"],
            "withdrawal_animals": summary_open["withdrawalAnimals"],
        },
        "resolved_summary": {
            "active_cases": summary_resolved["activeClinicalCases"],
            "active_sick_animals": summary_resolved["activeSickAnimals"],
            "followups_due": summary_resolved["followupsDue"],
            "withdrawal_animals": summary_resolved["withdrawalAnimals"],
        },
        "passport_withdrawal_active_after_resolution": (
            health_state_resolved["summary"]["active_withdrawal"]
        ),
    }


def _record_synthetic_vaccination_stage(
    client,
    created_animals: dict[str, str],
    *,
    operational_clock: dict[str, date],
):
    """SIM-V: schedule and endorse vaccination occurrences.

    The stage follows the operator's schedule-first workflow. Its independent
    oracle keeps one future occurrence visible in the vaccination summary but
    absent from dashboard attention, while a same-day occurrence is shown as
    actionable and can be marked given without creating a duplicate history
    row.
    """

    animal_id = created_animals["FEMALE-CALF-01"]
    due_date = operational_clock["value"]
    future_date = due_date + timedelta(days=7)
    vaccine = "FC-SIM-CORE-VACCINE"

    def get_json(path: str, **kwargs):
        response = client.get(path, **kwargs)
        assert response.status_code == 200, response.text
        return response.json()

    schedule_response = client.post(
        f"/farm/animals/{animal_id}/vaccinations/schedule-batch",
        json={
            "animal_id": animal_id,
            "operator": "FC-SIM Vaccination Scheduler",
            "occurrences": [
                {
                    "vaccine": vaccine,
                    "dose": "2 ml",
                    "scheduled_date": due_date.isoformat(),
                    "veterinarian": "FC-SIM Vaccination Veterinarian",
                    "notes": "FC-SIM due-today schedule-first occurrence",
                },
                {
                    "vaccine": vaccine,
                    "dose": "2 ml",
                    "scheduled_date": future_date.isoformat(),
                    "veterinarian": "FC-SIM Vaccination Veterinarian",
                    "notes": "FC-SIM future schedule-first occurrence",
                },
            ],
        },
    )
    assert schedule_response.status_code == 200, schedule_response.text
    scheduled = schedule_response.json()
    assert scheduled["animal_id"] == animal_id
    assert scheduled["count"] == 2
    occurrences = scheduled["occurrences"]
    assert len(occurrences) == 2
    due_occurrence = next(
        row for row in occurrences if row["next_due_date"] == due_date.isoformat()
    )
    future_occurrence = next(
        row
        for row in occurrences
        if row["next_due_date"] == future_date.isoformat()
    )
    occurrence_id = int(due_occurrence["id"])
    future_occurrence_id = int(future_occurrence["id"])
    for occurrence in occurrences:
        assert occurrence["animal_id"] == animal_id
        assert occurrence["vaccine"] == vaccine
        assert occurrence["administered_date"] is None
        assert occurrence["schedule_status"] == "SCHEDULED"

    history_before = get_json(
        f"/farm/animals/{animal_id}/vaccinations"
    )
    matching_before = [
        row
        for row in history_before
        if row.get("id") in {occurrence_id, future_occurrence_id}
    ]
    assert len(matching_before) == 2
    assert all(row["administered_date"] is None for row in matching_before)
    assert {
        row["next_due_date"] for row in matching_before
    } == {due_date.isoformat(), future_date.isoformat()}

    summary_future = get_json("/farm/vaccination/summary")
    assert summary_future["vaccinationsRecorded"] == 0
    assert summary_future["vaccinationsOverdue"] == 0
    assert summary_future["vaccinationsDueNext30Days"] == 1
    future_upcoming = [
        row
        for row in summary_future["upcomingVaccinations"]
        if row.get("vaccination_occurrence_id") == future_occurrence_id
    ]
    assert len(future_upcoming) == 1
    assert future_upcoming[0]["due_state"] == "SCHEDULED"
    assert future_upcoming[0]["next_due_date"] == future_date.isoformat()
    due_upcoming = [
        row
        for row in summary_future["upcomingVaccinations"]
        if row.get("vaccination_occurrence_id") == occurrence_id
    ]
    assert len(due_upcoming) == 1
    assert due_upcoming[0]["due_state"] == "DUE_TODAY"

    dashboard_future = get_json("/dashboard")
    assert dashboard_future["vaccination"]["due"] == 1
    assert [
        row
        for row in dashboard_future["vaccination"]["due_animals"]
        if row.get("vaccination_occurrence_id") == future_occurrence_id
    ] == []
    due_rows = [
        row
        for row in dashboard_future["vaccination"]["due_animals"]
        if row.get("vaccination_occurrence_id") == occurrence_id
    ]
    assert len(due_rows) == 1
    assert due_rows[0]["due_state"] == "DUE_TODAY"

    administer_response = client.post(
        (
            f"/farm/animals/{animal_id}/vaccinations/"
            f"{occurrence_id}/administer"
        ),
        json={
            "administered_date": due_date.isoformat(),
            "operator": "FC-SIM Vaccination Operator",
            "veterinarian": "FC-SIM Vaccination Veterinarian",
            "notes": "FC-SIM marked given from scheduled row",
        },
    )
    assert administer_response.status_code == 200, administer_response.text
    administered = administer_response.json()
    assert int(administered["id"]) == occurrence_id
    assert administered["administered_date"] == due_date.isoformat()
    assert administered["next_due_date"] == due_date.isoformat()
    assert administered["schedule_status"] == "ADMINISTERED"

    history_after = get_json(
        f"/farm/animals/{animal_id}/vaccinations"
    )
    matching_after = [
        row for row in history_after if row.get("id") == occurrence_id
    ]
    assert len(matching_after) == 1
    assert matching_after[0]["administered_date"] == due_date.isoformat()
    assert matching_after[0]["next_due_date"] == due_date.isoformat()
    assert matching_after[0]["schedule_status"] == "ADMINISTERED"
    future_after = [
        row
        for row in history_after
        if row.get("id") == future_occurrence_id
    ]
    assert len(future_after) == 1
    assert future_after[0]["administered_date"] is None
    assert future_after[0]["next_due_date"] == future_date.isoformat()

    audit = get_json(
        "/farm/vaccinations/audit-history",
        params={"animal_id": animal_id},
    )
    assert len(audit) == 3
    assert sorted(row["action"] for row in audit) == [
        "ADMINISTERED",
        "SCHEDULE_CREATED",
        "SCHEDULE_CREATED",
    ]
    schedule_audit = [
        row for row in audit if row["action"] == "SCHEDULE_CREATED"
    ]
    assert {
        row["scheduled_date"] for row in schedule_audit
    } == {due_date.isoformat(), future_date.isoformat()}
    assert all(row["administered_date"] is None for row in schedule_audit)
    administered_audit = next(
        row
        for row in audit
        if row["action"] == "ADMINISTERED"
    )
    assert administered_audit["vaccination_occurrence_id"] == occurrence_id
    assert administered_audit["scheduled_date"] == due_date.isoformat()
    assert administered_audit["administered_date"] == due_date.isoformat()

    summary_after = get_json("/farm/vaccination/summary")
    assert summary_after["vaccinationsRecorded"] == 1
    assert summary_after["vaccinationsOverdue"] == 0
    assert summary_after["vaccinationsDueNext30Days"] == 1
    future_after_summary = [
        row
        for row in summary_after["upcomingVaccinations"]
        if row.get("vaccination_occurrence_id") == future_occurrence_id
    ]
    assert len(future_after_summary) == 1
    assert future_after_summary[0]["due_state"] == "SCHEDULED"
    assert [
        row
        for row in summary_after["upcomingVaccinations"]
        if row.get("vaccination_occurrence_id") == occurrence_id
    ] == []

    dashboard_after = get_json("/dashboard")
    assert dashboard_after["vaccination"]["completed"] == 1
    assert dashboard_after["vaccination"]["due"] == 0
    assert [
        row
        for row in dashboard_after["vaccination"]["due_animals"]
        if row.get("vaccination_occurrence_id") == occurrence_id
    ] == []

    return {
        "animal_id": animal_id,
        "occurrence_id": occurrence_id,
        "future_occurrence_id": future_occurrence_id,
        "vaccine": vaccine,
        "due_date": due_date,
        "future_date": future_date,
        "future_summary": {
            "recorded": summary_future["vaccinationsRecorded"],
            "overdue": summary_future["vaccinationsOverdue"],
            "due_next_30_days": summary_future[
                "vaccinationsDueNext30Days"
            ],
        },
        "due_state": due_rows[0]["due_state"],
        "administered_date": due_date,
        "audit_actions": sorted(row["action"] for row in audit),
        "final_summary": {
            "recorded": summary_after["vaccinationsRecorded"],
            "overdue": summary_after["vaccinationsOverdue"],
            "due_next_30_days": summary_after[
                "vaccinationsDueNext30Days"
            ],
            "future_occurrence_remains_scheduled": True,
        },
    }


def _record_synthetic_cross_module_stage(
    client,
    health_stage: dict,
):
    """SIM-X: carry an active health withdrawal into Milk safely.

    The independent oracle expects the Milk write to retain biological
    production while creating exactly one paired WASTAGE disposition. This
    proves the Health -> Milk boundary without changing the frozen SIM-M
    production date or using a read-model value as the oracle.
    """

    animal_id = health_stage["animal_id"]
    production_date = health_stage["health_date"]
    litres = Decimal("5")

    response = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "milking_session": "MORNING",
            "production_date": production_date.isoformat(),
            "morning_yield": float(litres),
            "operator": "FC-SIM Cross-Module Operator",
            "notes": "FC-SIM Health-to-Milk withdrawal boundary",
        },
    )
    assert response.status_code == 200, response.text
    milk_result = response.json()
    assert milk_result["withdrawal_warning"] is True
    assert Decimal(str(milk_result["withdrawal_wastage_litres"])) == litres
    assert "automatically posted to WASTAGE" in milk_result["safety_message"]
    assert milk_result["withdrawal_wastage_ids"]

    ledger_response = client.get(
        "/farm/milk/ledger",
        params={
            "start_date": production_date.isoformat(),
            "end_date": production_date.isoformat(),
        },
    )
    assert ledger_response.status_code == 200, ledger_response.text
    ledger = ledger_response.json()

    production_rows = [
        row for row in ledger["production"] if row["animal_id"] == animal_id
    ]
    assert len(production_rows) == 1
    production_row = production_rows[0]
    assert production_row["status"] == "RECORDED"
    assert production_row["milking_session"] == "MORNING"
    assert Decimal(str(production_row["total_yield"])) == litres

    wastage_rows = [
        row
        for row in ledger["dispositions"]
        if row["disposition_type"] == "WASTAGE"
        and str(row.get("notes") or "").startswith(
            "AUTO_WITHDRAWAL_WASTAGE:"
        )
        and animal_id in str(row.get("notes") or "")
    ]
    assert len(wastage_rows) == 1
    wastage = wastage_rows[0]
    assert Decimal(str(wastage["quantity_litres"])) == litres
    assert Decimal(str(wastage["amount_due"])) == Decimal("0")
    assert Decimal(str(wastage["amount_received"])) == Decimal("0")
    assert wastage["status"] == "RECORDED"

    trace_response = client.get(
        f"/farm/milk/{animal_id}/traceability"
    )
    assert trace_response.status_code == 200, trace_response.text
    trace = trace_response.json()
    assert trace["traceability_complete"] is True
    assert trace["record_count"] == 2
    assert Decimal(str(trace["total_litres"])) == Decimal("35")
    assert any(
        row.get("id") == production_row["id"]
        and str(row.get("production_date") or "")[:10]
        == production_date.isoformat()
        for row in trace["milk_records"]
    )

    return {
        "animal_id": animal_id,
        "production_date": production_date,
        "biological_litres": litres,
        "withdrawal_litres": litres,
        "saleable_litres": Decimal("0"),
        "production_id": production_row["id"],
        "wastage_id": wastage["id"],
        "traceability_complete": trace["traceability_complete"],
    }


def _record_synthetic_negative_stage(
    client,
    created_animals: dict[str, str],
    vaccination_stage: dict,
):
    """SIM-N: prove representative governed rejection boundaries.

    These attempts target existing synthetic records and must fail closed:
    duplicate schedule, repeat administration, and cross-animal
    administration must not add relational rows or operational events.
    """

    animal_id = vaccination_stage["animal_id"]
    due_occurrence_id = vaccination_stage["occurrence_id"]
    future_occurrence_id = vaccination_stage["future_occurrence_id"]
    vaccine = vaccination_stage["vaccine"]
    due_date = vaccination_stage["due_date"]
    future_date = vaccination_stage["future_date"]

    def get_json(path: str, **kwargs):
        response = client.get(path, **kwargs)
        assert response.status_code == 200, response.text
        return response.json()

    history_before = get_json(
        f"/farm/animals/{animal_id}/vaccinations"
    )
    event_history_before = get_json(
        "/farm/vaccinations/audit-history",
        params={"animal_id": animal_id},
    )
    assert len(history_before) == 2
    assert len(event_history_before) == 3

    duplicate_schedule = client.post(
        f"/farm/animals/{animal_id}/vaccinations/schedule-batch",
        json={
            "animal_id": animal_id,
            "operator": "FC-SIM Negative Operator",
            "occurrences": [
                {
                    "vaccine": vaccine,
                    "dose": "2 ml",
                    "scheduled_date": future_date.isoformat(),
                }
            ],
        },
    )
    assert duplicate_schedule.status_code == 409, duplicate_schedule.text
    assert "Duplicate active vaccination occurrence" in str(
        duplicate_schedule.json()["detail"]
    )

    repeat_administration = client.post(
        (
            f"/farm/animals/{animal_id}/vaccinations/"
            f"{due_occurrence_id}/administer"
        ),
        json={
            "administered_date": due_date.isoformat(),
            "operator": "FC-SIM Negative Operator",
        },
    )
    assert repeat_administration.status_code == 409
    assert "already been administered" in str(
        repeat_administration.json()["detail"]
    )

    other_animal_id = created_animals["MALE-CALF-01"]
    cross_animal_administration = client.post(
        (
            f"/farm/animals/{other_animal_id}/vaccinations/"
            f"{future_occurrence_id}/administer"
        ),
        json={
            "administered_date": due_date.isoformat(),
            "operator": "FC-SIM Negative Operator",
        },
    )
    assert cross_animal_administration.status_code == 409
    assert "does not belong to this animal" in str(
        cross_animal_administration.json()["detail"]
    )

    history_after = get_json(
        f"/farm/animals/{animal_id}/vaccinations"
    )
    event_history_after = get_json(
        "/farm/vaccinations/audit-history",
        params={"animal_id": animal_id},
    )
    assert len(history_after) == len(history_before) == 2
    assert len(event_history_after) == len(event_history_before) == 3
    assert {
        row["id"] for row in history_after
    } == {due_occurrence_id, future_occurrence_id}
    assert [
        row["action"] for row in event_history_after
    ] == [row["action"] for row in event_history_before]

    summary = get_json("/farm/vaccination/summary")
    assert summary["vaccinationsRecorded"] == 1
    assert summary["vaccinationsOverdue"] == 0
    assert summary["vaccinationsDueNext30Days"] == 1
    assert any(
        row.get("vaccination_occurrence_id") == future_occurrence_id
        for row in summary["upcomingVaccinations"]
    )

    return {
        "animal_id": animal_id,
        "rejections": {
            "duplicate_schedule": duplicate_schedule.status_code,
            "repeat_administration": repeat_administration.status_code,
            "cross_animal_administration": (
                cross_animal_administration.status_code
            ),
        },
        "history_rows_before": len(history_before),
        "history_rows_after": len(history_after),
        "audit_rows_before": len(event_history_before),
        "audit_rows_after": len(event_history_after),
        "future_occurrence_retained": True,
    }


def _record_synthetic_breeding_stage(
    client,
    created_animals: dict[str, str],
    finance_stage: dict,
    *,
    operational_clock: dict[str, date],
):
    """SIM-B: execute one governed reproductive lifecycle and restart it.

    The independent oracle deliberately derives every reproductive date from
    the AI date. The stage uses the Finance-created semen lot, the public
    breeding routes, and the governed post-calving reconciliation service;
    it never inserts a breeding, inventory, or animal row directly.
    """

    animal_id = created_animals["DRY-01"]
    semen_purchase_id = int(finance_stage["semen_purchase"]["id"])

    def get_json(path: str, **kwargs):
        response = client.get(path, **kwargs)
        assert response.status_code == 200, response.text
        return response.json()

    def post_event(*, event_type: str, result: str, event_date: date, **extra):
        response = client.post(
            "/farm/breeding",
            json={
                "animal_id": animal_id,
                "event_type": event_type,
                "technician": "FC-SIM Reproduction Operator",
                "operator": "FC-SIM Reproduction Operator",
                "result": result,
                "timestamp": event_date.isoformat(),
                **extra,
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["propagation_status"] == "DELIVERED"
        return payload

    stock_before = get_json("/farm/breeding/semen-stock")
    matching_lots = [
        row
        for row in stock_before["available_lots"]
        if int(row.get("purchase_transaction_id") or 0) == semen_purchase_id
    ]
    assert len(matching_lots) == 1, stock_before
    semen_lot = matching_lots[0]
    assert semen_lot["semen_type"] == "SEXED"
    assert int(semen_lot["available_straws"]) == 5

    ai_date = operational_clock["value"]
    pd_due_date = ai_date + timedelta(days=35)
    calving_date = ai_date + timedelta(days=283)
    planned_return_date = calving_date + timedelta(days=30)
    second_ai_date = planned_return_date + timedelta(days=60)

    # First cycle: AI -> PD -> calving.
    first_ai = post_event(
        event_type="insemination",
        result="COMPLETED",
        event_date=ai_date,
        semen_lot_id=int(semen_lot["id"]),
    )
    assert first_ai["semen_lot_id"] == semen_lot["id"]
    assert first_ai["semen_type"] == "SEXED"
    assert first_ai["sire_code"] == "FC-SIM-SIRE-001"
    assert first_ai["reproductive_state"]["state"] == "INSEMINATED"

    stock_after_first_ai = get_json("/farm/breeding/semen-stock")
    first_balance = next(
        row["available_straws"]
        for row in stock_after_first_ai["lots"]
        if row["id"] == semen_lot["id"]
    )
    assert int(first_balance) == 4

    first_state = get_json(f"/farm/animals/{animal_id}/reproduction")
    assert first_state["state"] == "INSEMINATED"
    assert first_state["last_insemination_date"] == ai_date.isoformat()
    assert first_state["pd_due_date"] == pd_due_date.isoformat()

    operational_clock["value"] = pd_due_date
    positive_pd = post_event(
        event_type="pregnancy_diagnosis",
        result="POSITIVE",
        event_date=pd_due_date,
    )
    assert positive_pd["event_type"] == "pregnancy_diagnosis"
    assert positive_pd["result"] == "pregnant"
    assert positive_pd["reproductive_state"]["state"] == "PREGNANT"
    assert (
        positive_pd["reproductive_state"]["pregnancy_confirmed_date"]
        == pd_due_date.isoformat()
    )
    assert (
        positive_pd["reproductive_state"]["expected_calving_date"]
        == calving_date.isoformat()
    )
    assert positive_pd["reproductive_state"]["pd_due_date"] == pd_due_date.isoformat()

    pd_state = get_json(f"/farm/animals/{animal_id}/reproduction")
    assert pd_state["state"] == "PREGNANT"
    assert pd_state["pregnancy_status"] == "PREGNANT"
    assert pd_state["expected_calving_date"] == calving_date.isoformat()

    operational_clock["value"] = calving_date
    calving = post_event(
        event_type="calving",
        result="COMPLETED",
        event_date=calving_date,
        calf_sex="FEMALE",
        planned_return_to_milking_date=planned_return_date.isoformat(),
    )
    calf_id = calving["calf_animal_id"]
    assert calf_id
    assert calving["reproductive_state"]["state"] == "DRY_OFF"
    assert calving["reproductive_state"]["pregnancy_status"] == "NOT_PREGNANT"
    assert calving["planned_return_to_milking_date"] == planned_return_date.isoformat()

    mother_after_calving = get_json(f"/farm/animals/{animal_id}")
    assert mother_after_calving["lifecycle_status"] == "DRY"
    assert mother_after_calving["is_currently_milking"] is False
    assert mother_after_calving["milking_frequency"] is None

    calf = get_json(f"/farm/animals/{calf_id}")
    assert calf["sex"] == "FEMALE"
    assert calf["lifecycle_status"] == "CALF"
    assert calf["dam_id"] == animal_id
    assert calf["is_currently_milking"] is False

    calving_state = get_json(f"/farm/animals/{animal_id}/reproduction")
    assert calving_state["state"] == "DRY_OFF"
    assert calving_state["pregnancy_status"] == "NOT_PREGNANT"
    assert calving_state["last_calving_date"] == calving_date.isoformat()
    assert calving_state["expected_calving_date"] is None

    # The operator-entered return date is applied by the lifecycle service,
    # not by a read endpoint, and a repeated pass must be idempotent.
    operational_clock["value"] = planned_return_date
    applied = reconcile_due_post_calving_returns(
        container.repository_factory,
        container.event_journal,
        as_of_date=planned_return_date,
    )
    assert applied == [animal_id]
    assert reconcile_due_post_calving_returns(
        container.repository_factory,
        container.event_journal,
        as_of_date=planned_return_date,
    ) == []

    mother_after_return = get_json(f"/farm/animals/{animal_id}")
    assert mother_after_return["lifecycle_status"] == "LACTATING"
    assert mother_after_return["is_currently_milking"] is True
    assert mother_after_return["milking_frequency"] in {
        "TWICE_DAILY",
        "THRICE_DAILY",
    }

    returned_state = get_json(f"/farm/animals/{animal_id}/reproduction")
    assert returned_state["state"] == "LACTATING"
    assert returned_state["pregnancy_status"] == "NOT_PREGNANT"
    assert returned_state["last_calving_date"] == calving_date.isoformat()

    frequency_history = get_json(
        f"/farm/animals/{animal_id}/milking-frequency/history"
    )
    planned_return_rows = [
        row
        for row in frequency_history
        if str(row.get("reason") or "").upper()
        == "POST_CALVING_PLANNED_RETURN"
        and str(row.get("effective_from"))[:10]
        == planned_return_date.isoformat()
    ]
    assert len(planned_return_rows) == 1

    # Second cycle: the post-calving reset must permit a new AI and consume
    # exactly one additional straw from the same governed lot.
    operational_clock["value"] = second_ai_date
    second_ai = post_event(
        event_type="insemination",
        result="COMPLETED",
        event_date=second_ai_date,
        semen_lot_id=int(semen_lot["id"]),
    )
    assert second_ai["record_id"] != first_ai["record_id"]
    assert second_ai["reproductive_state"]["state"] == "INSEMINATED"
    assert (
        second_ai["reproductive_state"]["last_insemination_date"]
        == second_ai_date.isoformat()
    )
    assert second_ai["reproductive_state"]["pd_due_date"] == (
        second_ai_date + timedelta(days=35)
    ).isoformat()

    stock_after_second_ai = get_json("/farm/breeding/semen-stock")
    second_balance = next(
        row["available_straws"]
        for row in stock_after_second_ai["lots"]
        if row["id"] == semen_lot["id"]
    )
    assert int(second_balance) == 3

    breeding_ledger = get_json("/farm/breeding")
    animal_events = [
        row for row in breeding_ledger if row.get("animal_id") == animal_id
    ]
    assert [row["event_type"] for row in animal_events] == [
        "insemination",
        "pregnancy_diagnosis",
        "calving",
        "insemination",
    ]
    assert all(row.get("semen_lot_id") == semen_lot["id"] for row in animal_events[::3])

    passport = get_json(
        f"/farm/animals/{animal_id}/passport",
        params={"as_of_date": second_ai_date.isoformat()},
    )
    passport_current = passport["reproduction"]["current"]
    assert passport_current["current_api_status"] == "INSEMINATED"
    assert passport_current["pregnancy_status"] == "NOT_PREGNANT"
    assert passport_current["last_calving_date"] == calving_date.isoformat()
    lifetime_events = passport["reproduction"]["lifetime_events"]
    assert sum(event["event_type"] == "INSEMINATION" for event in lifetime_events) == 2
    assert any(
        event["event_type"] == "PREGNANCY_CONFIRMED"
        for event in lifetime_events
    )
    assert any(event["event_type"] == "CALVING" for event in lifetime_events)

    dashboard = get_json("/dashboard")
    assert dashboard["reproduction"]["inseminated"] >= 1
    assert dashboard["reproduction"]["pregnant"] == 0

    return {
        "animal_id": animal_id,
        "calf_id": calf_id,
        "semen_lot_id": semen_lot["id"],
        "first_ai_date": ai_date,
        "pd_due_date": pd_due_date,
        "calving_date": calving_date,
        "planned_return_date": planned_return_date,
        "second_ai_date": second_ai_date,
        "stock_balances": (5, int(first_balance), int(second_balance)),
        "event_types": [row["event_type"] for row in animal_events],
        "returned_lifecycle": mother_after_return["lifecycle_status"],
        "second_cycle_state": second_ai["reproductive_state"]["state"],
    }


def test_fc_sim_08_whole_farm_certification_contract(client, monkeypatch):
    """
    Whole-farm synthetic certification.

    This harness executes one coherent synthetic farm through governed
    production APIs and services.

    Execution is restricted to the governed disposable certification database.

    The executable lifecycle currently proves:

        Animals
          -> Milk
          -> Feed/TMR
          -> Finance
          -> COP
          -> Health
          -> Vaccination
          -> Semen/Breeding

    Dashboard and Passport reads in the implemented stages are projections
    and reconciliation surfaces.

    using one coherent synthetic farm state.

    The lifecycle uses controlled synthetic writes and independently
    reconciles persisted and projected production state.
    """

    _assert_disposable_database_contract()

    operational_date = date(2026, 9, 14)
    operational_clock = {"value": operational_date}

    monkeypatch.setattr(
        OperationalDateAuthority,
        "current_date",
        lambda self: operational_clock["value"],
    )

    created_animals = _create_synthetic_herd(client)

    _assert_synthetic_herd_projection(
        client,
        created_animals,
    )

    assert len(created_animals) == HERD_ORACLE.total

    assert HERD_ORACLE.total == 9
    assert MILK_ORACLE.milking_animals == 4
    assert MILK_ORACLE.total_liters == Decimal("100")
    assert (
        MILK_ORACLE.average_per_milking_animal
        == Decimal("25")
    )

    milk_stage = _record_synthetic_milk_stage(
        client,
        created_animals,
        operational_date,
    )

    assert milk_stage["expected_session_count"] == 11
    assert (
        milk_stage["calculated_animal_totals"]
        == milk_stage["expected_animal_totals"]
    )
    assert (
        milk_stage["persisted_animal_totals"]
        == milk_stage["expected_animal_totals"]
    )
    assert (
        milk_stage["passport_animal_totals"]
        == milk_stage["expected_animal_totals"]
    )
    assert (
        milk_stage["calculated_biological_total"]
        == Decimal("100")
    )
    assert (
        milk_stage["persisted_biological_total"]
        == Decimal("100")
    )
    assert milk_stage["summary_total"] == Decimal("100")
    assert (
        milk_stage["summary_average_per_cow"]
        == Decimal("25")
    )
    assert (
        milk_stage["dashboard_daily_total"]
        == Decimal("100")
    )
    assert (
        milk_stage["dashboard_average"]
        == Decimal("25")
    )

    _print_reconciliation(
        label="SIM-A WHOLE-FARM HERD",
        input_value=HERD_ORACLE,
        expected=HERD_ORACLE.total,
        persisted=len(created_animals),
        projected={
            "Milking": 4,
            "Dry": 1,
            "Heifer": 1,
            "Female Calf": 1,
            "Male Calf": 1,
            "Bull": 1,
        },
        calculated=len(created_animals),
    )

    _print_reconciliation(
        label="SIM-M BIOLOGICAL MILK",
        input_value={
            "sessions": 11,
            "animal_totals": (
                milk_stage["expected_animal_totals"]
            ),
        },
        expected=Decimal("100"),
        persisted=(
            milk_stage["persisted_biological_total"]
        ),
        projected={
            "summary": milk_stage["summary_total"],
            "dashboard": (
                milk_stage["dashboard_daily_total"]
            ),
            "passport": (
                milk_stage["passport_animal_totals"]
            ),
        },
        calculated=(
            milk_stage["calculated_biological_total"]
        ),
    )

    _print_reconciliation(
        label="SIM-M AVERAGE YIELD",
        input_value={
            "biological_liters": Decimal("100"),
            "milking_animals": 4,
        },
        expected=Decimal("25"),
        persisted=(
            milk_stage["summary_average_per_cow"]
        ),
        projected=milk_stage["dashboard_average"],
        calculated=(
            Decimal("100") / Decimal("4")
        ),
    )

    feed_tmr_stage = _record_synthetic_feed_tmr_stage(
        client,
        operational_date=operational_date,
    )

    _print_reconciliation(
        label="SIM-F FEED/TMR",
        input_value={
            "herd_counts": {
                "Milking": 4,
                "Dry": 1,
                "Heifer": 1,
                "Female Calf": 1,
                "Male Calf": 1,
                "Bull": 1,
            },
            "feeding_events": 5,
            "upstream_milk_litres": "100",
        },
        expected={
            "whole_herd_feed_cost_per_day": "3200",
            "feeding_events": 5,
        },
        persisted={
            "whole_herd_feed_cost_per_day": str(
                feed_tmr_stage[
                    "persisted_whole_herd_cost"
                ]
            ),
            "feeding_events": feed_tmr_stage[
                "feeding_event_count"
            ],
            "snapshot_record_id": feed_tmr_stage[
                "snapshot_record_id"
            ],
        },
        projected={
            "live_whole_herd_feed_cost_per_day": str(
                feed_tmr_stage[
                    "live_whole_herd_cost"
                ]
            ),
            "all_six_categories": True,
        },
        calculated={
            "whole_herd_feed_cost_per_day": str(
                sum(
                    feed_tmr_stage[
                        "expected_category_cost"
                    ].values()
                )
            ),
            "feeding_events": 5,
        },

    )

    finance_stage = _record_synthetic_finance_stage(
        client,
        operational_date=operational_date,
    )

    _print_reconciliation(
        label="SIM-$ FINANCE",
        input_value={
            "milk_sale": {
                "quantity_liters": "78",
                "rate_per_liter": "150",
            },
            "ordinary_opex": "2000",
            "equipment_purchase": "50000",
            "owner_withdrawal": "5000",
            "owner_investment": "10000",
            "semen_purchase": {
                "straws": "5",
                "rate_per_straw": "1000",
            },
        },
        expected={
            "milk_sale_amount": "11700",
            "direct_opex": "2000",
            "equipment_purchase": "50000",
            "owner_withdrawal": "5000",
            "owner_investment": "10000",
            "semen_purchase_amount": "5000",
        },
        persisted={
            "milk_sale_amount": str(
                finance_stage["milk_sale"]["amount"]
            ),
            "direct_opex": str(
                finance_stage["opex"]["amount"]
            ),
            "equipment_purchase": str(
                finance_stage["equipment"]["amount"]
            ),
            "owner_withdrawal": str(
                finance_stage["owner_withdrawal"]["amount"]
            ),
            "owner_investment": str(
                finance_stage["owner_investment"]["amount"]
            ),
            "semen_purchase_amount": str(
                finance_stage["semen_purchase"]["amount"]
            ),
        },
        projected={
            "milk_sale_status": finance_stage[
                "milk_sale"
            ]["status"],
            "opex_classification": finance_stage[
                "opex"
            ]["cop_classification"],
            "equipment_classification": finance_stage[
                "equipment"
            ]["cop_classification"],
            "semen_purchase_transaction_id": finance_stage[
                "semen_purchase"
            ]["id"],
        },
        calculated={
            "milk_sale_amount": str(
                Decimal("78") * Decimal("150")
            ),
            "direct_opex": "2000",
            "equipment_purchase": "50000",
            "owner_withdrawal": "5000",
            "owner_investment": "10000",
            "semen_purchase_amount": str(
                Decimal("5") * Decimal("1000")
            ),
        },
    )

    # ------------------------------------------------------------
    # SIM-C — integrated COP / COML
    # ------------------------------------------------------------
    #
    # Independent external oracle:
    #
    #   persisted authoritative Milk = 100 L
    #   governed whole-herd TMR       = Rs 3,200
    #   attributed ordinary OPEX      = Rs 2,000
    #
    # Therefore:
    #
    #   Feed Cost/L = 3200 / 100 = 32
    #   OPEX/L      = 2000 / 100 = 20
    #   COP/L       = 5200 / 100 = 52
    #
    # Do not use saleable litres as the denominator. Do not include
    # Equipment Purchase, owner financing, or unconsumed semen purchase
    # in attributed operating OPEX.

    cop_response = client.get(
        "/farm/coml/integrated",
        params={
            "period_start": operational_date.isoformat(),
            "period_end": operational_date.isoformat(),
            "allow_current_period": True,
        },
    )

    assert cop_response.status_code == 200, cop_response.text

    cop_body = cop_response.json()
    cop_costs = cop_body["costs"]

    authoritative_milk = Decimal(
        str(cop_body["production"]["totalLiters"])
    )

    persisted_feed_total = Decimal(
        str(cop_costs["feed_total"])
    )

    persisted_opex_total = Decimal(
        str(cop_costs["opex_total"])
    )

    projected_feed_per_liter = Decimal(
        str(cop_costs["feed_cost_per_liter"])
    )

    projected_opex_per_liter = Decimal(
        str(cop_costs["opex_cost_per_liter"])
    )

    projected_cop_per_liter = Decimal(
        str(cop_costs["total_coml_per_liter"])
    )

    expected_cost = CostOracle(
        feed_cost=Decimal("3200"),
        opex=Decimal("2000"),
        milk_liters=Decimal("100"),
    )

    assert authoritative_milk == Decimal("100")
    assert persisted_feed_total == Decimal("3200")
    assert persisted_opex_total == Decimal("2000")

    assert projected_feed_per_liter == (
        expected_cost.feed_cost_per_liter
    )
    assert projected_opex_per_liter == (
        expected_cost.opex_per_liter
    )
    assert projected_cop_per_liter == (
        expected_cost.cop_per_liter
    )

    assert Decimal(
        str(cop_body["feed_cost_per_liter"])
    ) == expected_cost.feed_cost_per_liter

    assert Decimal(
        str(cop_body["opex_cost_per_liter"])
    ) == expected_cost.opex_per_liter

    assert Decimal(
        str(cop_body["total_coml_per_liter"])
    ) == expected_cost.cop_per_liter

    assert cop_costs["source"] == "TMR_HERD_COST+FINANCE_OPEX"

    assert cop_costs["feed_source"]["complete"] is True

    # Explicit contamination barriers.
    #
    # Equipment Purchase = Rs50,000
    # Owner Withdrawal    = Rs5,000
    # Owner Investment    = Rs10,000
    # Semen purchase      = Rs5,000, consumption-governed
    #
    # None may increase current attributed OPEX beyond Rs2,000.
    assert persisted_opex_total != Decimal("52000")
    assert persisted_opex_total != Decimal("57000")
    assert persisted_opex_total != Decimal("67000")
    assert persisted_opex_total != Decimal("72000")

    print()
    print("=== SIM-C COP/COML ===")
    print(
        "INPUT      :",
        {
            "authoritative_milk_liters": "100",
            "whole_herd_tmr_cost": "3200",
            "ordinary_attributed_opex": "2000",
            "equipment_purchase": "50000",
            "owner_withdrawal": "5000",
            "owner_investment": "10000",
            "unconsumed_semen_purchase": "5000",
        },
    )
    print(
        "EXPECTED   :",
        {
            "feed_cost_per_liter": "32",
            "opex_cost_per_liter": "20",
            "cop_per_liter": "52",
        },
    )
    print(
        "PERSISTED  :",
        {
            "milk_liters": str(authoritative_milk),
            "feed_total": str(persisted_feed_total),
            "opex_total": str(persisted_opex_total),
        },
    )
    print(
        "PROJECTED  :",
        {
            "feed_cost_per_liter": str(
                projected_feed_per_liter
            ),
            "opex_cost_per_liter": str(
                projected_opex_per_liter
            ),
            "cop_per_liter": str(
                projected_cop_per_liter
            ),
            "source": cop_costs["source"],
            "feed_authority_complete": (
                cop_costs["feed_source"]["complete"]
            ),
        },
    )
    print(
        "CALCULATED :",
        {
            "feed_cost_per_liter": str(
                expected_cost.feed_cost_per_liter
            ),
            "opex_cost_per_liter": str(
                expected_cost.opex_per_liter
            ),
            "cop_per_liter": str(
                expected_cost.cop_per_liter
            ),
        },
    )
    print(
        "DELTA      :",
        {
            "feed": str(
                projected_feed_per_liter
                - expected_cost.feed_cost_per_liter
            ),
            "opex": str(
                projected_opex_per_liter
                - expected_cost.opex_per_liter
            ),
            "cop": str(
                projected_cop_per_liter
                - expected_cost.cop_per_liter
            ),
        },
    )
    print("RESULT     : PASS")

    # The executable COP stage must still obtain its denominator from
    # persisted authoritative Milk production. These values are independent
    # external expectations, not Dashboard/COP-derived results.
    assert MILK_ORACLE.saleable_liters == Decimal("78")
    assert MILK_ORACLE.withdrawal_liters == Decimal("22")
    assert MILK_ORACLE.thrice_average_liters == (
        Decimal("79") / Decimal("3")
    )
    assert MILK_ORACLE.twice_average_liters == Decimal("21")

    health_stage = _record_synthetic_health_stage(
        client,
        created_animals,
        operational_clock=operational_clock,
    )

    _print_reconciliation(
        label="SIM-H HEALTH / WITHDRAWAL",
        input_value={
            "animal": "MILK-THRICE-01",
            "severity": "SEVERE",
            "observation": "Elevated temperature and reduced appetite",
            "withdrawal_days": 3,
            "follow_up_date": health_stage["health_date"].isoformat(),
        },
        expected={
            "withdrawal_days": 3,
            "open_summary": {
                "active_cases": 1,
                "active_sick_animals": 1,
                "followups_due": 1,
                "withdrawal_animals": 1,
            },
            "resolved_summary": {
                "active_cases": 0,
                "active_sick_animals": 0,
                "followups_due": 0,
                "withdrawal_animals": 1,
            },
            "passport_withdrawal_active_after_resolution": True,
        },
        persisted={
            "case_code": health_stage["case_code"],
            "case_id": health_stage["case_id"],
            "withdrawal_until": health_stage["withdrawal_until"],
            "status_after_resolution": "RESOLVED",
        },
        projected={
            "open_summary": health_stage["open_summary"],
            "resolved_summary": health_stage["resolved_summary"],
            "passport_withdrawal_active_after_resolution": health_stage[
                "passport_withdrawal_active_after_resolution"
            ],
        },
        calculated={
            "withdrawal_days": health_stage["withdrawal_days"],
            "open_summary": health_stage["open_summary"],
            "resolved_summary": health_stage["resolved_summary"],
            "passport_withdrawal_active_after_resolution": health_stage[
                "passport_withdrawal_active_after_resolution"
            ],
        },
    )

    vaccination_stage = _record_synthetic_vaccination_stage(
        client,
        created_animals,
        operational_clock=operational_clock,
    )

    _print_reconciliation(
        label="SIM-V VACCINATION / SCHEDULE",
        input_value={
            "animal": "FEMALE-CALF-01",
            "vaccine": vaccination_stage["vaccine"],
            "due_date": vaccination_stage["due_date"].isoformat(),
            "future_date": vaccination_stage["future_date"].isoformat(),
        },
        expected={
            "future_summary": {
                "recorded": 0,
                "overdue": 0,
                "due_next_30_days": 1,
            },
            "due_state_before_mark_given": "DUE_TODAY",
            "same_occurrence_administered": True,
            "audit_actions": [
                "ADMINISTERED",
                "SCHEDULE_CREATED",
                "SCHEDULE_CREATED",
            ],
            "final_summary": {
                "recorded": 1,
                "overdue": 0,
                "due_next_30_days": 1,
                "future_occurrence_remains_scheduled": True,
            },
        },
        persisted={
            "occurrence_id": vaccination_stage["occurrence_id"],
            "administered_date": vaccination_stage[
                "administered_date"
            ].isoformat(),
            "audit_actions": vaccination_stage["audit_actions"],
        },
        projected={
            "future_summary": vaccination_stage["future_summary"],
            "due_state_before_mark_given": vaccination_stage[
                "due_state"
            ],
            "final_summary": vaccination_stage["final_summary"],
        },
        calculated={
            "future_summary": vaccination_stage["future_summary"],
            "due_state_before_mark_given": vaccination_stage[
                "due_state"
            ],
            "same_occurrence_administered": True,
            "audit_actions": vaccination_stage["audit_actions"],
            "final_summary": vaccination_stage["final_summary"],
        },
    )

    cross_module_stage = _record_synthetic_cross_module_stage(
        client,
        health_stage,
    )

    _print_reconciliation(
        label="SIM-X HEALTH -> MILK WITHDRAWAL",
        input_value={
            "animal": "MILK-THRICE-01",
            "production_date": cross_module_stage[
                "production_date"
            ].isoformat(),
            "biological_litres": "5",
            "health_withdrawal_active": True,
        },
        expected={
            "biological_litres": "5",
            "withdrawal_litres": "5",
            "saleable_litres": "0",
            "paired_wastage": True,
            "traceability_complete": True,
        },
        persisted={
            "production_id": cross_module_stage["production_id"],
            "wastage_id": cross_module_stage["wastage_id"],
            "biological_litres": str(
                cross_module_stage["biological_litres"]
            ),
            "withdrawal_litres": str(
                cross_module_stage["withdrawal_litres"]
            ),
        },
        projected={
            "traceability_complete": cross_module_stage[
                "traceability_complete"
            ],
            "withdrawal_warning": True,
        },
        calculated={
            "biological_litres": str(
                cross_module_stage["biological_litres"]
            ),
            "withdrawal_litres": str(
                cross_module_stage["withdrawal_litres"]
            ),
            "saleable_litres": str(
                cross_module_stage["saleable_litres"]
            ),
            "paired_wastage": True,
            "traceability_complete": True,
        },
    )

    negative_stage = _record_synthetic_negative_stage(
        client,
        created_animals,
        vaccination_stage,
    )

    _print_reconciliation(
        label="SIM-N GOVERNED REJECTIONS",
        input_value={
            "duplicate_schedule": True,
            "repeat_administration": True,
            "cross_animal_administration": True,
        },
        expected={
            "rejection_statuses": {
                "duplicate_schedule": 409,
                "repeat_administration": 409,
                "cross_animal_administration": 409,
            },
            "history_unchanged": True,
            "audit_unchanged": True,
            "future_occurrence_retained": True,
        },
        persisted={
            "rejections": negative_stage["rejections"],
            "history_rows_before": negative_stage[
                "history_rows_before"
            ],
            "history_rows_after": negative_stage["history_rows_after"],
            "audit_rows_before": negative_stage["audit_rows_before"],
            "audit_rows_after": negative_stage["audit_rows_after"],
        },
        projected={
            "future_occurrence_retained": negative_stage[
                "future_occurrence_retained"
            ],
        },
        calculated={
            "rejection_statuses": negative_stage["rejections"],
            "history_unchanged": (
                negative_stage["history_rows_before"]
                == negative_stage["history_rows_after"]
            ),
            "audit_unchanged": (
                negative_stage["audit_rows_before"]
                == negative_stage["audit_rows_after"]
            ),
            "future_occurrence_retained": True,
        },
    )

    breeding_stage = _record_synthetic_breeding_stage(
        client,
        created_animals,
        finance_stage,
        operational_clock=operational_clock,
    )

    _print_reconciliation(
        label="SIM-B BREEDING / SEMEN",
        input_value={
            "animal": "DRY-01",
            "semen_lot_id": breeding_stage["semen_lot_id"],
            "first_ai": breeding_stage["first_ai_date"].isoformat(),
            "pd_due": breeding_stage["pd_due_date"].isoformat(),
            "calving": breeding_stage["calving_date"].isoformat(),
            "planned_return": breeding_stage[
                "planned_return_date"
            ].isoformat(),
            "second_ai": breeding_stage["second_ai_date"].isoformat(),
        },
        expected={
            "event_types": [
                "insemination",
                "pregnancy_diagnosis",
                "calving",
                "insemination",
            ],
            "stock_balances": (5, 4, 3),
            "returned_lifecycle": "LACTATING",
            "second_cycle_state": "INSEMINATED",
        },
        persisted={
            "event_types": breeding_stage["event_types"],
            "stock_balances": breeding_stage["stock_balances"],
            "calf_id": breeding_stage["calf_id"],
        },
        projected={
            "returned_lifecycle": breeding_stage["returned_lifecycle"],
            "second_cycle_state": breeding_stage["second_cycle_state"],
            "planned_return_applied_once": True,
        },
        calculated={
            "event_types": breeding_stage["event_types"],
            "stock_balances": breeding_stage["stock_balances"],
            "returned_lifecycle": breeding_stage["returned_lifecycle"],
            "second_cycle_state": breeding_stage["second_cycle_state"],
        },
    )

    print("")
    print("============================================================")
    print("============================================================")
