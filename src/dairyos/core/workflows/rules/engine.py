class WorkflowEngine:


    def __init__(self):

        self.rules = []


    def add_rule(self, rule):

        self.rules.append(rule)


    def evaluate(self, event):

        results = []

        for rule in self.rules:

            result = rule(event)

            if result:
                results.append(result)

        return results
