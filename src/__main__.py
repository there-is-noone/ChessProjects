import asyncio
import os

from utils.stopwatch import Timer
import chess.engine
import chess.pgn
from engineanalyzer import EngineAnalyzer
from player import Player
from analyzedgame import AnalyzedGame


async def main():
    transport, engine = await chess.engine.popen_uci(
        "/home/kkrec/stockfish/stockfish-ubuntu-x86-64-avx2"
    )
    await engine.configure({"Threads":os.cpu_count()-2})

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
    with Timer("Analysis"):
        for i,game in test.Games:
            with Timer(f"{i} Single Game"):
                await game.get_analysis()


    await engine.quit()


if __name__ == "__main__":
    asyncio.run(main())
