from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)


class FinancialIntelligenceService:
    """
    Operational intelligence for farm financial execution.

    Converts financial operational state into
    actionable attention items.

    Rules:
    - Reads FarmOperationalState only.
    - Does not modify financial facts.
    - Does not perform accounting.
    - Does not replace financial management.

    Financial truth remains inside:
        FarmOperationalState.financial_status
    """



    def evaluate(
        self,
        state: FarmOperationalState,
    ) -> list[dict]:
        """
        Evaluate financial operational condition.

        Returns operational attention items.
        """

        decisions = []


        financial_status = (
            state.financial_status
            if state.financial_status
            else {}
        )


        self._check_financial_status(
            financial_status,
            decisions,
        )


        self._check_cash_reserve(
            financial_status,
            decisions,
        )


        self._check_financial_visibility(
            financial_status,
            decisions,
        )


        return decisions



    def _check_financial_status(
        self,
        financial_status,
        decisions,
    ):
        """
        Detect financial awareness conditions.
        """

        for financial_id, financial in (
            financial_status.items()
        ):

            awareness_status = financial.get(
                "awareness_status",
                "",
            )


            if (
                isinstance(
                    awareness_status,
                    str,
                )
                and
                awareness_status.upper()
                in (
                    "WARNING",
                    "CRITICAL",
                )
            ):

                decisions.append(
                    {
                        "type":
                            "financial",

                        "priority":
                            "HIGH",

                        "action":
                            "review_financial_position",

                        "title":
                            "Review financial operational status",

                        "details":
                            {
                                "financial_id":
                                    financial_id,

                                "financial":
                                    financial,
                            },
                    }
                )



    def _check_cash_reserve(
        self,
        financial_status,
        decisions,
    ):
        """
        Detect cash reserve risk.
        """

        for financial_id, financial in (
            financial_status.items()
        ):

            cash_available = financial.get(
                "cash_available"
            )

            minimum_cash_required = financial.get(
                "minimum_cash_required"
            )


            if (
                cash_available is not None
                and minimum_cash_required is not None
                and
                cash_available < minimum_cash_required
            ):

                decisions.append(
                    {
                        "type":
                            "financial",

                        "priority":
                            "HIGH",

                        "action":
                            "review_cash_reserve",

                        "title":
                            "Cash reserve below operational threshold",

                        "details":
                            {
                                "financial_id":
                                    financial_id,

                                "financial":
                                    financial,
                            },
                    }
                )



    def _check_financial_visibility(
        self,
        financial_status,
        decisions,
    ):
        """
        Detect missing financial operational visibility.
        """

        if not financial_status:

            decisions.append(
                {
                    "type":
                        "financial",

                    "priority":
                        "WARNING",

                    "action":
                        "record_financial_activity",

                    "title":
                        "Financial operational data unavailable",

                    "details":
                        {},
                }
            )
