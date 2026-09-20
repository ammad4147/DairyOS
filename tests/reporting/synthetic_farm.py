"""Deterministic synthetic farm for end-to-end Reporting certification.

Everything here is written to a disposable test database only. The farm
clock is frozen at ``TODAY`` so every expected figure is a fixed constant.

Expected results are declared in ``EXPECTED`` *before* any report runs and
are derived by hand from the fixtures below, never from Reporting code.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal

from dairyos.data.database.models.breeding_record_model import BreedingRecordModel
from dairyos.data.models.animal import Animal
from dairyos.data.models.coml_record import COMLRecord
from dairyos.data.models.feed_ration import FeedRation
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.health_case import HealthCase
from dairyos.data.models.milk_disposition import MilkDisposition
from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.semen_inventory import SemenLot, SemenStockMovement
from dairyos.data.models.treatment_record import TreatmentRecord
from dairyos.data.models.vaccination_record import VaccinationRecord

PKT = timezone(timedelta(hours=5))
TODAY = date(2026, 9, 18)
NOW = datetime(2026, 9, 18, 12, 0, tzinfo=PKT)

D = Decimal

# --------------------------------------------------------------------------
# Herd: 48 current animals plus two exits that must never be counted.
# --------------------------------------------------------------------------
HERD = {
    "Milking": [f"M{i:03d}" for i in range(1, 21)],
    "Dry": [f"D{i:03d}" for i in range(1, 6)],
    "Heifer": [f"H{i:03d}" for i in range(1, 9)],
    "Female Calf": [f"FC{i:03d}" for i in range(1, 8)],
    "Male Calf": [f"MC{i:03d}" for i in range(1, 7)],
    "Bull": [f"B{i:03d}" for i in range(1, 3)],
}
LIFECYCLE = {"Milking": ("LACTATING", "FEMALE"), "Dry": ("DRY", "FEMALE"), "Heifer": ("HEIFER", "FEMALE"),
             "Female Calf": ("CALF", "FEMALE"), "Male Calf": ("CALF", "MALE"), "Bull": ("BULL", "MALE")}
BREEDS = ("Holstein Friesian", "Jersey", "Sahiwal")
EXITED_SOLD, EXITED_DEAD = "XS001", "XD001"

# --------------------------------------------------------------------------
# Milk: every milking cow, every day 31-Aug to 17-Sep (18 days).
# cow i: morning 10 + i % 3, afternoon 8 (cows 1-15, cows 16-20 are twice
# daily), evening 7 + i % 2.
#   morning  = 200 + 7*1 + 7*2 = 221
#   afternoon= 15 * 8          = 120
#   evening  = 140 + 10        = 150
#   per day                    = 491 litres
# --------------------------------------------------------------------------
MILK_DAYS = [date(2026, 8, 31)] + [date(2026, 9, d) for d in range(1, 18)]
DAILY_MILK = {"morning": 221.0, "afternoon": 120.0, "evening": 150.0, "total": 491.0}
SALE_DAYS = [date(2026, 9, d) for d in range(1, 13)]  # 400 L sold each day

EXPECTED = {
    "herd": {"Milking": 20, "Dry": 5, "Heifer": 8, "Female Calf": 7, "Male Calf": 6, "Bull": 2, "total": 48},
    "milk_sep": 17 * 491.0,                     # 8,347 L
    "milk_custom": 18 * 491.0,                  # 31-Aug to 17-Sep = 8,838 L
    # Finance, September 2026
    "sep_revenue": {"Milk Sales": D("1200000.00"), "Animal Sales": D("150000.00"),
                    "Organic Manure / Dung": D("30000.00"), "Other Revenue": D("20000.00")},
    "sep_revenue_total": D("1400000.00"),
    "sep_expenses_total": D("750000.00"),
    "sep_position": D("650000.00"),
    "sep_expense_classes": {"Feed": D("500000.00"), "OPEX": D("190000.00"), "Non-OPEX": D("60000.00")},
    "sep_void": (2, D("112344.00")),
    # Q3 2026: 01-Jul to 30-Sep
    "q3_revenue": D("1413332.00"),
    "q3_expenses": D("757000.00"),
    # Custom 10-Aug to 17-Sep
    "custom_revenue": D("1401111.00"),
    "custom_expenses": D("727000.00"),
    # Positions as of 18-Sep-2026
    "receivables": D("350000.00"), "receivables_overdue": D("100000.00"),
    "payables": D("230000.00"), "payables_overdue": D("200000.00"),
    "receivables_as_of_sep5": D("200000.00"),
    # Settlements with a settled date in September
    "settled_received": D("800000.00"), "settled_paid": D("370000.00"),
    # OPEX attributed to 01-Sep..30-Sep with the farm clock at 18-Sep:
    #   vet fee (direct, 06-Sep)                         50,000.00
    #   medications 30,000 over 30 days, 18 days         18,000.00
    #   electricity 70,000 over 30 days, 18 days         42,000.00
    #   semen: 3 straws used x 2,000                      6,000.00
    "sep_opex": D("116000.00"),
    "sep_feed_cost": D("450000.00"),           # 18 locked days x 25,000
}


def _dt(day: date) -> datetime:
    return datetime.combine(day, time.min)


def _finance(session, day, kind, category, amount, **extra) -> FinancialTransaction:
    row = FinancialTransaction(transaction_type=kind, category=category, amount=D(str(amount)),
                               transaction_date=_dt(day), currency="PKR", **extra)
    row.status = extra.get("status", "RECORDED")
    session.add(row)
    session.flush()
    return row


def _opex(session, day, item, amount, legacy, method, *, service=None, cover=None, **extra):
    return _finance(session, day, "EXPENSE", legacy, amount, master_category="OPEX", sub_category=item,
                    cop_classification="OPEX", cop_attribution_method=method, cop_service_date=service,
                    cop_coverage_start=cover[0] if cover else None, cop_coverage_end=cover[1] if cover else None, **extra)


def seed(session) -> dict:
    """Write the synthetic farm. Returns handles the tests need."""
    # ---- herd -----------------------------------------------------------
    counter = 0
    for category, ids in HERD.items():
        lifecycle, sex = LIFECYCLE[category]
        for animal_id in ids:
            counter += 1
            session.add(Animal(
                animal_id=animal_id, animal_type="CATTLE", sex=sex, lifecycle_status=lifecycle, status="ACTIVE",
                active=True, breed=BREEDS[counter % 3], ear_tag=f"ET-{animal_id}" if counter % 5 else None,
                rfid=f"RF-{animal_id}" if counter % 4 else None,
                date_of_birth=date(2026, 9, 3) if animal_id == "FC001" else date(2020 + counter % 5, 1 + counter % 12, 1 + counter % 27),
                date_of_acquisition=date(2026, 9, 4) if animal_id == "H008" else None,
                dam_id=None, is_currently_milking=category == "Milking",
                milking_frequency=("TWICE_DAILY" if int(animal_id[1:]) > 15 else "THRICE_DAILY") if category == "Milking" else None,
                production_group="High Yield" if category == "Milking" and int(animal_id[1:]) <= 10 else ("Low Yield" if category == "Milking" else None),
                location="Shed A" if counter % 2 else "Shed B",
                photo_data="data:image/png;base64,SECRETPHOTOBYTES",
            ))
    for animal_id in (EXITED_SOLD, EXITED_DEAD):
        session.add(Animal(animal_id=animal_id, animal_type="CATTLE", sex="FEMALE", lifecycle_status="HEIFER",
                           status="ACTIVE", active=True, breed="Jersey", date_of_birth=date(2024, 3, 1)))
    session.flush()
    session.query(Animal).filter(Animal.animal_id == "FC001").update({"dam_id": "M006"})

    # ---- milk -----------------------------------------------------------
    for day in MILK_DAYS:
        for i in range(1, 21):
            morning, evening = 10.0 + i % 3, 7.0 + i % 2
            afternoon = 8.0 if i <= 15 else None
            session.add(MilkProduction(
                animal_id=f"M{i:03d}", production_date=_dt(day) + timedelta(hours=6), session_ledger=True,
                morning_yield=morning, afternoon_yield=afternoon, evening_yield=evening,
                total_yield=morning + (afternoon or 0.0) + evening, status="RECORDED"))
    # Rows that must never be counted.
    session.add(MilkProduction(animal_id="D001", production_date=_dt(date(2026, 9, 16)) + timedelta(hours=6),
                               session_ledger=True, morning_yield=30.0, total_yield=30.0, status="VOID"))
    session.add(MilkProduction(animal_id="D002", production_date=_dt(date(2026, 9, 16)) + timedelta(hours=6),
                               session_ledger=True, status="NOT_MILKED"))
    session.add(MilkProduction(animal_id="D003", production_date=_dt(date(2026, 9, 16)) + timedelta(hours=6),
                               session_ledger=False, total_yield=55.0, status="RECORDED"))

    # ---- revenue ---------------------------------------------------------
    sales = {}
    for day in SALE_DAYS:
        if day.day <= 8:
            status, extra = "RECEIVED", {"settled_date": day + timedelta(days=2)}
        elif day.day <= 10:
            status, extra = "RECORDED", {}
        elif day.day == 11:
            status, extra = "RECEIVABLE", {"due_date": date(2026, 9, 14)}
        else:
            status, extra = "RECEIVABLE", {"due_date": date(2026, 10, 15)}
        row = _finance(session, day, "INCOME", "MILK_SALES", 100000, quantity=400.0, unit="litre",
                       unit_rate=D("250"), counterparty="Lahore Milk Co", status=status, **extra)
        sales[day] = row
        session.add(MilkDisposition(production_date=day, disposition_type="SOLD", quantity_litres=400.0,
                                    sale_id=f"FIN-{row.id}", counterparty="Lahore Milk Co",
                                    selling_price_per_litre=D("250"), amount_due=D("100000"),
                                    amount_received=D("0") if status == "RECEIVABLE" else D("100000"), status="RECORDED"))
        for kind, litres in (("CALF_FEED", 60.0), ("DOMESTIC_USE", 20.0), ("WASTAGE", 5.0)):
            session.add(MilkDisposition(production_date=day, disposition_type=kind, quantity_litres=litres, status="RECORDED"))
    session.add(MilkDisposition(production_date=date(2026, 9, 12), disposition_type="WASTAGE", quantity_litres=77.0, status="VOID"))

    _finance(session, date(2026, 9, 10), "INCOME", "HEIFER_SALE", 150000, animal_id=EXITED_SOLD,
             counterparty="Rana Livestock", status="RECEIVABLE", due_date=date(2026, 9, 30))
    _finance(session, date(2026, 9, 5), "INCOME", "MANURE_SALES", 30000, counterparty="Green Fields")
    _finance(session, date(2026, 9, 17), "INCOME", "OTHER_REVENUE", 15556)          # exactly custom To
    _finance(session, date(2026, 9, 18), "INCOME", "OTHER_REVENUE", 4444)           # day after custom To
    _finance(session, date(2026, 9, 12), "INCOME", "MILK_SALES", 99999, quantity=400.0, unit="litre", status="VOID",
             notes="Duplicate entry\nSTATUS_TRANSITION_AT=2026-09-12T10:00:00+00:00 FROM=RECEIVABLE TO=VOID REASON=Entered twice")
    # Period boundaries
    _finance(session, date(2026, 6, 30), "INCOME", "OTHER_REVENUE", 5555)           # day before Q3
    _finance(session, date(2026, 7, 1), "INCOME", "OTHER_REVENUE", 6666)            # first day of Q3
    _finance(session, date(2026, 8, 9), "INCOME", "OTHER_REVENUE", 1111)            # day before custom From
    _finance(session, date(2026, 8, 10), "INCOME", "OTHER_REVENUE", 2222)           # exactly custom From
    _finance(session, date(2026, 8, 20), "INCOME", "OTHER_REVENUE", 3333)           # inside custom
    _finance(session, date(2026, 10, 1), "INCOME", "OTHER_REVENUE", 7777)           # day after Q3
    # Cash-only movements: never revenue, never expense.
    _finance(session, date(2026, 9, 2), "OWNER_INVESTMENT", "OWNER_INVESTMENT", 500000)
    _finance(session, date(2026, 9, 3), "OWNER_WITHDRAWAL", "OWNER_WITHDRAWAL", 40000)

    # ---- expenses --------------------------------------------------------
    _finance(session, date(2026, 9, 3), "EXPENSE", "FEED", 300000, master_category="FEED",
             sub_category="Corn / Maize Silage", counterparty="Punjab Silage", quantity=20000.0, unit="kg",
             unit_rate=D("15"), status="PAID", settled_date=date(2026, 9, 3))
    _finance(session, date(2026, 9, 8), "EXPENSE", "FEED", 200000, master_category="FEED",
             sub_category="Wheat Bran (Choker)", counterparty="Al-Noor Feeds", status="PAYABLE", due_date=date(2026, 9, 12))
    _opex(session, date(2026, 9, 6), "Routine Vet Fees / Consultation", 50000, "HEALTH", "DIRECT",
          service=date(2026, 9, 6), counterparty="Dr. Hamid")
    _opex(session, date(2026, 9, 7), "Antibiotics & General Medications", 30000, "HEALTH", "ALLOCATED",
          cover=(date(2026, 9, 1), date(2026, 9, 30)), counterparty="Vet Pharma", status="PAYABLE", due_date=date(2026, 10, 5))
    semen = _opex(session, date(2026, 9, 2), "Semen Straws (Sexed / Conventional)", 40000, "BREEDING", "CONSUMPTION",
                  counterparty="Genetics Plus", quantity=20.0, unit="straw", unit_rate=D("2000"))
    _opex(session, date(2026, 9, 15), "Electricity / Power", 70000, "UTILITIES", "PERIODIC",
          cover=(date(2026, 9, 1), date(2026, 9, 30)), counterparty="LESCO", status="PAID", settled_date=date(2026, 9, 15))
    for day, amount in ((date(2026, 9, 17), 35000), (date(2026, 9, 18), 25000)):
        _finance(session, day, "EXPENSE", "EQUIPMENT", amount, master_category="NON_OPEX",
                 sub_category="Equipment Purchase", cop_classification="NON_OPEX", counterparty="Agri Machines")
    _opex(session, date(2026, 9, 9), "Routine Vet Fees / Consultation", 12345, "HEALTH", "DIRECT",
          service=date(2026, 9, 9), status="VOID",
          notes="STATUS_TRANSITION_AT=2026-09-09T09:00:00+00:00 FROM=RECORDED TO=VOID REASON=Wrong amount")
    for day, amount in ((date(2026, 6, 30), 3000), (date(2026, 7, 1), 4000), (date(2026, 8, 9), 1000),
                        (date(2026, 8, 10), 2000), (date(2026, 10, 1), 5000)):
        _opex(session, day, "Pest Control", amount, "OTHER_OPERATING", "DIRECT", service=day)

    # ---- semen -----------------------------------------------------------
    lot = SemenLot(lot_code="SL-001", sire_code="HF-777", bull_name="Titan", breed="Holstein Friesian",
                   semen_type="SEXED", supplier="Genetics Plus", batch_number="B-42",
                   purchase_transaction_id=semen.id, purchase_date=date(2026, 9, 2), expiry_date=date(2026, 11, 1),
                   unit_cost=D("2000"), purchased_quantity=20, active=True)
    session.add(lot)
    session.flush()
    session.add(SemenStockMovement(semen_lot_id=lot.id, movement_type="PURCHASE", quantity=20, signed_quantity=20,
                                   source_financial_transaction_id=semen.id, recorded_at=_dt(date(2026, 9, 2))))

    # ---- breeding --------------------------------------------------------
    sequence = [0]

    def breed(animal_id, day, event, result, technician="Dr. Asif", lot_id=None):
        sequence[0] += 1
        record_id = f"BR-{sequence[0]:03d}"
        session.add(BreedingRecordModel(
            record_id=record_id, animal_id=animal_id, event_type=event, result=result, technician=technician,
            semen_or_bull="SEXED — HF-777" if event == "insemination" else None, semen_lot_id=lot_id,
            semen_unit_cost=D("2000") if lot_id else None,
            timestamp=datetime.combine(day, time(8, 0), tzinfo=UTC)))
        if lot_id:
            session.add(SemenStockMovement(semen_lot_id=lot_id, movement_type="AI_CONSUMPTION", quantity=1,
                                           signed_quantity=-1, breeding_record_id=record_id,
                                           recorded_at=datetime.combine(day, time(8, 0))))

    breed("M001", date(2026, 6, 1), "calving", "LIVE")
    breed("M001", date(2026, 8, 1), "insemination", "RECORDED")
    breed("M001", date(2026, 9, 6), "pregnancy_diagnosis", "pregnant")          # pregnant, due 11-May-2027
    breed("M002", date(2026, 5, 15), "calving", "LIVE")
    breed("M002", date(2026, 8, 20), "insemination", "RECORDED")                # PD due 24-Sep (not yet)
    breed("M003", date(2026, 5, 1), "calving", "LIVE")
    breed("M003", date(2026, 8, 5), "insemination", "RECORDED", "Bilal")        # PD due 09-Sep (overdue)
    breed("M004", date(2026, 4, 1), "calving", "LIVE")
    breed("M004", date(2026, 6, 10), "insemination", "RECORDED", "Bilal")
    breed("M004", date(2026, 7, 16), "pregnancy_diagnosis", "open", "Bilal")
    breed("M004", date(2026, 7, 20), "insemination", "RECORDED", "Bilal")
    breed("M004", date(2026, 8, 25), "pregnancy_diagnosis", "open", "Bilal")
    breed("M004", date(2026, 9, 1), "insemination", "RECORDED", "Bilal")        # 3rd service: repeat breeder
    breed("M005", date(2026, 3, 1), "calving", "LIVE")
    breed("M005", date(2026, 5, 10), "insemination", "RECORDED")
    breed("M005", date(2026, 6, 15), "pregnancy_diagnosis", "pregnant")
    breed("M005", date(2026, 8, 15), "pregnancy_lost", "MISCARRIAGE")           # open again
    breed("M006", date(2026, 9, 3), "calving", "LIVE")                          # inside waiting period
    breed("D001", date(2025, 10, 1), "calving", "LIVE")
    breed("D001", date(2025, 12, 20), "insemination", "RECORDED")
    breed("D001", date(2026, 1, 25), "pregnancy_diagnosis", "pregnant")         # calving due 29-Sep-2026
    for animal_id, day in (("H002", 5), ("H003", 9), ("H004", 12)):
        breed(animal_id, date(2026, 9, day), "insemination", "RECORDED", lot_id=lot.id)

    # ---- health ----------------------------------------------------------
    case = HealthCase(case_id="HC-0001", animal_id="M007", severity="MODERATE", diagnosis="Mastitis", status="OPEN",
                      opened_at=_dt(date(2026, 9, 10)), opened_by="Dr. Hamid",
                      follow_up_due_at=_dt(date(2026, 9, 15)), withdrawal_until=_dt(date(2026, 9, 20)))
    closed = HealthCase(case_id="HC-0002", animal_id="M008", severity="LOW", diagnosis="Lameness", status="RESOLVED",
                        opened_at=_dt(date(2026, 8, 20)), resolved_at=_dt(date(2026, 8, 27)), resolution="Recovered")
    session.add_all([case, closed])
    session.flush()
    session.add(TreatmentRecord(animal_id="M007", diagnosis="Mastitis", medicine="Oxytetracycline", dose="20 ml",
                                treated_by="Dr. Hamid", treated_at=_dt(date(2026, 9, 10)), milk_withdrawal_days=10,
                                milk_withdrawal_until=_dt(date(2026, 9, 20)), health_case_id=case.id))
    session.add(TreatmentRecord(animal_id="M008", diagnosis="Lameness", medicine="Meloxicam", dose="10 ml",
                                treated_by="Dr. Hamid", treated_at=_dt(date(2026, 8, 20)), milk_withdrawal_days=3,
                                milk_withdrawal_until=_dt(date(2026, 8, 23)), health_case_id=closed.id))
    session.add(VaccinationRecord(animal_id="M001", vaccine="FMD", dose="2 ml", next_due_date=date(2026, 9, 10),
                                  schedule_status="SCHEDULED", status="SCHEDULED", operator="Test"))
    session.add(VaccinationRecord(animal_id="M002", vaccine="FMD", dose="2 ml", next_due_date=date(2026, 9, 25),
                                  schedule_status="SCHEDULED", status="SCHEDULED", operator="Test"))
    session.add(VaccinationRecord(animal_id="M003", vaccine="HS", dose="5 ml", administered_date=date(2026, 9, 5),
                                  schedule_status="ADMINISTERED", status="COMPLETED", operator="Test"))
    session.add(VaccinationRecord(animal_id="M004", vaccine="FMD", dose="2 ml", next_due_date=date(2026, 9, 1),
                                  schedule_status="VOID", status="VOID", operator="Test"))

    # ---- feed cost authority and official COML ---------------------------
    for offset in range(18):
        day = date(2026, 9, 1) + timedelta(days=offset)
        snapshot = {"kind": "TMR_DAILY_COST_SNAPSHOT", "operational_date": day.isoformat(),
                    "basis": "GOVERNED_TMR_X_ACTIVE_HERD_AT_12_00", "herd_counts": {k: len(v) for k, v in HERD.items()},
                    "total_herd_feed_cost_per_day": 25000.0}
        session.add(FeedRation(name=f"TMR Daily Herd Cost {day.isoformat()}", animal_group="TMR_DAILY_COST_SNAPSHOT",
                               ingredients_json=json.dumps(snapshot, sort_keys=True), effective_date=day.isoformat(),
                               operator="TMR_DAILY_12_00_LOCK"))
    session.add(COMLRecord(month_start=date(2026, 8, 1), feed_cost_per_liter=D("52.5"), opex_cost_per_liter=D("12.25"),
                           total_coml_per_liter=D("64.75"), status="OFFICIAL", updated_by="Owner"))
    session.commit()
    return {"sales": {day.isoformat(): row.id for day, row in sales.items()}, "semen_lot_id": lot.id}
