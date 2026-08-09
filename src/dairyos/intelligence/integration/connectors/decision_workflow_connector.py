class DecisionWorkflowConnector:
    """
    Connects decision intelligence with workflow intelligence.

    Responsibilities:

    - pass approved decisions to workflow layer
    - maintain loose coupling

    Future extensions:

    - decision validation
    - approval routing
    - decision confidence checks
    """


    def __init__(
        self,
        workflow_gateway=None,
    ):

        self.workflow_gateway = workflow_gateway


    def submit(
        self,
        decision,
    ):

        return {
            "decision": decision,
            "status": "submitted",
        }
