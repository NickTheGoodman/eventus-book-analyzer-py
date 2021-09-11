from collections import namedtuple
from dataclasses import dataclass
from typing import Dict, List

from src.market_log_commands import SideOfBookEnum, MessageTypeEnum

PriceSizeTuple = namedtuple('PriceSizeTuple', [
    'price',
    'size'
])

StateOfBidBook = namedtuple('StateOfBidBook', [
    'total_bid_size',
    'price_of_cheapest_bid_to_take',
    'selling_income'
])


@dataclass
class Bid:
    order_id: str
    price: int
    size: int
    side: SideOfBookEnum = SideOfBookEnum.BID

    def reduce_size(self, size_reduction: int):
        self.size -= size_reduction


# All bids of the same price
@dataclass
class BidGroup:
    price: int
    limit_orders: List[str]
    total_size: int
    side: SideOfBookEnum = SideOfBookEnum.BID

    def add_bid(self, bid: Bid):
        self.limit_orders.append(bid.order_id)
        self.total_size += bid.size

    def reduce_total_size(self, size_reduction: int):
        self.total_size -= size_reduction

    def remove_bid(self, order_id: str):
        self.limit_orders.remove(order_id)

    def __str__(self) -> str:
        return f"BidGroup(" \
               f"price={self.price}, " \
               f"total_size={self.total_size}, " \
               f"bid_ids={self.limit_orders})"


UNCALCULATED_VALUE: int = -1


class BidBook:
    def __init__(self, target_size: int):
        self._target_size = target_size

        self._bids: Dict[str, Bid] = {}
        self._bid_groups: Dict[int, BidGroup] = {}
        self._sorted_bid_prices: List[int] = []

        self._total_bid_size = 0
        self._bids_to_take: List[PriceSizeTuple] = []
        self._price_of_cheapest_bid_to_take = UNCALCULATED_VALUE
        self._selling_income: int = UNCALCULATED_VALUE

    @property
    def total_bid_size(self) -> int:
        return self._total_bid_size

    @property
    def bids_to_take(self) -> List[PriceSizeTuple]:
        return self._bids_to_take

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
            self._update_sorted_list(bid)

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
        self._bid_groups[price] = \
            BidGroup(price=price, limit_orders=[order_id], total_size=size)

    def _update_sorted_list(self, bid: Bid):
        self._sorted_bid_prices.append(bid.price)
        self._sorted_bid_prices.sort(reverse=True)

    def reduce_bid(self, order_id: str, size_reduction: int):
        bid = self._bids[order_id]
        price = bid.price
        bid_group = self._bid_groups[price]
        actual_size_reduction = \
            self._get_adjusted_size_reduction(bid, size_reduction)

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
            self._sorted_bid_prices.remove(price)

    def _update_state_of_bid_book(self,
                                  msg_type: MessageTypeEnum,
                                  size_difference: int
                                  ):
        if msg_type == MessageTypeEnum.ADD_LIMIT_ORDER:
            self._total_bid_size += size_difference
        elif msg_type == MessageTypeEnum.REDUCE_LIMIT_ORDER:
            self._total_bid_size -= size_difference

        self._calculate_selling_income()

    def _calculate_selling_income(self):
        bids_to_take: List[PriceSizeTuple] = []
        price_of_cheapest_bid_to_take = UNCALCULATED_VALUE
        selling_income = UNCALCULATED_VALUE

        if self._should_calculate():
            num_shares_left_to_sell = self._target_size

            for price in self._sorted_bid_prices:
                bid_group = self._bid_groups[price]
                selling_income = 0

                if num_shares_left_to_sell >= bid_group.total_size:
                    num_shares_to_sell = bid_group.total_size

                    bids_to_take.append(
                        PriceSizeTuple(price, num_shares_to_sell)
                    )
                    selling_income += price * num_shares_to_sell

                    num_shares_left_to_sell -= num_shares_to_sell
                else:
                    num_shares_to_sell = num_shares_left_to_sell

                    bids_to_take.append(
                        PriceSizeTuple(price, num_shares_to_sell)
                    )
                    price_of_cheapest_bid_to_take = price
                    selling_income += price * num_shares_to_sell

                    break

        self._bids_to_take = bids_to_take
        self._price_of_cheapest_bid_to_take = price_of_cheapest_bid_to_take
        self._selling_income = selling_income

    def _should_calculate(self):
        return self._total_bid_size >= self._target_size

    def get_state_of_bid_book(self) -> StateOfBidBook:
        return StateOfBidBook(
            self._total_bid_size,
            self._price_of_cheapest_bid_to_take,
            self._selling_income
        )

    def __str__(self):
        bid_group_str = ""
        for i, price in enumerate(self._sorted_bid_prices):
            bid_group = self._bid_groups[price]
            bid_group_str += f"{bid_group}"
            if i < len(self._sorted_bid_prices) - 1:
                bid_group_str += ", "
        return bid_group_str
