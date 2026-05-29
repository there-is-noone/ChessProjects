import os

from utils.stopwatch import Timer
import chess.engine
from engineanalyzer import EngineAnalyzer
from player import Player
from analyzedgame import AnalyzedGame

if __name__ == "__main__":
    engine = chess.engine.SimpleEngine.popen_uci(
        "/home/kkrec/stockfish/stockfish-ubuntu-x86-64-avx2"
    )
    engine.configure({"Threads":os.cpu_count()-2})

    analyzer = EngineAnalyzer(engine)

    test = Player("gracznumerx", [], [], [])
    with open(
        "/home/kkrec/chessgames/lichess_gracznumerx_2026-05-25.pgn", encoding="utf-8"
    ) as games:
        nr = 1
        while game := chess.pgn.read_game(games):
            test.add_game(game=AnalyzedGame(game, analyzer, []))
            nr += 1
        print("Winrate:", test.winrate(), "%")
        print("Short game rate:", test.short_game_rate(), "%")
        print("Short game winrate:", test.short_game_win_rate(), "%")
        print("Endgame rate:", test.endgame_rate(), "%")
        print("Endgame win rate:", test.endgame_win_rate(), "%")
        with Timer("All game analysis time"):
            for i, game in enumerate(test.Games[:200]):
                with Timer("ACPL timer"):
                    print(i)
                    print("ACPL:", game.get_acpl())
    engine.close()
