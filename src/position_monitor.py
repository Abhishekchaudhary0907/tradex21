class PositionMonitor:

    def __init__(self, groww_client):

        self.client = groww_client

    def get_nifty_option_positions(self):

        response = self.client.get_fno_positions()

        positions = response.get("positions", [])

        result = []

        for position in positions:

            symbol = position.get("trading_symbol", "")

            quantity = position.get("quantity", 0)

            if quantity is None:
                continue

            quantity = int(quantity)

            # We only handle LONG option positions
            if quantity <= 0:
                continue

            # NIFTY option only
            is_nifty = symbol.startswith("NIFTY")

            is_option = (
                symbol.endswith("CE")
                or symbol.endswith("PE")
            )

            if not is_nifty:
                continue

            if not is_option:
                continue

            result.append(position)

        return result