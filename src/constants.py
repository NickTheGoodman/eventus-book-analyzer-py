from enum import Enum


class MessageTypeEnum(Enum):
    ADD_LIMIT_ORDER = 'A'
    REDUCE_LIMIT_ORDER = 'R'


class SideOfBookEnum(Enum):
    BID = 'B'
    ASK = 'S'


UNCALCULATED_VALUE = -1
