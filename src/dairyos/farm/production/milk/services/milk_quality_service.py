from datetime import datetime

from dairyos.farm.production.milk.models.milk_quality_record import (
    MilkQualityRecord,
)


class MilkQualityService:
    """Handles milk quality testing, averaging, and premium eligibility."""

    def __init__(self, repository):
        self.repository = repository

    def record_quality(self, record: MilkQualityRecord):
        return self.repository.save(record)

    def average_quality(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ):
        """
        Calculate weighted-average quality metrics by volume.
        Returns None if no records found.
        """
        records = self.repository.get_all()

        if date_from is not None:
            records = [
                r
                for r in records
                if r.recorded_at is not None and r.recorded_at >= date_from
            ]

        if date_to is not None:
            records = [
                r
                for r in records
                if r.recorded_at is not None and r.recorded_at <= date_to
            ]

        if not records:
            return None

        total_litres = sum(r.litres for r in records)

        if total_litres <= 0.001:
            return None

        weighted_fat = (
            sum(r.litres * r.fat_pct for r in records) / total_litres
        )
        weighted_snf = (
            sum(r.litres * r.snf_pct for r in records) / total_litres
        )
        weighted_density = (
            sum(r.litres * r.density for r in records) / total_litres
        )

        avg_bacteria = sum(r.bacterial_count for r in records) / len(records)

        premium_eligible = (
            weighted_fat >= 3.5
            and weighted_snf >= 8.5
            and avg_bacteria <= 100000
        )

        return {
            "avg_fat_pct": round(weighted_fat, 2),
            "avg_snf_pct": round(weighted_snf, 2),
            "avg_density": round(weighted_density, 3),
            "avg_bacterial_count": round(avg_bacteria, 0),
            "total_litres": round(total_litres, 3),
            "record_count": len(records),
            "premium_eligible": premium_eligible,
            "quality_grade": "PREMIUM" if premium_eligible else "STANDARD",
        }

    def check_compliance(self, record: MilkQualityRecord):
        """Check if a single record meets food safety standards."""
        issues = []

        if record.fat_pct < 3.0:
            issues.append("Fat percentage below minimum (3.0%)")

        if record.snf_pct < 8.0:
            issues.append("SNF below minimum (8.0%)")

        if record.bacterial_count > 200000:
            issues.append("Bacterial count exceeds safety limit (200,000/ml)")

        if record.density < 1.028 or record.density > 1.034:
            issues.append("Density outside normal range (1.028 - 1.034)")

        return {
            "record_id": record.record_id,
            "compliant": len(issues) == 0,
            "issues": issues,
        }
