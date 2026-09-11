"""Optional Woods lactation-curve forecasting support."""

try:
    import numpy as np
    from scipy.optimize import curve_fit
except ModuleNotFoundError:  # Optional legacy forecasting capability.
    np = None
    curve_fit = None


def _require_forecasting_dependencies() -> None:
    """Raise an actionable error when optional math packages are absent."""
    if np is None or curve_fit is None:
        raise RuntimeError(
            "Woods yield forecasting requires the optional numpy and scipy "
            "dependencies. Install the DairyOS forecasting extra before use."
        )


class WoodsYieldForecaster:
    """Predictive engine for modeling 305-day lactation curves."""

    @staticmethod
    def _woods_equation(dim, a, b, c):
        """The mathematical function for Wood's Lactation Model."""
        _require_forecasting_dependencies()
        # Using np.float64 to prevent overflow errors in exponential calculations
        dim = np.asarray(dim, dtype=np.float64)
        return a * (dim**b) * np.exp(-c * dim)

    def fit_cow_curve(
        self,
        days_in_milk: list[int],
        yields: list[float],
    ) -> tuple[float, float, float]:
        """
        Fits early lactation data to find the optimal a, b, c parameters for a specific cow.
        Requires at least 14 days of data for a reliable curve.
        """
        if len(days_in_milk) < 14:
            raise ValueError(
                "Insufficient data: At least 14 days of milk weights required "
                "for prediction."
            )

        _require_forecasting_dependencies()
        # p0 represents initial guesses for [a, b, c] based on standard Holstein curves
        initial_guesses = [15.0, 0.2, 0.004]

        try:
            # curve_fit runs a non-linear least squares optimization
            optimized_params, _ = curve_fit(
                self._woods_equation,
                days_in_milk,
                yields,
                p0=initial_guesses,
                maxfev=5000,
            )
            return tuple(optimized_params)  # Returns (a, b, c)
        except RuntimeError as exc:
            raise ValueError(
                "Curve fitting failed to converge. Data may be too erratic."
            ) from exc

    def project_305_days(
        self,
        a: float,
        b: float,
        c: float,
    ) -> dict[str, object]:
        """Projects the daily yields and calculates the total 305-day volume."""
        _require_forecasting_dependencies()
        projection_days = np.arange(1, 306)
        projected_yields = self._woods_equation(projection_days, a, b, c)

        peak_yield_day = int(b / c) if c > 0 else 0
        total_305_volume = float(np.sum(projected_yields))

        return {
            "total_projected_volume": total_305_volume,
            "projected_peak_day": peak_yield_day,
            "projected_peak_yield": float(
                self._woods_equation(peak_yield_day, a, b, c)
            ),
            "daily_forecast": projected_yields.tolist(),
        }
