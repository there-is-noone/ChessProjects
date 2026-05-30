from dataclasses import dataclass
import os
@dataclass
class ConfigData:
    NODES = 40000
    EVALUATION_LIMIT=500
    THREADS = os.cpu_count() - 2
    ENGINE_PATH="/home/kkrec/stockfish/stockfish-ubuntu-x86-64-avx2"