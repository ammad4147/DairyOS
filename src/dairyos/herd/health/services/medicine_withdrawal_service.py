from datetime import datetime, UTC



class MedicineWithdrawalService:
    """
    Tracks medicine withdrawal periods to ensure milk safety compliance.

    Prevents sale of milk from animals under active withdrawal.
    """



    # Withdrawal periods in HOURS after treatment
    WITHDRAWAL_PERIODS = {
        ""ANTIBIOTIC_A"": 72,
        ""ANTIBIOTIC_B"": 96,
        ""ANTIBIOTIC_C"": 120,
        ""ANTI_INFLAMMATORY"": 48,
        ""DEWORMER"": 24,
        ""MASTITIS_TREATMENT"": 60,
        ""FOOT_BATH"": 0,
        ""VITAMIN_INJECTION"": 0,
    }



    def record_treatment(
        self,
        animal_id: str,
        medicine_code: str,
        treatment_time: datetime | None = None,
    ):
        """
        Record a treatment event. Returns the expected clearance time.
        """
        treatment_time = treatment_time or datetime.now(UTC)

        code_upper = str(medicine_code or """").strip().upper()

        required_hours = self.WITHDRAWAL_PERIODS.get(code_upper, 48)

        clearance_time = treatment_time + __import__('datetime').timedelta(hours=required_hours)



        return {
            ""animal_id"": animal_id,
            ""medicine_code"": code_upper,
            ""treatment_time"": treatment_time.isoformat(),
            ""required_hours"": required_hours,
            ""clearance_time"": clearance_time.isoformat(),
            ""milk_safe"": False,
            ""status"": ""WITHDRAWAL_ACTIVE"",
        }



    def check_withdrawal_status(
        self,
        animal_id: str,
        medicine_code: str,
        treatment_time: datetime,
        current_time: datetime | None = None,
    ):
        """
        Check if milk is safe to sell from this animal.
        """
        current_time = current_time or datetime.now(UTC)

        code_upper = str(medicine_code or """").strip().upper()

        required_hours = self.WITHDRAWAL_PERIODS.get(code_upper, 48)

        hours_elapsed = (current_time - treatment_time).total_seconds() / 3600.0

        hours_remaining = required_hours - hours_elapsed



        if hours_remaining <= 0:

            return {
                ""animal_id"": animal_id,
                ""medicine_code"": code_upper,
                ""status"": ""CLEAR"",
                ""milk_safe"": True,
                ""hours_remaining"": 0.0,
                ""message"": ""Milk is safe for sale and consumption."",
            }

        else:

            return {
                ""animal_id"": animal_id,
                ""medicine_code"": code_upper,
                ""status"": ""WITHDRAWAL_ACTIVE"",
                ""milk_safe"": False,
                ""hours_remaining"": round(hours_remaining, 1),
                ""message"": f""Milk NOT safe. Wait {round(hours_remaining, 1)} more hours."",
            }



    def get_all_active_withdrawals(
        self,
        treatments: list,
        current_time: datetime | None = None,
    ):
        """
        Filter a list of treatments to find only active withdrawals.
        """
        current_time = current_time or datetime.now(UTC)

        active = []

        for t in treatments:
            status = self.check_withdrawal_status(
                t[""animal_id""],
                t[""medicine_code""],
                t[""treatment_time""],
                current_time,
            )
            if not status[""milk_safe""]:
                active.append(status)

        return active
