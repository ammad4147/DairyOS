from typing import List

from ..models.execution_performance_record import (
    ExecutionPerformanceRecord,
)


class PerformanceBridge:
    """
    Converts execution accountability
    into measurable performance records.
    """


    def __init__(self):

        self.records: List[
            ExecutionPerformanceRecord
        ] = []


    def evaluate_execution(
        self,
        accountability_record,
    ) -> ExecutionPerformanceRecord:


        if accountability_record.status == "COMPLETED":

            score = 100.0

        else:

            score = 50.0


        record = ExecutionPerformanceRecord(

            execution_id=(
                accountability_record.execution_id
            ),

            staff_member=(
                accountability_record.staff_member
            ),

            task_name=(
                accountability_record.task_name
            ),

            completion_status=(
                accountability_record.status
            ),

            performance_score=score,

        )


        self.records.append(record)


        return record



    def get_records(
        self,
    ) -> List[ExecutionPerformanceRecord]:

        return self.records
