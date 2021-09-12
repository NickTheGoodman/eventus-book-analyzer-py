from collections import namedtuple
from dataclasses import dataclass
from typing import Dict, List

from src.constants import SideOfBookEnum, UNCALCULATED_VALUE, MessageTypeEnum

StateOfBook = namedtuple('StateOfBook', [
    'total_size',
    'price_of_last_order_taken',
    'total_price_of_taken_shares'
])

PriceSizeTuple = namedtuple('PriceSizeTuple', [
    'price',
    'size'
])


@dataclass
class LimitOrder:
    side: SideOfBookEnum
    order_id: str
    price: int
    size: int

    def reduce_size(self, size_reduction: int):
        self.size -= size_reduction


# All limit orders of the same side and price
@dataclass
class LimitOrderGroup:
    side: SideOfBookEnum
    price: int
    order_ids: List[str]
    total_size: int

    def add_order(self, order: LimitOrder):
        self.order_ids.append(order.order_id)
        self.total_size += order.size

    def reduce_total_size(self, size_reduction: int):
        self.total_size -= size_reduction

    def remove_order(self, order_id: str):
        self.order_ids.remove(order_id)

    def __str__(self) -> str:
        return f"LimitOrderGroup(" \
               f"side={self.side.value}, " \
               f"price={self.price}, " \
               f"total_size={self.total_size}, " \
               f"order_ids={self.order_ids})"


class LimitOrderBook:
    def __init__(self, side_of_book: SideOfBookEnum, target_size: int):
        self._side_of_book = side_of_book
        self._target_size = target_size

        self._orders: Dict[str, LimitOrder] = {}
        self._order_groups: Dict[int, LimitOrderGroup] = {}
        self._sorted_order_prices: List[int] = []
        self._total_book_size = 0

        self._orders_taken: List[PriceSizeTuple] = []
        self._price_of_last_order_taken = UNCALCULATED_VALUE
        self._total_price_of_orders_taken: int = UNCALCULATED_VALUE

    @property
    def total_book_size(self) -> int:
        return self._total_book_size

    @property
    def orders_to_take(self) -> List[PriceSizeTuple]:
        return self._orders_taken

    @property
    def total_price_of_orders_to_take(self) -> int:
        """ This is the selling income when the book stores bids.
            This is the buying expense when the book stores asks."""
        return self._total_price_of_orders_taken

    def get_order(self, order_id: str) -> LimitOrder:
        if order_id in self._orders.keys():
            return self._orders[order_id]
        return None

    def add_order(self, order_id: str, price: int, size: int):
        order = LimitOrder(self._side_of_book, order_id, price, size)
        self._add_order_by_id(order)

        if self._order_group_already_exists(order.price):
            self._add_order_to_order_group(order)
        else:
            self._add_new_order_group(order)
            self._update_sorted_list(order)

        self._update_state_of_book(
            MessageTypeEnum.ADD_LIMIT_ORDER,
            size
        )

    def _order_group_already_exists(self, price: int) -> bool:
        return price in self._order_groups.keys()

    def _add_order_by_id(self, order: LimitOrder):
        self._orders[order.order_id] = order

    def _add_order_to_order_group(self, order: LimitOrder):
        self._order_groups[order.price].add_order(order)

    def _add_new_order_group(self, order: LimitOrder):
        side, price, order_id, size = \
            order.side, order.price, order.order_id, order.size
        self._order_groups[price] = LimitOrderGroup(
            side=side,
            price=price,
            order_ids=[order_id],
            total_size=size
        )

    def _update_sorted_list(self, order: LimitOrder):
        """ If storing bids, sort by price in DESCENDING order so the priciest bids are first.
            If storing asks, sort by price in ASCENDING order so the cheapest asks are first."""
        self._sorted_order_prices.append(order.price)
        if order.side == SideOfBookEnum.BID:
            self._sorted_order_prices.sort(reverse=True)
        else:
            self._sorted_order_prices.sort()

    def reduce_order(self, order_id: str, size_reduction: int):
        order = self._orders[order_id]
        price = order.price
        order_group = self._order_groups[price]
        actual_size_reduction = \
            self._get_adjusted_size_reduction(order, size_reduction)

        order.reduce_size(actual_size_reduction)
        order_group.reduce_total_size(actual_size_reduction)

        self._remove_order_if_needed(order, order_group)
        self._remove_order_group_if_needed(order_group)

        self._update_state_of_book(
            MessageTypeEnum.REDUCE_LIMIT_ORDER,
            actual_size_reduction
        )

    @staticmethod
    def _get_adjusted_size_reduction(order: LimitOrder, size_reduction: int) -> int:
        return size_reduction if order.size - size_reduction >= 0 else order.size

    def _remove_order_if_needed(self, order: LimitOrder, order_group: LimitOrderGroup):
        order_id = order.order_id
        should_remove_order = order.size == 0

        if should_remove_order:
            del self._orders[order_id]
            order_group.remove_order(order_id)

    def _remove_order_group_if_needed(self, order_group: LimitOrderGroup):
        price = order_group.price
        should_remove_order_group = order_group.total_size == 0

        if should_remove_order_group:
            del self._order_groups[price]
            self._sorted_order_prices.remove(price)

    def _update_state_of_book(self,
                              msg_type: MessageTypeEnum,
                              size_difference: int
                              ):
        if msg_type == MessageTypeEnum.ADD_LIMIT_ORDER:
            self._total_book_size += size_difference
        elif msg_type == MessageTypeEnum.REDUCE_LIMIT_ORDER:
            self._total_book_size -= size_difference

        self._calculate_total_price_of_taken_orders()

    def _calculate_total_price_of_taken_orders(self):
        orders_taken: List[PriceSizeTuple] = []
        price_of_last_order_to_take = UNCALCULATED_VALUE
        total_price_of_orders_to_take = UNCALCULATED_VALUE

        if self._should_calculate():
            num_shares_left_to_take = self._target_size
            total_price_of_orders_to_take = 0

            for price in self._sorted_order_prices:
                order_group = self._order_groups[price]

                if num_shares_left_to_take >= order_group.total_size:
                    num_shares_taken = order_group.total_size

                    orders_taken.append(PriceSizeTuple(price, num_shares_taken))
                    total_price_of_orders_to_take += price * num_shares_taken
                    num_shares_left_to_take -= num_shares_taken
                else:
                    num_shares_taken = num_shares_left_to_take

                    orders_taken.append(PriceSizeTuple(price, num_shares_taken))
                    price_of_last_order_to_take = price
                    total_price_of_orders_to_take += price * num_shares_taken
                    break

        self._orders_taken = orders_taken
        self._price_of_last_order_taken = price_of_last_order_to_take
        self._total_price_of_orders_taken = total_price_of_orders_to_take

    def _should_calculate(self):
        return self._total_book_size >= self._target_size

    def get_state_of_book(self) -> StateOfBook:
        return StateOfBook(
            total_size=self._total_book_size,
            price_of_last_order_taken=self._price_of_last_order_taken,
            total_price_of_taken_shares=self._total_price_of_orders_taken
        )

    def __str__(self):
        order_group_str = ""
        for i, price in enumerate(self._sorted_order_prices):
            order_group = self._order_groups[price]
            order_group_str += f"{order_group}"
            if i < len(self._sorted_order_prices) - 1:
                order_group_str += ", "
        return order_group_str
