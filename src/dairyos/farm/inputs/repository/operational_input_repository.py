from datetime import datetime, timezone


class OperationalInputRepository:
    """
    Persistence boundary for operational inputs.

    Initial implementation keeps the contract
    independent from storage technology.
    """


    def __init__(self):

        self._records = []



    def save(
        self,
        record,
    ):

        self._records.append(
            record
        )

        return record



    def list_all(
        self,
    ):

        return list(
            self._records
        )



    def find_by_type(
        self,
        input_type,
    ):

        return [

            record

            for record in self._records

            if record.input_type == input_type

        ]
