from datetime import datetime

from dairyos.feed import FeedingRecord
from dairyos.feed.services import FeedingService



def test_add_feeding_record():

    service = FeedingService()


    record = FeedingRecord(
        record_id="FD-001",
        animal_group="MILKING_COWS",
        feed_id="CONCENTRATE-001",
        quantity=50,
        feeding_time=datetime.now(),
        worker="WORKER-001",
    )


    service.add_record(record)


    records = service.get_records()


    assert len(records) == 1
    assert records[0].animal_group == "MILKING_COWS"



def test_group_feed_filter():

    service = FeedingService()


    service.add_record(
        FeedingRecord(
            record_id="FD-002",
            animal_group="CALVES",
            feed_id="HAY-001",
            quantity=20,
            feeding_time=datetime.now(),
            worker="WORKER-001",
        )
    )


    calves = service.get_group_records(
        "CALVES"
    )


    assert len(calves) == 1
