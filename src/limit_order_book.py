from dataclasses import dataclass

from src.market_log_commands import SideOfBookEnum


@dataclass
class LimitOrder:
    order_type: SideOfBookEnum
    order_id: str
    price_in_cents: int
    size: int


# Combine like-priced bids and asks into the same object
class OrderPrice:
    def __init__(self, price_in_cents, size, order_id):
        self._price_in_cents = price_in_cents
        self._total_size = size
        self._limit_orders = [order_id]

    @property
    def price(self):
        return self._price_in_cents

    @property
    def total_size(self):
        return self._total_size

    @property
    def limit_orders(self):
        return self._limit_orders

# class AskPrice

class LimitOrderBook:
    def __init__(self, target_size):
        self._target_size = target_size

        self._orders_by_id = {}
        self._all_bids = set()

        self._total_bid_size = 0
        self._bids_to_buy = [] # list of (price, size) tuples
        self._selling_income = 0 # AKA "NA"
        self._price_of_cheapest_bid_to_buy = 0
        self._leftover_size_of_cheapest_bid_to_buy = 0


    def get_order_by_id(self, order_id):
        return self._orders_by_id[order_id]

    def add_new_bid(self, add_limit_order):
        order_id = add_limit_order.get_order_id()
        price = add_limit_order.get_price()
        size = add_limit_order.get_size()

        self._orders_by_id[order_id] = add_limit_order
        self._add_bid_to_price_set(add_limit_order)

    def _add_bid_to_order_dict(self, limit_order):
        pass

    def _add_bid_to_price_set(self, limit_order):
        pass

    def reduce_order(self, order_reduction):
        pass
