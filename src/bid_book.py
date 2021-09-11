from dataclasses import dataclass

from typing import Dict, List

from src.market_log_commands import SideOfBookEnum


@dataclass
class Bid:
    order_id: str
    price: int
    size: int

    def reduce_size(self, reduction_in_size: int):
        self.size -= reduction_in_size

    def side(self):
        return SideOfBookEnum.BID.value


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
        return f"{self._price} {self._total_size} {self._bid_ids}"


class BidBook:
    def __init__(self):
        self._bids: Dict[str, Bid] = {}
        self._bid_groups: Dict[int, BidGroup] = {}
        self._sorted_prices: List[int] = []

    def add_bid(self, bid: Bid):
        self._add_bid_by_id(bid)
        if self._bid_group_already_exists(bid.price):
            self._add_bid_to_bid_group(bid)
        else:
            self._add_new_bid_group(bid)

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
        should_remove_bid_price = bid_group.total_size == 0

        if should_remove_bid_price:
            del self._bid_groups[price]
            self._sorted_prices.remove(price)

    def __str__(self):
        bid_prices_str = ""
        for i, price in enumerate(self._sorted_prices):
            bid_price = self._bid_groups[price]
            bid_prices_str += f"{bid_price}"
            if i < len(self._sorted_prices) - 1:
                bid_prices_str += "\n"
        return bid_prices_str
