import asyncio
from utils.Config import ConfigData
from utils.stopwatch import Timer
import chess.engine
import chess.pgn
from engineanalyzer import EngineAnalyzer
from player import Player
from analyzedgame import AnalyzedGame


async def main():
    transport, engine = await chess.engine.popen_uci(
        ConfigData.ENGINE_PATH
    )
    await engine.configure({"Threads":ConfigData.THREADS})

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
        for game in test.Games:
            with Timer(f"Single Game"):
                await game.get_analysis()


    await engine.quit()


if __name__ == "__main__":
    asyncio.run(main())
