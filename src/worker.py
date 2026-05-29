import io
import chess
import chess.pgn
import chess.engine
import atexit
from engineanalyzer import EngineAnalyzer
from utils.stopwatch import Timer

def close_engine():
    global ENGINE
    if ENGINE is not None:
        ENGINE.quit()
        ENGINE = None


def init_engine():
    global ENGINE
    ENGINE = chess.engine.SimpleEngine.popen_uci(
        "/home/kkrec/stockfish/stockfish-ubuntu-x86-64-avx2"
    )
    ENGINE.configure({"Threads":4})
    atexit.register(close_engine)


def analyze_game_worker(pgn_text: str):
    import psutil, os
    global ENGINE
    game = chess.pgn.read_game(io.StringIO(pgn_text))

    analyzer = EngineAnalyzer(ENGINE)
    result = analyzer.analyze_game(game)
    return result


def game_stream(path):
    with open(path, encoding="utf-8") as f:
        while game := chess.pgn.read_game(f):
            exporter = chess.pgn.StringExporter(
                headers=True, variations=True, comments=False
            )
            yield game.accept(exporter)
