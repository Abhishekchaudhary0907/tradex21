import time
import uuid
import traceback

from config import POLL_INTERVAL_SECONDS

from groww_client import GrowwClient
from position_monitor import PositionMonitor
from sl_manager import StopLossManager
from state_store import StateStore


def extract_smart_order_id(response):

    if not response:
        return None

    if "smart_order_id" in response:
        return response["smart_order_id"]

    payload = response.get("payload")

    if isinstance(payload, dict):
        return payload.get("smart_order_id")

    return None


def extract_orders(response):

    if not response:
        return []

    if "orders" in response:
        return response["orders"]

    payload = response.get("payload")

    if isinstance(payload, dict):
        return payload.get("orders", [])

    return []


def find_existing_gtt(
    active_orders,
    trading_symbol
):

    for order in active_orders:

        if order.get(
            "trading_symbol"
        ) != trading_symbol:
            continue

        if order.get(
            "smart_order_type"
        ) != "GTT":
            continue

        if order.get(
            "status"
        ) != "ACTIVE":
            continue

        return order

    return None


def create_trade_id():

    return (
        f"TRADE-{uuid.uuid4().hex[:10]}"
    )


def main():

    print()
    print("======================================")
    print("     NIFTY MANUAL ENTRY SL BOT")
    print("======================================")
    print()

    groww_client = GrowwClient()

    position_monitor = PositionMonitor(
        groww_client
    )

    sl_manager = StopLossManager()

    state_store = StateStore()

    print("Bot started.")
    print(
        "Waiting for manually entered "
        "NIFTY CE/PE..."
    )
    print()

    while True:

        try:

            # ======================================
            # 1. GET CURRENT POSITIONS
            # ======================================

            positions = (
                position_monitor
                .get_nifty_option_positions()
            )

            # Convert to dictionary for easy lookup
            current_positions = {}

            for position in positions:

                symbol = position.get(
                    "trading_symbol"
                )

                quantity = int(
                    position.get(
                        "quantity",
                        0
                    )
                )

                if not symbol:
                    continue

                if quantity <= 0:
                    continue

                current_positions[symbol] = (
                    position
                )

            # ======================================
            # 2. DETECT CLOSED POSITIONS
            # ======================================

            active_symbols = (
                state_store
                .get_active_symbols()
            )

            for symbol in active_symbols:

                if symbol not in current_positions:

                    print()
                    print(
                        "================================"
                    )

                    print(
                        f"[POSITION CLOSED] {symbol}"
                    )

                    print(
                        "Removing active trade "
                        "state."
                    )

                    print(
                        "================================"
                    )

                    state_store.close_trade(
                        symbol
                    )

            # ======================================
            # 3. GET ACTIVE GTT ORDERS
            # ======================================

            active_orders_response = (
                groww_client
                .get_active_gtt_orders()
            )

            active_orders = extract_orders(
                active_orders_response
            )

            # ======================================
            # 4. PROCESS CURRENT POSITIONS
            # ======================================

            for symbol, position in (
                current_positions.items()
            ):

                quantity = int(
                    position.get(
                        "quantity",
                        0
                    )
                )

                entry_price = float(
                    position.get(
                        "net_price",
                        0
                    )
                )

                if entry_price <= 0:
                    continue

                print()
                print(
                    f"[POSITION] {symbol}"
                )

                print(
                    f"  Quantity : {quantity}"
                )

                print(
                    f"  Entry    : ₹{entry_price:.2f}"
                )

                # ==================================
                # 5. GET ACTIVE TRADE STATE
                # ==================================

                trade = (
                    state_store
                    .get_active_trade(symbol)
                )

                # ==================================
                # 6. NEW TRADE
                # ==================================

                if trade is None:

                    trade_id = create_trade_id()

                    initial_sl = (
                        sl_manager
                        .calculate_initial_sl(
                            entry_price
                        )
                    )

                    trigger_price = (
                        sl_manager
                        .calculate_trigger_price(
                            entry_price
                        )
                    )

                    trailing_sl = (
                        sl_manager
                        .calculate_trailing_sl(
                            entry_price
                        )
                    )

                    trade = {

                        "trade_id": trade_id,

                        "symbol": symbol,

                        "entry_price": entry_price,

                        "quantity": quantity,

                        "initial_sl": initial_sl,

                        "trigger_price": trigger_price,

                        "trailing_sl": trailing_sl,

                        "smart_order_id": None,

                        "trail_completed": False,

                        "status": "ACTIVE",

                    }

                    state_store.create_trade(
                        symbol,
                        trade
                    )

                    print()
                    print(
                        "================================"
                    )

                    print(
                        "[NEW TRADE DETECTED]"
                    )

                    print(
                        f"Trade ID    : {trade_id}"
                    )

                    print(
                        f"Symbol      : {symbol}"
                    )

                    print(
                        f"Entry       : ₹{entry_price:.2f}"
                    )

                    print(
                        f"Initial SL  : ₹{initial_sl:.2f}"
                    )

                    print(
                        f"Trigger     : ₹{trigger_price:.2f}"
                    )

                    print(
                        f"New SL      : ₹{trailing_sl:.2f}"
                    )

                    print(
                        "================================"
                    )

                else:

                    # IMPORTANT:
                    #
                    # Do NOT overwrite the original
                    # entry price.
                    #
                    # The trade's entry price is fixed
                    # for the lifetime of this trade.

                    entry_price = float(
                        trade["entry_price"]
                    )

                    print(
                        f"  Trade ID : "
                        f"{trade['trade_id']}"
                    )

                # ==================================
                # 7. IF TRAILING ALREADY COMPLETED
                # ==================================

                if trade["trail_completed"]:

                    print(
                        "[LOCKED] "
                        "Automatic SL modification "
                        "already completed."
                    )

                    continue

                # ==================================
                # 8. FIND EXISTING GTT
                # ==================================

                existing_gtt = find_existing_gtt(
                    active_orders,
                    symbol
                )

                # ==================================
                # 9. CREATE INITIAL SL
                # ==================================

                if trade["smart_order_id"] is None:

                    if existing_gtt:

                        smart_order_id = (
                            existing_gtt.get(
                                "smart_order_id"
                            )
                        )

                        if smart_order_id:

                            trade[
                                "smart_order_id"
                            ] = smart_order_id

                            state_store.update_trade(
                                symbol,
                                trade
                            )

                            print(
                                "[EXISTING GTT FOUND]"
                            )

                            print(
                                f"  GTT ID : "
                                f"{smart_order_id}"
                            )

                    else:

                        initial_sl = (
                            trade["initial_sl"]
                        )

                        print()
                        print(
                            "[CREATING INITIAL SL]"
                        )

                        print(
                            f"  Symbol : {symbol}"
                        )

                        print(
                            f"  SL     : "
                            f"₹{initial_sl:.2f}"
                        )

                        response = (
                            groww_client
                            .create_initial_sl(

                                trading_symbol=symbol,

                                quantity=quantity,

                                trigger_price=initial_sl,
                            )
                        )

                        smart_order_id = (
                            extract_smart_order_id(
                                response
                            )
                        )

                        if not smart_order_id:

                            print(
                                "[ERROR] "
                                "Could not obtain "
                                "smart_order_id."
                            )

                            print(response)

                            continue

                        trade[
                            "smart_order_id"
                        ] = smart_order_id

                        state_store.update_trade(
                            symbol,
                            trade
                        )

                        print(
                            "[INITIAL SL CREATED]"
                        )

                        print(
                            f"  GTT ID : "
                            f"{smart_order_id}"
                        )

                # ==================================
                # 10. GET CURRENT LTP
                # ==================================

                current_price = (
                    groww_client
                    .get_ltp(symbol)
                )

                if current_price is None:

                    print(
                        "[WARNING] "
                        f"LTP unavailable for "
                        f"{symbol}"
                    )

                    continue

                current_price = float(
                    current_price
                )

                print(
                    f"  LTP      : "
                    f"₹{current_price:.2f}"
                )

                print(
                    f"  Trigger  : "
                    f"₹{trade['trigger_price']:.2f}"
                )

                # ==================================
                # 11. CHECK TRIGGER
                # ==================================

                should_trail = (
                    sl_manager.should_trail(

                        entry_price=entry_price,

                        current_price=current_price,

                        trail_completed=(
                            trade[
                                "trail_completed"
                            ]
                        ),
                    )
                )

                if not should_trail:

                    continue

                # ==================================
                # 12. MODIFY SL
                # ==================================

                new_sl = trade[
                    "trailing_sl"
                ]

                smart_order_id = trade[
                    "smart_order_id"
                ]

                print()
                print(
                    "======================================"
                )

                print(
                    "[TRIGGER HIT]"
                )

                print(
                    f"Trade ID    : "
                    f"{trade['trade_id']}"
                )

                print(
                    f"Symbol      : {symbol}"
                )

                print(
                    f"Entry       : "
                    f"₹{entry_price:.2f}"
                )

                print(
                    f"Current LTP : "
                    f"₹{current_price:.2f}"
                )

                print(
                    f"Old SL      : "
                    f"₹{trade['initial_sl']:.2f}"
                )

                print(
                    f"New SL      : "
                    f"₹{new_sl:.2f}"
                )

                print(
                    "======================================"
                )

                response = (
                    groww_client
                    .modify_sl(

                        smart_order_id=(
                            smart_order_id
                        ),

                        quantity=quantity,

                        trigger_price=new_sl,
                    )
                )

                print(
                    "[GROWW MODIFY RESPONSE]"
                )

                print(response)

                # ==================================
                # 13. CONFIRM SUCCESS
                # ==================================

                success = False

                if isinstance(
                    response,
                    dict
                ):

                    status = response.get(
                        "status"
                    )

                    payload = response.get(
                        "payload"
                    )

                    if status == "SUCCESS":

                        success = True

                    elif isinstance(
                        payload,
                        dict
                    ):

                        payload_status = (
                            payload.get(
                                "status"
                            )
                        )

                        if payload_status in (
                            "SUCCESS",
                            "ACTIVE",
                        ):

                            success = True

                # ==================================
                # 14. ONLY LOCK AFTER SUCCESS
                # ==================================

                if success:

                    trade[
                        "trail_completed"
                    ] = True

                    trade[
                        "final_sl"
                    ] = new_sl

                    state_store.update_trade(
                        symbol,
                        trade
                    )

                    print()
                    print(
                        "********************************"
                    )

                    print(
                        "[SUCCESS]"
                    )

                    print(
                        f"SL modified to "
                        f"₹{new_sl:.2f}"
                    )

                    print(
                        "[LOCKED]"
                    )

                    print(
                        "Bot will NOT modify "
                        "this trade's SL again."
                    )

                    print(
                        "********************************"
                    )

                else:

                    print()
                    print(
                        "[MODIFICATION NOT CONFIRMED]"
                    )

                    print(
                        "The trade remains active."
                    )

                    print(
                        "The bot will retry on "
                        "the next cycle."
                    )

            # ======================================
            # 15. WAIT
            # ======================================

            time.sleep(
                POLL_INTERVAL_SECONDS
            )

        except KeyboardInterrupt:

            print()
            print(
                "Bot stopped by user."
            )

            break

        except Exception as error:

            print()
            print(
                "[ERROR]",
                str(error)
            )

            traceback.print_exc()

            print(
                "Retrying in 2 seconds..."
            )

            time.sleep(2)


if __name__ == "__main__":
    main()