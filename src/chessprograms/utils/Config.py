import os
from dataclasses import dataclass

import chess


@dataclass
class ConfigData:
    NODES = 15000
    EVALUATION_LIMIT = 50
    THREADS = max(1, (os.cpu_count() or 1) - 2)
    MAX_CACHE_SIZE = 50000

    SACRIFICE_MAX_LOSS = 20
    INACCURACY_THRESHOLD = 50
    MISTAKE_THRESHOLD = 100
    BLUNDER_THRESHOLD = 300
    TEMPO_LOSS = 0.5
    SHORT_GAME_THRESHOLD = 25
    CASTLING_BONUS = 1.5
    QUEEN_LOSS = 1
    CENTER_PAWN_BONUS = 0.5
    DEVELOPED_PIECE_BONUS = 1
    ROOK_MOVE_LOSS = 1
    DEVELOPMENT_DIFFERENCE = 0.5

    ENGINE_PATH = "/home/kkrec/stockfish/stockfish-ubuntu-x86-64-avx2"
    FILE_PATH = "/home/kkrec/chessgames/Tal.pgn"
    PLAYER_NAME = "Tal, Mihail"
    ENGINE_ANALYSIS_TYPE = "acpl_deep"
    OPENING_BOOK_PATH = "opening_book.pkl"
    PICKLE_FILE = f"data/analysis{PLAYER_NAME}{ENGINE_ANALYSIS_TYPE}.pkl"

    SACRIFICE_MATERIAL_THRESHOLD = 2
    SACRIFICE_QUIESCENCE_PLIES = 5
    HARDCODED_VALUE_TO_MEASURE_VOLATILITY = 3000
    VOLATILITY_UPPER_BOUND = 500
    PIECE_VALUES = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
    }
