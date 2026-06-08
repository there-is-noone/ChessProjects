from dataclasses import dataclass
import os


@dataclass
class ConfigData:
    NODES = 20000
    EVALUATION_LIMIT = 50
    THREADS = os.cpu_count() - 2
    _MAX_CACHE_SIZE = 50_000
    ENGINE_PATH = "/home/kkrec/stockfish/stockfish-ubuntu-x86-64-avx2"
    FILE_PATH = "/home/kkrec/chessgames/lichess_gracznumerx_2026-05-30.pgn"
    PLAYER_NAME = "gracznumerx"
    ENGINE_ANALYSIS_TYPE = "acpl_fast"
