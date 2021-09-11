from collections import namedtuple
from dataclasses import dataclass

from typing import Dict, List, Tuple

from src.market_log_commands import SideOfBookEnum, MessageTypeEnum


@dataclass
class Bid:
    order_id: str
    price: int
    size: int
    side: SideOfBookEnum = SideOfBookEnum.BID

    def reduce_size(self, size_reduction: int):
        self.size -= size_reduction


# All bids of the same price
class BidGroup:
    def __init__(self, price: int, order_id: str, size: int):
        self._price: int = price
        self._bid_ids: List[str] = [order_id]
        self._total_size: int = size

    @property
    def price(self) -> int:
        return self._price

    @price.setter
    def price(self, price: int):
        self._price = price

    @property
    def total_size(self) -> int:
        """ Total size of all bids at this price. """
        return self._total_size

    @property
    def limit_orders(self) -> List[str]:
        """ All bids at this price. """
        return self._bid_ids

    def add_bid(self, bid: Bid):
        self._add_id(bid.order_id)
        self._increment_size(bid.size)

    def _add_id(self, order_id: str):
        self._bid_ids.append(order_id)

    def _increment_size(self, size: int):
        self._total_size += size

    def reduce_total_size(self, reduction_in_size: int):
        self._total_size -= reduction_in_size

    def remove_bid(self, order_id: str):
        self._bid_ids.remove(order_id)

    def __str__(self) -> str:
        return f"BidGroup(price={self._price}, total_size={self._total_size}, bid_ids={self._bid_ids})"


PriceSizeTuple = namedtuple('PriceSizeTuple', [
    'price',
    'size'
])

StateOfBidBook = namedtuple('StateOfBidBook', [
    'total_bid_size',
    'price_of_cheapest_bid_to_buy',
    'selling_income'
])

UNCALCULATED_VALUE: int = -1


class BidBook:
    def __init__(self, target_size: int):
        self._target_size = target_size

        self._bids: Dict[str, Bid] = {}
        self._bid_groups: Dict[int, BidGroup] = {}
        self._sorted_prices: List[int] = []

        self._total_bid_size = 0
        self._bids_to_buy: List[PriceSizeTuple] = []
        self._price_of_cheapest_bid_to_buy = UNCALCULATED_VALUE
        self._selling_income: int = UNCALCULATED_VALUE

    @property
    def total_bid_size(self) -> int:
        return self._total_bid_size

    @property
    def bids_to_buy(self) -> List[PriceSizeTuple]:
        return self._bids_to_buy

    @property
    def selling_income(self) -> int:
        return self._selling_income

    def add_bid(self, order_id: str, price: int, size: int):
        bid = Bid(order_id, price, size)
        self._add_bid_by_id(bid)

        if self._bid_group_already_exists(bid.price):
            self._add_bid_to_bid_group(bid)
        else:
            self._add_new_bid_group(bid)

        self._update_state_of_bid_book(
            MessageTypeEnum.ADD_LIMIT_ORDER,
            size
        )

    def _bid_group_already_exists(self, price: int) -> bool:
        return price in self._bid_groups.keys()

    def _add_bid_by_id(self, bid: Bid):
        self._bids[bid.order_id] = bid

    def _add_bid_to_bid_group(self, bid: Bid):
        self._bid_groups[bid.price].add_bid(bid)

    def _add_new_bid_group(self, bid: Bid):
        price, order_id, size = bid.price, bid.order_id, bid.size

        self._bid_groups[price] = BidGroup(price, order_id, size)

        self._sorted_prices.append(price)
        self._sorted_prices.sort(reverse=True)

    def reduce_bid(self, order_id: str, size_reduction: int):
        bid = self._bids[order_id]
        price = bid.price
        bid_group = self._bid_groups[price]
        actual_size_reduction = self._get_adjusted_size_reduction(bid, size_reduction)

        bid.reduce_size(actual_size_reduction)
        bid_group.reduce_total_size(actual_size_reduction)

        self._remove_bid_if_needed(bid, bid_group)
        self._remove_bid_group_if_needed(bid_group)

        self._update_state_of_bid_book(
            MessageTypeEnum.REDUCE_LIMIT_ORDER,
            actual_size_reduction
        )

    @staticmethod
    def _get_adjusted_size_reduction(bid: Bid, size_reduction: int) -> int:
        return size_reduction if bid.size - size_reduction >= 0 else bid.size

    def _remove_bid_if_needed(self, bid: Bid, bid_group: BidGroup):
        order_id = bid.order_id
        should_remove_bid = bid.size == 0

        if should_remove_bid:
            del self._bids[order_id]
            bid_group.remove_bid(order_id)

    def _remove_bid_group_if_needed(self, bid_group: BidGroup):
        price = bid_group.price
        should_remove_bid_group = bid_group.total_size == 0

        if should_remove_bid_group:
            del self._bid_groups[price]
            self._sorted_prices.remove(price)

    def _update_state_of_bid_book(self, msg_type: MessageTypeEnum, size_difference: int):
        if msg_type == MessageTypeEnum.ADD_LIMIT_ORDER:
            self._total_bid_size += size_difference
        elif msg_type == MessageTypeEnum.REDUCE_LIMIT_ORDER:
            self._total_bid_size -= size_difference

        self._calculate_bids_to_buy()

        self._calculate_selling_income()

    def _calculate_bids_to_buy(self):
        bids_to_buy: List[PriceSizeTuple] = []
        price_of_cheapest_bid_to_buy = UNCALCULATED_VALUE

        if self._should_calculate():
            num_shares_left_to_buy = self._target_size

            for price in self._sorted_prices:
                bid_group = self._bid_groups[price]

                if num_shares_left_to_buy >= bid_group.total_size:
                    num_shares_to_buy = bid_group.total_size
                    bids_to_buy.append(PriceSizeTuple(price, num_shares_to_buy))
                    num_shares_left_to_buy -= bid_group.total_size
                else:
                    bids_to_buy.append((price, num_shares_left_to_buy))
                    price_of_cheapest_bid_to_buy = price
                    break

        self._bids_to_buy = bids_to_buy
        self._price_of_cheapest_bid_to_buy = price_of_cheapest_bid_to_buy

    def _calculate_selling_income(self):
        selling_income = UNCALCULATED_VALUE

        if self._should_calculate():
            selling_income = 0
            for (price, size) in self._bids_to_buy:
                selling_income += price * size

        self._selling_income = selling_income

    def _should_calculate(self):
        return self._total_bid_size >= self._target_size

    def get_state_of_bid_book(self) -> Tuple[int, int, int]:
        return StateOfBidBook(
            self._total_bid_size,
            self._price_of_cheapest_bid_to_buy,
            self._selling_income
        )

    def __str__(self):
        bid_group_str = ""
        for i, price in enumerate(self._sorted_prices):
            bid_group = self._bid_groups[price]
            bid_group_str += f"{bid_group}"
            if i < len(self._sorted_prices) - 1:
                bid_group_str += ", "
        return bid_group_str
