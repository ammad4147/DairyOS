from dairyos.feed import FeedInventoryTransaction
from dairyos.feed.services import FeedInventoryService



def test_receive_feed_inventory():

    service = FeedInventoryService()

    transaction = FeedInventoryTransaction(
        transaction_id="TX-001",
        feed_id="SILAGE-001",
        transaction_type="RECEIVE",
        quantity=1000,
        recorded_by="STORE_MANAGER",
    )

    service.add_transaction(transaction)

    assert len(service.get_transactions()) == 1



def test_feed_inventory_balance():

    service = FeedInventoryService()

    service.add_transaction(
        FeedInventoryTransaction(
            transaction_id="TX-001",
            feed_id="SILAGE-001",
            transaction_type="RECEIVE",
            quantity=1000,
            recorded_by="STORE_MANAGER",
        )
    )

    service.add_transaction(
        FeedInventoryTransaction(
            transaction_id="TX-002",
            feed_id="SILAGE-001",
            transaction_type="ISSUE",
            quantity=200,
            recorded_by="FEED_OPERATOR",
        )
    )


    balance = service.calculate_balance(
        "SILAGE-001"
    )

    assert balance == 800
