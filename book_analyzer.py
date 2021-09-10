import sys
import re

from src.limit_order_book import LimitOrderBook
from src.market_log_commands import AddLimitOrder, ReduceLimitOrder, MessageTypeEnum


class BookAnalyzer:
    def __init__(self, target_size):
        self._target_size = target_size
        self._book = LimitOrderBook(target_size)

    def analyze_market_log(self, log):
        count = 1

        for line in log:
            if (count == 10):
                exit()

            market_command = self._parse_message(line.rstrip())

            self._process_market_command(market_command)

            count += 1

    def _parse_message(self, message):
        limit_order_message_pattern = r'^\d+ A \w+ (B|S) \d+\.\d{2} \d+$'
        order_reduction_message_pattern = r'^\d+ R \w+ \d+$'

        limit_order_match = re.compile(limit_order_message_pattern).match(message)
        order_reduction_match = re.compile(order_reduction_message_pattern).match(message)

        if limit_order_match:
            return self._parse_limit_order(message)
        elif order_reduction_match:
            return self._parse_order_reduction(message)
        else:
            raise ValueError(f"Invalid market log message: {message}")
            # TODO: Do I need to return also?

    def _parse_limit_order(self, message):
        timestamp, message_type, order_id, side, price, size = message.split(' ')
        return AddLimitOrder(timestamp, order_id, side, price, size)

    def _parse_order_reduction(self, message):
        timestamp, message_type, order_id, size = message.split(' ')
        return ReduceLimitOrder(timestamp, order_id, size)

    def _process_market_command(self, market_command):
        print(market_command)
        if market_command.get_message_type() == MessageTypeEnum.ADD_LIMIT_ORDER:
            # self._book.process_new_bid(market_command)
            pass
        elif market_command.get_message_type() == MessageTypeEnum.REDUCE_LIMIT_ORDER:
            pass


if __name__ == "__main__":
    target_size = sys.argv[1]
    analyzer = BookAnalyzer(target_size)
    analyzer.analyze_market_log(sys.stdin)
