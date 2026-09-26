class StopLossManager:

    INITIAL_SL_POINTS = 5.0
    TRAIL_TRIGGER_POINTS = 0.10
    TRAIL_SL_POINTS = 3.0

    def calculate_initial_sl(self, entry_price):

        return round(
            entry_price - self.INITIAL_SL_POINTS,
            2
        )

    def calculate_trigger_price(self, entry_price):

        return round(
            entry_price + self.TRAIL_TRIGGER_POINTS,
            2
        )

    def calculate_trailing_sl(self, entry_price):

        return round(
            entry_price - self.TRAIL_SL_POINTS,
            2
        )

    def should_trail(
        self,
        entry_price,
        current_price,
        trail_completed,
    ):

        if trail_completed:
            return False

        trigger_price = self.calculate_trigger_price(
            entry_price
        )

        return current_price >= trigger_price