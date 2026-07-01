from enum import Enum
import chess

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

WHITE_START = {
    chess.B1,
    chess.G1,
    chess.C1,
    chess.F1,
    chess.A1,
    chess.H1,
    chess.D1,
    chess.E1,
}

BLACK_START = {
    chess.B8,
    chess.G8,
    chess.C8,
    chess.F8,
    chess.A8,
    chess.H8,
    chess.D8,
    chess.E8,
}
STARTING_PIECES = {
    chess.WHITE: {
        chess.B1: "NQ",
        chess.G1: "NK",
        chess.C1: "BQ",
        chess.F1: "BK",
    },
    chess.BLACK: {
        chess.B8: "NQ",
        chess.G8: "NK",
        chess.C8: "BQ",
        chess.F8: "BK",
    },
}