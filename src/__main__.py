import asyncio
from utils.Config import ConfigData
from utils.stopwatch import Timer
import chess.engine
import chess.pgn
from engineanalyzer import EngineAnalyzer
from player import Player
from analyzedgame import AnalyzedGame
from utils.EngineStrategies import STRATEGIES
from player_stats import PlayerStats
import openings.openingbook as openingbook

async def main():
    transport, engine = await chess.engine.popen_uci(ConfigData.ENGINE_PATH)
    await engine.configure({"Threads": ConfigData.THREADS})
    strategy = STRATEGIES[ConfigData.ENGINE_ANALYSIS_TYPE]
    analyzer = EngineAnalyzer(engine, strategy)

    test = Player(ConfigData.PLAYER_NAME)
    stats = PlayerStats(test)

    try:
        opening = openingbook.OpeningBook.load()
    except FileNotFoundError:
        opening = openingbook.OpeningBook.build_trie()
        opening.save()

    with open(ConfigData.FILE_PATH, encoding="utf-8") as games:
        nr = 1
        while game := chess.pgn.read_game(games):
            analyzed=AnalyzedGame(game, analyzer)
            test.add_game(analyzed)
            with Timer("Analysis"):
                await analyzed.precompute_acpl()
            nr += 1

    print("Winrate:", stats.winrate, "%")
    print("Short game rate:", stats.short_game_rate, "%")
    print("Short game winrate:", stats.short_game_win_rate, "%")
    print("Endgame rate:", stats.endgame_rate, "%")
    print("Endgame win rate:", stats.endgame_win_rate, "%")
    print("Winrate_per_eco: ", stats.winrate_per_eco, "%")
    await engine.quit()

    with Timer("ACPL"):
        acpl_list= await stats.get_acpl_list()
        print("ACPL: ",acpl_list)

if __name__ == "__main__":
    asyncio.run(main())
