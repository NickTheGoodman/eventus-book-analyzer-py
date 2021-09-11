import re
import sys
from typing import TextIO, Tuple

from src.bid_book import BidBook, Bid, UNCALCULATED_VALUE
from src.market_log_commands import AddOrderCommand, ReduceOrderCommand, MessageTypeEnum, MarketLogCommand


class BookAnalyzer:
    def __init__(self, target_size: int):
        self._target_size: int = target_size
        self._book: BidBook = BidBook(target_size)

    def analyze_market_log(self, log: TextIO):
        for line in log:
            prev_bid_vars = self._book.get_state_of_bid_book()

            market_command = self._parse_message(line.rstrip())

            if market_command is None:
                continue

            print(f" timestamp: {market_command.timestamp}")

            self._process_market_command(market_command)

            cur_bid_vars = self._book.get_state_of_bid_book()

            self._output_selling_income_if_needed(
                market_command.timestamp,
                self._target_size,
                prev_bid_vars,
                cur_bid_vars)

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
            return None

    def _parse_add_order_command(self, message: str) -> AddOrderCommand:
        # TODO: need to further validate that all input args are accounted for
        timestamp, message_type, order_id, side, price_str, size_str = message.split(' ')
        price_in_cents = self._to_cents(price_str)
        size = int(size_str)
        return AddOrderCommand(timestamp, order_id, side, price_in_cents, size)

    @staticmethod
    def _parse_reduce_order_command(message: str) -> ReduceOrderCommand:
        # TODO: need to further validate that all input args are accounted for
        timestamp, message_type, order_id, reduction_size_str = message.split(' ')
        reduction_size = int(reduction_size_str)
        return ReduceOrderCommand(timestamp, order_id, reduction_size)

    @staticmethod
    def _to_cents(price_in_dollars_and_cents: str) -> int:
        dollars_str, cents_str = price_in_dollars_and_cents.split('.')
        return int(dollars_str)*100 + int(cents_str)

    def _process_market_command(self, cmd: MarketLogCommand):
        print(f" cmd: {cmd}")

        if cmd.get_message_type() == MessageTypeEnum.ADD_LIMIT_ORDER:
            self._process_add_order_command(cmd)
        elif cmd.get_message_type() == MessageTypeEnum.REDUCE_LIMIT_ORDER:
            self._process_reduce_order_command(cmd)

    def _process_add_order_command(self, cmd: AddOrderCommand):
        self._book.add_bid(cmd.order_id, cmd.price, cmd.size)

    def _process_reduce_order_command(self, cmd: ReduceOrderCommand):
        self._book.reduce_bid(cmd.order_id, cmd.size_reduction)

    @staticmethod
    def _command_to_bid(command: AddOrderCommand) -> Bid:
        return Bid(command.order_id, command.price, command.size)

    def _output_selling_income_if_needed(self, timestamp: int,
                                         target_size: int,
                                         prev_state_of_bid_book: Tuple[int, int, int],
                                         cur_state_of_bid_book: Tuple[int, int, int]):
        prev_total_bid_size, \
            prev_price_of_cheapest_bid_to_buy, \
            prev_selling_income = \
            prev_state_of_bid_book

        cur_total_bid_size, \
            cur_price_of_cheapest_bid_to_buy, \
            cur_selling_income = \
            cur_state_of_bid_book

        selling_income_has_changed = \
            cur_selling_income != prev_selling_income

        print(f" book:\t\t{self._book}")
        print(f" bids_to_buy:\t{self._book.bids_to_buy}")
        print(f" prev_bid_vars:\t{prev_state_of_bid_book}")
        print(f" cur_bid_vars:\t{cur_state_of_bid_book}")

        if selling_income_has_changed:
            selling_income_to_display = self._selling_income_to_display(cur_selling_income)
            print_to_stdout(f"{timestamp} S {selling_income_to_display}")

        print()

    @staticmethod
    def _to_dollars_and_cents(price_in_cents: int) -> str:
        dollars = str(int(price_in_cents / 100))
        cents = str(price_in_cents % 100).zfill(2)
        return f"{dollars}.{cents}"

    def _selling_income_to_display(self, selling_income_in_cents):
        return "NA" if selling_income_in_cents == UNCALCULATED_VALUE else \
            self._to_dollars_and_cents(selling_income_in_cents)


def print_to_stdout(*msg):
    print(*msg, file=sys.stdout)


def print_to_stderr(*msg):
    print(*msg, file=sys.stderr)


if __name__ == "__main__":
    target_size_arg = int(sys.argv[1])
    analyzer = BookAnalyzer(target_size_arg)
    analyzer.analyze_market_log(sys.stdin)
