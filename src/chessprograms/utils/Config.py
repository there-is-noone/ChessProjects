import os
from dataclasses import dataclass

import chess


@dataclass
class ConfigData:
    NODES = 5000
    EVALUATION_LIMIT = 50
    THREADS = os.cpu_count() - 2
    _MAX_CACHE_SIZE = 50_000
    BLUNDER_THRESHOLD = 300
    SHORT_GAME_THRESHOLD = 25
    DEVELOPMENT_DIFFERENCE=0.5

    ENGINE_PATH = "/home/kkrec/stockfish/stockfish-ubuntu-x86-64-avx2"
    FILE_PATH = "/home/kkrec/chessgames/lichess_ARM-777777_2026-06-08.pgn"
    PLAYER_NAME = "ARM-777777"
    ENGINE_ANALYSIS_TYPE = "acpl_deep"
    OPENING_BOOK_PATH = "opening_book.pkl"

    OPENING_GAMBIT_THRESHOLD = 100

    PIECE_VALUES = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
    }
