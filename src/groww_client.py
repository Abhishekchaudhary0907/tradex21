from growwapi import GrowwAPI

from .config import (
    GROWW_API_KEY,
    GROWW_API_SECRET,
)


class GrowwClient:

    def __init__(self):

        print("Authenticating with Groww...")

        access_token = GrowwAPI.get_access_token(
            api_key=GROWW_API_KEY,
            secret=GROWW_API_SECRET,
        )

        self.groww = GrowwAPI(access_token)

        print("Groww authentication successful.")

    # ==============================================
    # POSITIONS
    # ==============================================

    def get_fno_positions(self):

        return self.groww.get_positions_for_user(
            segment=self.groww.SEGMENT_FNO
        )

    # ==============================================
    # LTP
    # ==============================================

    def get_ltp(self, trading_symbol):

        exchange_symbol = f"NSE_{trading_symbol}"

        response = self.groww.get_ltp(
            segment=self.groww.SEGMENT_FNO,
            exchange_trading_symbols=(
                exchange_symbol,
            ),
        )

        return response.get(exchange_symbol)

    # ==============================================
    # ACTIVE GTT ORDERS
    # ==============================================

    def get_active_gtt_orders(self):

        return self.groww.get_smart_order_list(

            segment=self.groww.SEGMENT_FNO,

            smart_order_type=(
                self.groww.SMART_ORDER_TYPE_GTT
            ),

            status=(
                self.groww.SMART_ORDER_STATUS_ACTIVE
            ),

            page=0,

            page_size=50,
        )

    # ==============================================
    # CREATE INITIAL SL
    # ==============================================

    def create_initial_sl(
        self,
        trading_symbol,
        quantity,
        trigger_price,
    ):

        reference_id = (
            f"sl-{trading_symbol[-8:]}"
            f"-{int(trigger_price * 100)}"
        )

        # Groww requires 8-20 characters
        # for reference_id.
        reference_id = reference_id[:20]

        response = self.groww.create_smart_order(

            smart_order_type=(
                self.groww.SMART_ORDER_TYPE_GTT
            ),

            reference_id=reference_id,

            segment=self.groww.SEGMENT_FNO,

            trading_symbol=trading_symbol,

            quantity=abs(int(quantity)),

            product_type=self.groww.PRODUCT_NRML,

            exchange=self.groww.EXCHANGE_NSE,

            duration=self.groww.VALIDITY_DAY,

            trigger_price=f"{trigger_price:.2f}",

            trigger_direction=(
                self.groww.TRIGGER_DIRECTION_DOWN
            ),

            order={

                "order_type": (
                    self.groww.ORDER_TYPE_STOP_LOSS_MARKET
                ),

                "price": None,

                "transaction_type": (
                    self.groww.TRANSACTION_TYPE_SELL
                ),
            },
        )

        return response

    # ==============================================
    # MODIFY INITIAL SL → TRAILING SL
    # ==============================================

    def modify_sl(
        self,
        smart_order_id,
        quantity,
        trigger_price,
    ):

        response = self.groww.modify_smart_order(

            smart_order_id=smart_order_id,

            smart_order_type=(
                self.groww.SMART_ORDER_TYPE_GTT
            ),

            segment=self.groww.SEGMENT_FNO,

            quantity=abs(int(quantity)),

            trigger_price=f"{trigger_price:.2f}",

            trigger_direction=(
                self.groww.TRIGGER_DIRECTION_DOWN
            ),

            order={

                "order_type": (
                    self.groww.ORDER_TYPE_STOP_LOSS_MARKET
                ),

                "price": None,

                "transaction_type": (
                    self.groww.TRANSACTION_TYPE_SELL
                ),
            },
        )

        return response