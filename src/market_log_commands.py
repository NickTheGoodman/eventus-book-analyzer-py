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

    def get_message_type(self):
        return None


@dataclass
class AddOrderCommand(MarketLogCommand):
    side: SideOfBookEnum
    price: int
    size: int

    def get_message_type(self) -> MessageTypeEnum:
        return MessageTypeEnum.ADD_LIMIT_ORDER

    def get_side(self) -> SideOfBookEnum:
        return self.side

    # def __str__(self) -> str:
    #     return f"{self.timestamp} A {self.order_id} {self.side} {self.price} {self.size}"


@dataclass
class ReduceOrderCommand(MarketLogCommand):
    size_reduction: int

    def get_message_type(self) -> MessageTypeEnum:
        return MessageTypeEnum.REDUCE_LIMIT_ORDER

    # def __str__(self) -> str:
    #     return f"{self.timestamp} R {self.order_id} {self.size_reduction}"

