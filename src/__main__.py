import asyncio
import os.path
import pickle

from utils.Config import ConfigData
from utils.stopwatch import Timer
import chess.engine
import chess.pgn
from engineanalyzer import EngineAnalyzer
from player import Player
from analyzedgame import AnalyzedGame, serialize_game
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
    PICKLE_FILE = f"analysis{ConfigData.PLAYER_NAME}.pkl"

    if os.path.exists(PICKLE_FILE):
        with Timer("reading from file:"):
            with open(PICKLE_FILE, "rb") as f:
                all_games_data = pickle.load(f)
            for g in all_games_data:
                game = chess.pgn.Game()
                for key, value in g["headers"].items():
                    game.headers[key] = value

                node = game
                for uci_move in g.get("moves", []):
                    node = node.add_variation(chess.Move.from_uci(uci_move))
                analyzed = AnalyzedGame(game, analyzer)
                analyzed._acpl_white = g.get("acpl_white")
                analyzed._acpl_black = g.get("acpl_black")

                test.add_game(analyzed)
    else:
        all_games_data = []
        with open(ConfigData.FILE_PATH, encoding="utf-8") as games:
            nr = 1
            while game := chess.pgn.read_game(games):
                analyzed = AnalyzedGame(game, analyzer)
                test.add_game(analyzed)
                with Timer("Analysis"):
                    await analyzed.precompute_acpl()
                nr += 1
                all_games_data.append(serialize_game(analyzed))

        with open(PICKLE_FILE, "wb") as f:
            pickle.dump(all_games_data, f)

            for g in all_games_data:
                game = chess.pgn.Game()
                for key, value in g["headers"].items():
                    game.headers[key] = value

                analyzed = AnalyzedGame(game, analyzer)

                analyzed._acpl_white = g.get("acpl_white")
                analyzed._acpl_black = g.get("acpl_black")

                test.add_game(analyzed)

    print("Winrate:", stats.winrate, "%")
    print("Short game rate:", stats.short_game_rate, "%")
    print("Short game winrate:", stats.short_game_win_rate, "%")
    print("Endgame rate:", stats.endgame_rate, "%")
    print("Endgame win rate:", stats.endgame_win_rate, "%")
    print("Winrate_per_eco: ", stats.winrate_per_eco, "%")
    await engine.quit()

    with Timer("ACPL"):
        acpl_list = await stats.get_acpl_list()
        print("ACPL: ", acpl_list)
        print("ACPL standard deviation: ", stats.acpl_standard_deviation)
        print("Coefficient of variation: ", stats.coefficient_of_variation)


if __name__ == "__main__":
    asyncio.run(main())
