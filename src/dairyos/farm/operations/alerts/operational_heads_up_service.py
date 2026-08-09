from typing import List
from datetime import datetime, timezone

from dairyos.farm.operations.alerts.heads_up_notification import (
    HeadsUpNotification,
)


class OperationalHeadsUpService:
    """
    Generates operational awareness notifications.

    Rules:
    - Notifications are derived from operational state.
    - Notifications never mutate farm facts.
    - Manual operational entry remains source of truth.
    """

    def __init__(
        self,
        input_notification_service=None,
    ):

        self.input_notification_service = (
            input_notification_service
        )

    def project_to_state(
        self,
        projection,
    ):

        return projection



    def evaluate(
        self,
        state,
    ) -> List[HeadsUpNotification]:

        notifications = []


        tasks = self._get_tasks(
            state
        )


        exceptions = getattr(
            state,
            "exceptions",
            []
        )


        notifications.extend(
            self._evaluate_task_priority(
                tasks
            )
        )


        notifications.extend(
            self._evaluate_overdue_tasks(
                tasks
            )
        )


        notifications.extend(
            self._evaluate_inventory(
                state
            )
        )


        notifications.extend(
            self._evaluate_equipment(
                state
            )
        )


        notifications.extend(
            self._evaluate_breeding(
                state
            )
        )


        notifications.extend(
            self._evaluate_workforce(
                state
            )
        )


        notifications.extend(
            self._evaluate_financial_status(
                state
            )
        )


        if tasks:

            notifications.append(
                HeadsUpNotification(
                    notification_type="OPEN_TASKS",
                    message="Open operational tasks require attention",
                    severity="WARNING",
                )
            )


        if exceptions:

            notifications.append(
                HeadsUpNotification(
                    notification_type="OPERATIONAL_EXCEPTION",
                    message="Operational exceptions require investigation",
                    severity="CRITICAL",
                )
            )


        if self.input_notification_service:

            input_notification = (
                self.input_notification_service
                .evaluate()
            )


            if input_notification:

                notifications.append(
                    HeadsUpNotification(
                        notification_type=
                            input_notification.notification_type,

                        message=
                            input_notification.message,

                        severity=
                            input_notification.severity,
                    )
                )


        return notifications



    def _evaluate_financial_status(
        self,
        state,
    ):

        notifications = []

        financial_status = getattr(
            state,
            "financial_status",
            {},
        )


        for financial in financial_status.values():

            if not isinstance(
                financial,
                dict,
            ):
                continue


            awareness = financial.get(
                "awareness_status"
            )


            if awareness in (
                "WARNING",
                "CRITICAL",
            ):

                notifications.append(
                    HeadsUpNotification(
                        notification_type="FINANCIAL_AWARENESS",
                        message="Financial operational status requires attention",
                        severity=awareness,
                    )
                )


            cash_available = financial.get(
                "cash_available"
            )

            minimum_cash_required = financial.get(
                "minimum_cash_required"
            )


            if (
                cash_available is not None
                and minimum_cash_required is not None
                and cash_available < minimum_cash_required
            ):

                notifications.append(
                    HeadsUpNotification(
                        notification_type="CASH_RESERVE_WARNING",
                        message="Cash available below operational reserve threshold",
                        severity="CRITICAL",
                    )
                )


        return notifications



    def _evaluate_inventory(
        self,
        state,
    ):

        notifications = []

        for inventory in getattr(
            state,
            "inventory_status",
            {},
        ).values():

            if inventory.get(
                "status"
            ) == "CRITICAL":

                notifications.append(
                    HeadsUpNotification(
                        notification_type="INVENTORY_CRITICAL",
                        message="Inventory shortage requires attention",
                        severity="CRITICAL",
                    )
                )

        return notifications



    def _evaluate_equipment(
        self,
        state,
    ):

        notifications = []

        for equipment in getattr(
            state,
            "equipment_status",
            {},
        ).values():

            if equipment.get(
                "operational_status"
            ) == "ATTENTION":

                notifications.append(
                    HeadsUpNotification(
                        notification_type="EQUIPMENT_ATTENTION",
                        message="Equipment requires maintenance attention",
                        severity="WARNING",
                    )
                )

        return notifications



    def _evaluate_breeding(
        self,
        state,
    ):

        notifications = []

        for breeding in getattr(
            state,
            "breeding_status",
            {},
        ).values():

            if breeding.get(
                "result"
            ) in (
                "failed",
                "negative",
            ):

                notifications.append(
                    HeadsUpNotification(
                        notification_type="BREEDING_FOLLOW_UP",
                        message="Breeding status requires follow-up",
                        severity="WARNING",
                    )
                )

        return notifications



    def _evaluate_workforce(
        self,
        state,
    ):

        notifications = []

        workforce = getattr(
            state,
            "workforce_status",
            {},
        )


        for metric in (
            "pending_tasks",
            "overdue_tasks",
        ):

            if workforce.get(
                metric
            ):

                notifications.append(
                    HeadsUpNotification(
                        notification_type="WORKFORCE_LOAD",
                        message="Workforce workload requires attention",
                        severity="WARNING",
                    )
                )

        return notifications



    def _get_tasks(
        self,
        state,
    ):

        tasks = getattr(
            state,
            "open_tasks",
            None
        )


        if tasks is not None:

            return tasks


        tasks = getattr(
            state,
            "tasks",
            None
        )


        if tasks is not None:

            return tasks


        return []



    def _evaluate_task_priority(
        self,
        tasks,
    ):

        notifications = []


        for task in tasks:

            priority = (
                task.get("priority")
                if isinstance(task, dict)
                else getattr(
                    task,
                    "priority",
                    None,
                )
            )


            if priority == "HIGH":

                notifications.append(
                    HeadsUpNotification(
                        notification_type="HIGH_PRIORITY_TASK",
                        message="High priority operational task pending",
                        severity="WARNING",
                    )
                )


        return notifications



    def _evaluate_overdue_tasks(
        self,
        tasks,
    ):

        notifications = []

        now = datetime.now(
            timezone.utc
        )


        for task in tasks:

            due_date = (
                task.get("due_date")
                if isinstance(task, dict)
                else getattr(
                    task,
                    "due_date",
                    None,
                )
            )


            if due_date is None:

                continue


            if isinstance(
                due_date,
                str,
            ):

                try:

                    due_date = datetime.fromisoformat(
                        due_date
                    )

                except ValueError:

                    continue


            if due_date.tzinfo is None:

                due_date = due_date.replace(
                    tzinfo=timezone.utc
                )


            if due_date < now:

                notifications.append(
                    HeadsUpNotification(
                        notification_type="OVERDUE_TASK",
                        message="Operational task is overdue",
                        severity="WARNING",
                    )
                )


        return notifications
