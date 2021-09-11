import re
import sys
from typing import TextIO

from src.bid_book import BidBook, Bid
from src.market_log_commands import AddOrderCommand, ReduceOrderCommand, MessageTypeEnum, MarketLogCommand


class BookAnalyzer:
    def __init__(self, target_size: int):
        self._target_size: int = target_size
        self._book: BidBook = BidBook()

    def analyze_market_log(self, log: TextIO):
        count = 1

        for line in log:
            if count == 10:
                exit()

            market_command = self._parse_message(line.rstrip())

            self._process_market_command(market_command)
            print(f"book: \n{self._book}")
            print()

            count += 1

    def _parse_message(self, message: str) -> MarketLogCommand:
        add_order_message_pattern = r'^\d+ A \w+ (B|S) \d+\.\d{2} \d+$'
        reduce_order_message_pattern = r'^\d+ R \w+ \d+$'

        add_order_match = re.compile(add_order_message_pattern).match(message)
        reduce_order_match = re.compile(reduce_order_message_pattern).match(message)

        if add_order_match:
            return self._parse_add_order_command(message)
        elif reduce_order_match:
            return self._parse_reduce_order_command(message)
        else:
            raise ValueError(f"Invalid market log message: {message}")
            # TODO: Do I need to return also?

    def _parse_add_order_command(self, message: str) -> AddOrderCommand:
        timestamp, message_type, order_id, side, price_str, size_str = message.split(' ')
        price_in_cents = self._to_cents(price_str)
        size = int(size_str)
        return AddOrderCommand(timestamp, order_id, side, price_in_cents, size)

    @staticmethod
    def _parse_reduce_order_command(message: str) -> ReduceOrderCommand:
        timestamp, message_type, order_id, reduction_size_str = message.split(' ')
        reduction_size = int(reduction_size_str)
        return ReduceOrderCommand(timestamp, order_id, reduction_size)

    @staticmethod
    def _to_cents(price_in_dollars_and_cents: str) -> int:
        dollars_str, cents_str = price_in_dollars_and_cents.split('.')
        return int(dollars_str)*100 + int(cents_str)

    def _process_market_command(self, cmd: MarketLogCommand):
        if cmd.get_message_type() == MessageTypeEnum.ADD_LIMIT_ORDER:
            self._process_add_order_command(cmd)
        elif cmd.get_message_type() == MessageTypeEnum.REDUCE_LIMIT_ORDER:
            self._process_reduce_order_command(cmd)

    def _process_add_order_command(self, cmd: AddOrderCommand):
        print(f"{cmd}")
        bid = self._command_to_bid(cmd)
        print(f"{bid}")
        self._book.add_bid(bid)

    def _process_reduce_order_command(self, cmd: ReduceOrderCommand):
        print(f"{cmd}")
        order_id, size_reduction = cmd.order_id, cmd.size_reduction
        self._book.reduce_bid(order_id, size_reduction)

    @staticmethod
    def _command_to_bid(command: AddOrderCommand) -> Bid:
        return Bid(command.order_id, command.price, command.size)


if __name__ == "__main__":
    target_size_arg = int(sys.argv[1])
    analyzer = BookAnalyzer(target_size_arg)
    analyzer.analyze_market_log(sys.stdin)
