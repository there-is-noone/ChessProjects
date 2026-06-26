import asyncio
import os.path
import pickle

import chess.engine
import chess.pgn
from chessprograms.openings import openingbook
from chessprograms.analyzedgame import AnalyzedGame, serialize_game
from chessprograms.engineanalyzer import EngineAnalyzer
from chessprograms.player import Player
from chessprograms.player_stats import PlayerStats
from chessprograms.utils.Config import ConfigData
from chessprograms.utils.EngineStrategies import STRATEGIES
from chessprograms.utils.moveanalysis import MoveAnalysis
from chessprograms.utils.stopwatch import Timer


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
    AnalyzedGame._opening_book = opening

    PICKLE_FILE = f"analysis{ConfigData.PLAYER_NAME}{ConfigData.ENGINE_ANALYSIS_TYPE}.pkl"

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
                analyzed._acpl_opening = g.get("acpl_opening")
                analyzed._transition_opening_to_mid = g.get("early_mid_transition_ply")
                analyzed._transition_mid_to_endgame = g.get("mid_endgame_transition_ply")
                test.add_game(analyzed)

                if "losses" in g and "moves" in g:
                    analyzed._move_analysis = [
                        MoveAnalysis(
                            move=chess.Move.from_uci(m_uci),
                            loss=loss_val,
                            eval_before=0.0,
                            eval_after=eval_val,
                            color=chess.WHITE if idx % 2 == 0 else chess.BLACK,
                        )
                        for idx, (m_uci, loss_val, eval_val) in enumerate(
                            zip(g["moves"], g["losses"], g["evals"])
                        )
                    ]
    else:
        all_games_data = []
        with open(ConfigData.FILE_PATH, encoding="utf-8") as games:
            nr = 1
            while game := chess.pgn.read_game(games):
                try:
                    board = chess.Board()
                    for move in game.mainline_moves():
                        board.push(move)
                except AssertionError:
                    print("Skipping invalid game:", game.headers.get("Event", "?"))
                    continue
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
        print("Coefficient of variation: ", await stats.coefficient_of_variation())

        print("Opening coefficient of variation", stats.coefficient_of_variation_opening)

        print("Ending coefficient of variation: ", stats.coefficient_of_variation_endgame)

    with Timer("opening name check"):
        for game in test.Games:
            print(game.opening_name)


"""    with Timer("Gambit Check"):
        for nr, game in enumerate(test.Games[:1000]):
            if game.is_gambit:
                print(game.opening_name)
                print(nr)
                print()"""


if __name__ == "__main__":
    asyncio.run(main())
