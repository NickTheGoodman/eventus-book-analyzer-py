import re
import sys
from typing import TextIO

from limit_order_book import LimitOrderBook, LimitOrder, StateOfBook
from constants import SideOfBookEnum, MessageTypeEnum, UNCALCULATED_VALUE
from market_log_commands import AddOrderCommand, ReduceOrderCommand, MarketLogCommand


class BookAnalyzer:
    def __init__(self, target_size: int, debug_flag: bool):
        self._target_size = target_size
        self._debug_flag = debug_flag
        self._bid_book = LimitOrderBook(SideOfBookEnum.BID, target_size)
        self._ask_book = LimitOrderBook(SideOfBookEnum.ASK, target_size)

    def analyze_market_log(self, log: TextIO):
        for line in log:
            prev_bid_book_state = self._bid_book.get_state_of_book()
            prev_ask_book_state = self._ask_book.get_state_of_book()

            cmd = self._parse_message(line.rstrip())
            if cmd is None:
                continue

            side_of_book = self._process_market_log_command(cmd)

            relevant_prev_book_state = \
                prev_bid_book_state if side_of_book == SideOfBookEnum.BID else \
                prev_ask_book_state
            relevant_cur_book_state = self._get_state_of_book(side_of_book)

            self._output_relevant_total_price_if_needed(
                cmd.timestamp,
                side_of_book,
                relevant_prev_book_state,
                relevant_cur_book_state
            )

            self._book_analyzer_debug_print(
                cmd,
                side_of_book,
                relevant_prev_book_state,
                relevant_cur_book_state
            )

    def _get_state_of_book(self, side_of_book: SideOfBookEnum) -> StateOfBook:
        return \
            self._bid_book.get_state_of_book() if side_of_book == SideOfBookEnum.BID else \
            self._ask_book.get_state_of_book()

    def _parse_message(self, msg: str) -> MarketLogCommand:
        add_order_message_pattern = r'^\d+ A \w+ (B|S) \d+\.\d{2} \d+$'
        reduce_order_message_pattern = r'^\d+ R \w+ \d+$'

        add_order_match = re.compile(add_order_message_pattern).match(msg)
        reduce_order_match = re.compile(reduce_order_message_pattern).match(msg)

        if add_order_match:
            return self._parse_add_order_command(msg)
        elif reduce_order_match:
            return self._parse_reduce_order_command(msg)
        else:
            print_to_stderr(f"Invalid market log message: {msg}")

    def _parse_add_order_command(self, message: str) -> AddOrderCommand:
        timestamp_str, message_type, order_id, side_str, price_str, size_str = message.split(' ')
        timestamp = int(timestamp_str)
        side_enum = self._side_str_to_enum(side_str)
        price_in_cents = self._to_cents(price_str)
        size = int(size_str)
        return AddOrderCommand(timestamp, order_id, side_enum, price_in_cents, size)

    @staticmethod
    def _parse_reduce_order_command(message: str) -> ReduceOrderCommand:
        timestamp_str, message_type, order_id, reduction_size_str = message.split(' ')
        timestamp = int(timestamp_str)
        reduction_size = int(reduction_size_str)
        return ReduceOrderCommand(timestamp, order_id, reduction_size)

    @staticmethod
    def _side_str_to_enum(side_str: str) -> SideOfBookEnum:
        if side_str == 'B':
            return SideOfBookEnum.BID
        elif side_str == 'S':
            return SideOfBookEnum.ASK

    @staticmethod
    def _to_cents(price_in_dollars_and_cents: str) -> int:
        dollars_str, cents_str = price_in_dollars_and_cents.split('.')
        return int(dollars_str)*100 + int(cents_str)

    def _process_market_log_command(self, cmd: MarketLogCommand) -> SideOfBookEnum:
        if cmd.get_message_type() == MessageTypeEnum.ADD_LIMIT_ORDER:
            return self._process_add_order_command(cmd)
        elif cmd.get_message_type() == MessageTypeEnum.REDUCE_LIMIT_ORDER:
            return self._process_reduce_order_command(cmd)

    def _process_add_order_command(self, cmd: AddOrderCommand):
        if cmd.side == SideOfBookEnum.BID:
            self._bid_book.add_order(cmd.order_id, cmd.price, cmd.size)
        elif cmd.side == SideOfBookEnum.ASK:
            self._ask_book.add_order(cmd.order_id, cmd.price, cmd.size)
        return cmd.side

    def _process_reduce_order_command(self, cmd: ReduceOrderCommand):
        order = self._find_order_to_reduce(cmd.order_id)
        if order:
            if order.side == SideOfBookEnum.BID:
                self._bid_book.reduce_order(
                    cmd.order_id,
                    cmd.size_reduction
                )
            else:
                self._ask_book.reduce_order(cmd.order_id, cmd.size_reduction)
            return order.side
        else:
            print_to_stderr(f"Could not find order to reduce. Id: {cmd.order_id}")
            return None

    def _find_order_to_reduce(self, order_id: str) -> LimitOrder:
        """ Search both the bid and ask books for the order. """
        order = self._bid_book.get_order(order_id)
        if order is not None:
            return order
        return self._ask_book.get_order(order_id)

    def _output_relevant_total_price_if_needed(self,
                                               timestamp: int,
                                               side_of_book: SideOfBookEnum,
                                               prev_state_of_book: StateOfBook,
                                               cur_state_of_book: StateOfBook):
        prev_total_price = prev_state_of_book.total_price_of_taken_shares
        cur_total_price = cur_state_of_book.total_price_of_taken_shares

        total_price_has_changed = \
            cur_total_price != prev_total_price

        if total_price_has_changed:
            sell_or_buy = \
                'S' if side_of_book == SideOfBookEnum.BID else \
                'B'
            total_price_to_display = self._total_price_to_display(cur_total_price)
            print_to_stdout(f"{timestamp} {sell_or_buy} {total_price_to_display}")

    def _total_price_to_display(self, total_price_in_cents):
        return "NA" if total_price_in_cents == UNCALCULATED_VALUE else \
            self._to_dollars_and_cents(total_price_in_cents)

    @staticmethod
    def _to_dollars_and_cents(price_in_cents: int) -> str:
        dollars = str(int(price_in_cents / 100))
        cents = str(price_in_cents % 100).zfill(2)
        return f"{dollars}.{cents}"

    def _book_analyzer_debug_print(self,
                                   cmd: MarketLogCommand,
                                   side_of_book: SideOfBookEnum,
                                   prev_state_of_book: StateOfBook,
                                   cur_state_of_book: StateOfBook
                                   ):
        if self._debug_flag:
            print_to_stdout(f" cmd:\t{cmd}")
            print_to_stdout(f" side_of_book:\t{side_of_book}")
            if side_of_book == SideOfBookEnum.BID:
                print_to_stdout(f" bid_book:\t{self._bid_book}")
                print_to_stdout(f" bids_to_take:\t{self._bid_book.orders_to_take}")
                print_to_stdout(f" prev_bid_state:{prev_state_of_book}")
                print_to_stdout(f" cur_bid_state:\t{cur_state_of_book}")
            elif side_of_book == SideOfBookEnum.ASK:
                print_to_stdout(f" ask_book:\t{self._ask_book}")
                print_to_stdout(f" asks_to_take:\t{self._bid_book.orders_to_take}")
                print_to_stdout(f" prev_ask_state{prev_state_of_book}")
                print_to_stdout(f" cur_ask_state:\t{cur_state_of_book}")
            print_to_stdout("")


def print_to_stdout(*msg):
    print(*msg, file=sys.stdout)


def print_to_stderr(*msg):
    print(*msg, file=sys.stderr)


def parse_args(sys_args):
    """
    2 positional args:
        The 1st positional arg is the target_size (int)
        Anything being typed in the 2nd positional arg activates the debug flag.
    """
    arg1: int = int(sys_args[1])
    arg2: bool = len(sys_args) > 2
    return arg1, arg2


if __name__ == "__main__":
    (target_size_arg, debug_flag_arg) = parse_args(sys.argv)
    analyzer = BookAnalyzer(target_size_arg, debug_flag_arg)
    analyzer.analyze_market_log(sys.stdin)
