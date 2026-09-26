from growwapi import GrowwFeed


class MarketFeed:

    def __init__(self, groww_client):

        self.groww_client = groww_client

        self.feed = GrowwFeed(
            groww_client.groww
        )

    def subscribe(self, instruments):

        self.feed.subscribe_ltp(
            instruments
        )

    def get_ltp(self):

        return self.feed.get_ltp()

    def unsubscribe(self, instruments):

        self.feed.unsubscribe_ltp(
            instruments
        )