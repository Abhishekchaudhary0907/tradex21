import json
import os


class StateStore:

    def __init__(self, filename="state.json"):
        self.filename = filename
        self.state = self._load()

    def _load(self):
        if not os.path.exists(self.filename):
            return {
                "active_trades": {},
                "closed_trades": []
            }

        try:
            with open(
                self.filename,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            # Safety for old state.json files
            if "active_trades" not in data:
                data = {
                    "active_trades": {},
                    "closed_trades": []
                }

            return data

        except Exception:
            return {
                "active_trades": {},
                "closed_trades": []
            }

    def save(self):
        temp_file = f"{self.filename}.tmp"

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                self.state,
                file,
                indent=4
            )

        os.replace(
            temp_file,
            self.filename
        )

    def get_active_trade(self, symbol):
        return self.state["active_trades"].get(symbol)

    def create_trade(self, symbol, trade):
        self.state["active_trades"][symbol] = trade
        self.save()

    def update_trade(self, symbol, trade):
        self.state["active_trades"][symbol] = trade
        self.save()

    def close_trade(self, symbol):
        trade = self.state["active_trades"].pop(
            symbol,
            None
        )

        if trade is not None:
            trade["status"] = "CLOSED"

            self.state["closed_trades"].append(trade)

        self.save()

    def get_active_symbols(self):
        return set(
            self.state["active_trades"].keys()
        )
    