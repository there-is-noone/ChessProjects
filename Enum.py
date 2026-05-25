from enum import Enum


class Color(Enum):
    WHITE = 1
    BLACK = 0


class Ending(Enum):
    TIMEOUT = 0
    CHECKMATE = 1
    RESIGNATION = 2
    STALEMATE = -1
    DRAW = -2
    THREEFOLD = -3
    FIFTYMOVE = -4
