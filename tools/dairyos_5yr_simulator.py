import math
import random
import time
import requests
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

API_BASE_URL = "http://127.0.0.1:8000"

@dataclass
class SimulatedAnimal:
    animal_id: str
    ear_tag: str
    animal_type: str
    milking_frequency: int
    dob: datetime
    dam_id: Optional[str] = None
    sire_id: Optional[str] = None
    parity: int = 1
    calving_date: Optional[datetime] = None
    status: str = "ACTIVE"
    lifecycle_status: str = "LACTATING"
    is_alive: bool = True
    conception_date: Optional[datetime] = None
    days_in_milk: int = 0
    recent_yields: List[float] = field(default_factory=list)
    current_health_issue: Optional[Dict[str, Any]] = None
    milk_withholding_days: int = 0

class DairyOS5YearSimulator:
    def __init__(self, api_url: str = API_BASE_URL, start_date_str: str = "2026-01-01"):
        self.api_url = api_url
        self.sim_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        self.herd: Dict[str, SimulatedAnimal] = {}
        self.next_tag_seq = 101
        
        self.accumulated_credit_sales_liters = 0.0
        self.cash_balance = 500000.0
        self.total_revenue = 0.0
        self.total_feed_expense = 0.0
        self.total_opex_expense = 0.0
        self.total_ai_expense = 0.0

        self.injected_anomalies_count = 0
        self.target_anomalies = 10
        self.resolved_alerts_log = []

        self._initialize_foundation_herd()

    def _initialize_foundation_herd(self):
        for i in range(1, 11):
            cow_id = f"COW-3X-{i:02d}"
            tag = f"PK-3X-{self.next_tag_seq}"
            self.next_tag_seq += 1
            calving = self.sim_date - timedelta(days=random.randint(15, 60))
            self.herd[cow_id] = SimulatedAnimal(
                animal_id=cow_id,
                ear_tag=tag,
                animal_type="COW",
                milking_frequency=3,
                dob=self.sim_date - timedelta(days=random.randint(900, 1200)),
                dam_id="FOUNDATION_DAM",
                sire_id="SIRE_GEN_0",
                parity=random.choice([1, 2, 3]),
                calving_date=calving,
                days_in_milk=(self.sim_date - calving).days
            )

        for i in range(1, 11):
            cow_id = f"COW-2X-{i:02d}"
            tag = f"PK-2X-{self.next_tag_seq}"
            self.next_tag_seq += 1
            calving = self.sim_date - timedelta(days=random.randint(15, 60))
            self.herd[cow_id] = SimulatedAnimal(
                animal_id=cow_id,
                ear_tag=tag,
                animal_type="COW",
                milking_frequency=2,
                dob=self.sim_date - timedelta(days=random.randint(900, 1200)),
                dam_id="FOUNDATION_DAM",
                sire_id="SIRE_GEN_0",
                parity=random.choice([1, 2, 3]),
                calving_date=calving,
                days_in_milk=(self.sim_date - calving).days
            )

    def _calculate_daily_yield(self, animal: SimulatedAnimal, force_anomaly: Optional[str] = None) -> float:
        if animal.lifecycle_status != "LACTATING" or animal.days_in_milk <= 0:
            return 0.0

        t = animal.days_in_milk
        a, b, c = 18.0, 0.22, 0.0035
        base_yield = a * (math.pow(t, b)) * math.exp(-c * t)

        freq_multiplier = 1.15 if animal.milking_frequency == 3 else 1.0
        yield_val = base_yield * freq_multiplier
        yield_val += random.gauss(0, 0.6)

        if force_anomaly == "AMBER":
            yield_val *= random.uniform(0.75, 0.82)
        elif force_anomaly == "RED":
            yield_val *= random.uniform(0.50, 0.65)

        return max(round(yield_val, 2), 0.0)

    def run_day(self, day_index: int, speed_delay: float = 0.0):
        date_str = self.sim_date.strftime("%Y-%m-%d")
        daily_total_raw_milk = 0.0
        commercial_bulk_tank = 0.0
        daily_feed_expense = 0.0
        daily_ai_expense = 0.0

        active_calves = [a for a in self.herd.values() if a.is_alive and a.animal_type == "CALF"]
        active_heifers = [a for a in self.herd.values() if a.is_alive and a.animal_type == "HEIFER"]
        active_cows = [a for a in self.herd.values() if a.is_alive and a.animal_type == "COW"]
        lactating_cows = [c for c in active_cows if c.lifecycle_status == "LACTATING"]

        daily_feed_expense += len(active_cows) * 2000.0
        daily_feed_expense += len(active_heifers) * 1300.0
        daily_feed_expense += len(active_calves) * 800.0
        self.total_feed_expense += daily_feed_expense

        # Anomaly Selection with Safety Check
        anomaly_today = None
        target_cow = None
        if self.injected_anomalies_count < self.target_anomalies and day_index % 120 == 40 and lactating_cows:
            target_cow = random.choice(lactating_cows)
            anomaly_today = "RED" if (self.injected_anomalies_count % 2 == 0) else "AMBER"
            self.injected_anomalies_count += 1

        for cow in active_cows:
            if cow.lifecycle_status == "LACTATING":
                cow.days_in_milk += 1
                force_drop = anomaly_today if (target_cow and cow.animal_id == target_cow.animal_id) else None
                day_yield = self._calculate_daily_yield(cow, force_drop)
                daily_total_raw_milk += day_yield

                if cow.milking_frequency == 3:
                    m = round(day_yield * 0.38, 2)
                    a = round(day_yield * 0.32, 2)
                    e = round(day_yield - m - a, 2)
                else:
                    m = round(day_yield * 0.55, 2)
                    a = 0.0
                    e = round(day_yield - m, 2)

                if cow.milk_withholding_days > 0:
                    cow.milk_withholding_days -= 1
                else:
                    commercial_bulk_tank += day_yield

                if force_drop:
                    self._dispatch_health_alert_and_resolution(cow, force_drop, day_yield, date_str)

                cow.recent_yields.append(day_yield)
                if len(cow.recent_yields) > 7:
                    cow.recent_yields.pop(0)

                self._post_milk_record(cow.animal_id, m, a, e, date_str)

        nursing_calves = [c for c in active_calves if (self.sim_date - c.dob).days <= 60]
        calf_milk_deduction = len(nursing_calves) * 8.0
        domestic_quota = 10.0

        net_saleable_milk = max(commercial_bulk_tank - calf_milk_deduction - domestic_quota, 0.0)
        self.accumulated_credit_sales_liters += net_saleable_milk

        daily_opex = daily_total_raw_milk * 25.0
        self.total_opex_expense += daily_opex

        for animal in active_cows + active_heifers:
            if animal.animal_type == "COW" and animal.lifecycle_status == "LACTATING" and animal.days_in_milk >= 65 and not animal.conception_date:
                animal.conception_date = self.sim_date
                daily_ai_expense += 15000.0
                self.total_ai_expense += 15000.0
            elif animal.animal_type == "HEIFER" and (self.sim_date - animal.dob).days >= 425 and not animal.conception_date:
                animal.conception_date = self.sim_date
                daily_ai_expense += 15000.0
                self.total_ai_expense += 15000.0

            if animal.conception_date:
                days_pregnant = (self.sim_date - animal.conception_date).days
                if days_pregnant == 222:
                    animal.lifecycle_status = "DRIED_OFF"
                elif days_pregnant >= 282:
                    self._handle_calving_event(animal)

        self._evaluate_daily_mortality(active_cows, active_heifers, active_calves)

        if day_index % 15 == 0 and day_index > 0:
            settlement_amount = self.accumulated_credit_sales_liters * 225.0
            self.total_revenue += settlement_amount
            self.cash_balance += (settlement_amount - daily_feed_expense * 15 - daily_opex * 15)
            self.accumulated_credit_sales_liters = 0.0

        self.sim_date += timedelta(days=1)
        if speed_delay > 0:
            time.sleep(speed_delay)

    def _handle_calving_event(self, dam: SimulatedAnimal):
        dam.conception_date = None
        dam.calving_date = self.sim_date
        dam.days_in_milk = 0
        dam.lifecycle_status = "LACTATING"
        dam.parity += 1
        dam.animal_type = "COW"

        is_female = random.random() <= 0.70
        calf_id = f"CALF-{self.next_tag_seq:03d}"
        tag = f"PK-FL-{self.next_tag_seq}"
        self.next_tag_seq += 1

        if is_female:
            self.herd[calf_id] = SimulatedAnimal(
                animal_id=calf_id,
                ear_tag=tag,
                animal_type="CALF",
                milking_frequency=dam.milking_frequency,
                dob=self.sim_date,
                dam_id=dam.animal_id,
                sire_id="SIRE_GEN_ELITE",
                lifecycle_status="CALF_NURSING"
            )
        else:
            self.cash_balance += 15000.0

    def _dispatch_health_alert_and_resolution(self, cow: SimulatedAnimal, severity: str, yield_val: float, date_str: str):
        issue = "Clinical Mastitis (Quarter Inflammation)" if severity == "RED" else "Subclinical Mastitis / Ruminal Acidosis"
        treatment = "Intramammary Cefquinome + Flunixin" if severity == "RED" else "Buffer supplement + Probiotics"
        cow.milk_withholding_days = 3 if severity == "RED" else 0

        self.resolved_alerts_log.append({
            "date": date_str,
            "animal_id": cow.animal_id,
            "severity": severity,
            "issue": issue,
            "treatment": treatment,
            "status": "RESOLVED"
        })

        try:
            requests.post(f"{self.api_url}/farm/health-records", json={
                "animal_id": cow.animal_id,
                "observation": issue,
                "symptom": f"Drop in milk yield ({yield_val}L). Treatment: {treatment}",
                "severity": severity,
                "operator": "VET_SIMULATOR"
            }, timeout=0.1)
        except Exception:
            pass

    def _evaluate_daily_mortality(self, cows, heifers, calves):
        for c in cows:
            if random.random() < (0.02 / 365.0):
                c.is_alive = False
                c.status = "DECEASED"
        for h in heifers:
            if random.random() < (0.05 / 365.0):
                h.is_alive = False
                h.status = "DECEASED"
        for k in calves:
            if random.random() < (0.10 / 365.0):
                k.is_alive = False
                k.status = "DECEASED"

    def _post_milk_record(self, animal_id: str, m: float, a: float, e: float, date_str: str):
        try:
            requests.post(f"{self.api_url}/farm/operational-events", json={
                "animal_id": animal_id,
                "morning_yield": m,
                "afternoon_yield": a,
                "evening_yield": e,
                "operator": "SIM_AUTO",
                "date": date_str
            }, timeout=0.05)
        except Exception:
            pass

    def run_5_years(self, speed_delay: float = 0.0):
        print("================================================================")
        print("STARTING 5-YEAR (1,825 DAYS) COMPREHENSIVE DAIRY OS SIMULATION")
        print("================================================================")
        total_days = 1825
        
        for day in range(1, total_days + 1):
            self.run_day(day, speed_delay=speed_delay)

            if day % 365 == 0:
                year = day // 365
                active_cows = len([a for a in self.herd.values() if a.is_alive and a.animal_type == "COW"])
                active_heifers = len([a for a in self.herd.values() if a.is_alive and a.animal_type == "HEIFER"])
                active_calves = len([a for a in self.herd.values() if a.is_alive and a.animal_type == "CALF"])
                
                print(f"[Year {year} Complete | {self.sim_date.strftime('%Y-%m-%d')}]")
                print(f" - Herd Demographics: {active_cows} Milking Cows, {active_heifers} Heifers, {active_calves} Calves")
                print(f" - Financial Summary (PKR): Revenue={self.total_revenue:,.0f} | Feed={self.total_feed_expense:,.0f} | OPEX={self.total_opex_expense:,.0f} | AI={self.total_ai_expense:,.0f}")
                print(f" - Resolved Amber/Red Alerts: {len(self.resolved_alerts_log)} / {self.target_anomalies}")
                print("----------------------------------------------------------------")

        print("\nSIMULATION COMPLETE.")
        print(f"Total Animals in Passport/Lineage Registry: {len(self.herd)}")
        print(f"Total Resolved Health Notifications: {len(self.resolved_alerts_log)}")

if __name__ == "__main__":
    sim = DairyOS5YearSimulator()
    sim.run_5_years(speed_delay=0.0)
