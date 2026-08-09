from datetime import datetime

from dairyos.feed import FeedingRecord
from dairyos.feed.services import FeedClosureService



def test_complete_feeding_day():

    service = FeedClosureService()


    records = []


    for session in [
        "MORNING",
        "AFTERNOON",
        "EVENING",
    ]:

        record = FeedingRecord(
            record_id=session,
            animal_group="MILKING_COWS",
            feed_id="SILAGE-001",
            quantity=100,
            feeding_time=datetime.now(),
            worker="WORKER",
        )

        record.session = session

        records.append(record)



    assert service.validate_day(records) is True
