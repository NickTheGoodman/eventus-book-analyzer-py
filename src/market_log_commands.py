from dataclasses import dataclass

from src.constants import SideOfBookEnum, MessageTypeEnum


@dataclass
class MarketLogCommand:
    timestamp: int
    order_id: str

    def get_message_type(self) -> MessageTypeEnum:
        pass


@dataclass
class AddOrderCommand(MarketLogCommand):
    side: SideOfBookEnum
    price: int
    size: int

    def get_message_type(self) -> MessageTypeEnum:
        return MessageTypeEnum.ADD_LIMIT_ORDER

    def get_side(self) -> SideOfBookEnum:
        return self.side


@dataclass
class ReduceOrderCommand(MarketLogCommand):
    size_reduction: int

    def get_message_type(self) -> MessageTypeEnum:
        return MessageTypeEnum.REDUCE_LIMIT_ORDER
