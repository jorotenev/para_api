from enum import Enum


class OrderingDirection(Enum):
    asc = 'asc'
    desc = 'desc'

    @classmethod
    def is_member(cls, candidate: str):
        if type(candidate) == OrderingDirection:
            return True
        else:
            return candidate in [ord.name for ord in OrderingDirection]
