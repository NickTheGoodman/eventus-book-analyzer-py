from dataclasses import dataclass
from enum import Enum


class MessageTypeEnum(Enum):
    ADD_LIMIT_ORDER = 'A'
    REDUCE_LIMIT_ORDER = 'R'


class SideOfBookEnum(Enum):
    BID = 'B'
    ASK = 'S'


@dataclass
class MarketLogCommand:
    timestamp: int
    order_id: str
    size: int

    def get_message_type(self):
        return None


@dataclass
class AddLimitOrder(MarketLogCommand):
    side: SideOfBookEnum
    price_in_cents: int

    def __str__(self):
        return f"{self.timestamp} A {self.order_id} {self.side} {self.price_in_cents} {self.size}"

    def get_message_type(self):
        return MessageTypeEnum.ADD_LIMIT_ORDER

    def is_bid(self):
        return self.side == SideOfBookEnum.BID

    def is_ask(self):
        return self.side == SideOfBookEnum.ASK


@dataclass
class ReduceLimitOrder(MarketLogCommand):
    def __str__(self):
        return f"{self.timestamp} R {self.order_id} {self.size}"

    def get_message_type(self):
        return MessageTypeEnum.REDUCE_LIMIT_ORDER

