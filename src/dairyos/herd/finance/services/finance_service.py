from dairyos.data.repositories.repository_factory import RepositoryFactory


class FinanceService:


    def __init__(self, session=None):

        self.session = session

        self.costs = []

        self.revenues = []

        self.repository = None

        if session is not None:

            self.repository = (
                RepositoryFactory(session)
                .financial_repository()
            )


    def record_cost(self, cost):

        if self.repository:

            self.repository.add(cost)

        else:

            self.costs.append(cost)

        return cost


    def record_revenue(self, revenue):

        if self.repository:

            self.repository.add(revenue)

        else:

            self.revenues.append(revenue)

        return revenue


    def cost_count(self):

        if self.repository:

            return sum(
                1
                for transaction in self.repository.get_all()
                if transaction.transaction_type == "EXPENSE"
            )

        return len(self.costs)


    def revenue_count(self):

        if self.repository:

            return sum(
                1
                for transaction in self.repository.get_all()
                if transaction.transaction_type == "INCOME"
            )

        return len(self.revenues)


    def total_costs(self):

        if self.repository:

            return self.repository.total_expenses()

        return sum(
            cost.total_cost
            if hasattr(cost, "total_cost")
            else cost
            for cost in self.costs
        )


    def total_revenues(self):

        if self.repository:

            return self.repository.total_income()

        return sum(
            revenue.total_revenue
            if hasattr(revenue, "total_revenue")
            else revenue
            for revenue in self.revenues
        )


    def net_profit(self):

        return (
            self.total_revenues()
            -
            self.total_costs()
        )
