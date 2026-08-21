class MilkMassBalanceService:
    """
    Reconciles milk production against sales, waste, and inventory change.

    Detects spillage, theft, or recording errors by comparing
    what was produced vs. what was accounted for.
    """

    def reconcile(
        self,
        production_litres: float,
        sales_litres: float,
        waste_litres: float = 0.0,
        inventory_change_litres: float = 0.0,
    ):
        """
        production_litres: Total milk produced (from MilkRecordingService)
        sales_litres: Total milk sold (from MilkSalesManagementService)
        waste_litres: Spillage, spoilage, or rejected milk
        inventory_change_litres: Positive = stock increased, Negative = stock decreased
        """

        production_litres = max(0.0, float(production_litres or 0.0))
        sales_litres = max(0.0, float(sales_litres or 0.0))
        waste_litres = max(0.0, float(waste_litres or 0.0))
        inventory_change_litres = float(inventory_change_litres or 0.0)

        expected = production_litres
        actual = sales_litres + waste_litres + inventory_change_litres
        variance = expected - actual

        variance_pct = (
            round((variance / production_litres) * 100, 2)
            if production_litres > 0.001
            else 0.0
        )

        if abs(variance_pct) <= 1.0:
            status = "BALANCED"
            action = "No action required"
        elif abs(variance_pct) <= 5.0:
            status = "ACCEPTABLE_VARIANCE"
            action = "Monitor trends — minor variance within tolerance"
        else:
            status = "INVESTIGATE"
            action = (
                "Immediate review: check for theft, spillage, "
                "or recording errors"
            )

        return {
            "production_litres": round(production_litres, 3),
            "sales_litres": round(sales_litres, 3),
            "waste_litres": round(waste_litres, 3),
            "inventory_change_litres": round(inventory_change_litres, 3),
            "actual_accounted_litres": round(actual, 3),
            "variance_litres": round(variance, 3),
            "variance_pct": variance_pct,
            "status": status,
            "action": action,
            "investigation_required": status == "INVESTIGATE",
        }
