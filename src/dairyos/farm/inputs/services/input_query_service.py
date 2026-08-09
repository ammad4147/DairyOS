class InputQueryService:
    """
    Read service for operational input history.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def list_inputs(
        self,
    ):

        return (
            self.repository
            .list_all()
        )



    def list_all(
        self,
    ):

        return self.list_inputs()



    def list_by_type(
        self,
        input_type,
    ):

        return (
            self.repository
            .find_by_type(
                input_type
            )
        )
