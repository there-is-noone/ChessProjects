import asyncio
import os.path
import pickle

import chess.engine
import chess.pgn

from chessprograms import analyzedgame
from chessprograms.analyzedgame import AnalyzedGame, serialize_game
from chessprograms.engineanalyzer import EngineAnalyzer
from chessprograms.openings import openingbook
from chessprograms.player import Player
from chessprograms.player_stats import PlayerStats
from chessprograms.utils.Config import ConfigData
from chessprograms.utils.EngineStrategies import STRATEGIES
from chessprograms.utils.moveanalysis import MoveAnalysis
from chessprograms.utils.stopwatch import Timer


async def main():
    # initializing the objects used througout the program
    transport, engine = await chess.engine.popen_uci(ConfigData.ENGINE_PATH)
    await engine.configure({"Threads": ConfigData.THREADS})
    strategy = STRATEGIES[ConfigData.ENGINE_ANALYSIS_TYPE]
    analyzer = EngineAnalyzer(engine, strategy)
    test = Player(ConfigData.PLAYER_NAME)
    stats = PlayerStats(test)

    print(analyzedgame.king_pressure(chess.Board("6k1/6pp/8/7Q/8/8/8/6K1 w - - 0 1"), chess.BLACK))

    try:
        opening = openingbook.OpeningBook.load()
    except FileNotFoundError:
        opening = openingbook.OpeningBook.build_trie()
        opening.save()
    AnalyzedGame._opening_book = opening

    print(ConfigData.PICKLE_FILE)
    # loading/saving analyzed games
    if os.path.exists(ConfigData.PICKLE_FILE):
        with Timer("pickle read"):
            with open(ConfigData.PICKLE_FILE, "rb") as f:
                all_games_data = pickle.load(f)
        with Timer("decoding"):
            for pickled_game in all_games_data:
                if len(pickled_game["moves"]) < 2:
                    continue

                game = chess.pgn.Game()

                for header_name, header_value in pickled_game["headers"].items():
                    game.headers[header_name] = header_value

                node = game
                for uci_move in pickled_game.get("moves", []):
                    node = node.add_variation(chess.Move.from_uci(uci_move))
                analyzed = AnalyzedGame(game, analyzer)
                analyzed._acpl_white = pickled_game.get("acpl_white")
                analyzed._acpl_black = pickled_game.get("acpl_black")
                analyzed._acpl_opening = pickled_game.get("acpl_opening")
                analyzed._transition_opening_to_mid = pickled_game.get("early_mid_transition_ply")
                analyzed._transition_mid_to_endgame = pickled_game.get("mid_endgame_transition_ply")

                if "losses" in pickled_game and "moves" in pickled_game:
                    development = pickled_game.get("development")
                    if development is None:
                        development = [0.0] * len(pickled_game["moves"])

                    # gathering all information from decoding in one big list of moves
                    analyzed._move_analysis = [
                        MoveAnalysis(
                            move=chess.Move.from_uci(m_uci),
                            loss=loss_val,
                            eval_before=eval_before_val,
                            eval_after=eval_after_val,
                            color=chess.WHITE if idx % 2 == 0 else chess.BLACK,
                            development_advantage=dev_adv,
                            # is_sacrifice=is_sacrifice,
                            is_mobile=is_mobile,
                            pressure_gain=pressure_gain,
                        )
                        for idx, (
                            m_uci,
                            loss_val,
                            eval_before_val,
                            eval_after_val,
                            dev_adv,
                            # is_sacrifice,
                            is_mobile,
                            pressure_gain,
                        ) in enumerate(
                            zip(
                                pickled_game["moves"],
                                pickled_game["losses"],
                                pickled_game["evals_before"],
                                pickled_game["evals_after"],
                                development,
                                # pickled_game["is_sacrifices"],
                                pickled_game["is_mobile"],
                                pickled_game["development_gains"],
                            )
                        )
                    ]
                    test.add_game(analyzed)

    else:
        all_games_data = []
        with open(ConfigData.FILE_PATH, encoding="utf-8") as games:
            nr = 1
            with Timer("Full analysis time"):
                while game := chess.pgn.read_game(games):
                    # If moves are broken/from different starting board, throws an error
                    if "correspondence" in game.headers["Event"]:
                        continue
                    # use the game that was read from the file to the Player library of the games
                    analyzed = AnalyzedGame(game, analyzer)
                    # with Timer("Analysis"):
                    await analyzed.precompute_acpl()
                    test.add_game(analyzed)
                    nr += 1
                    all_games_data.append(serialize_game(analyzed))

        with Timer("pickling the games"):
            with open(ConfigData.PICKLE_FILE, "wb") as f:
                pickle.dump(all_games_data, f)

    # everything under it is just testing how the program has calculated the stats
    # will be changed a lot, will take shape after having a distinct first alpha version
    """with Timer("game len"):
        for game in stats.player.iterate_games():
            print(len(game._move_analysis))"""

    with Timer("basic stats"):
        print("Winrate:", stats.winrate, "%")
        print("Short game rate:", stats.short_game_rate, "%")
        print("Short game winrate:", stats.short_game_win_rate, "%")
        print("Endgame rate:", stats.endgame_rate, "%")
        print("Endgame win rate:", stats.endgame_win_rate, "%")
    # print("Winrate_per_eco: ", stats.winrate_per_eco, "%")
    await engine.quit()

    with Timer("stats based on acpl"):
        with Timer("Coefficient of variation time"):
            print("Coefficient of variation: ", await stats.coefficient_of_variation())

        with Timer("Opening coefficient of variation time"):
            print("Opening coefficient of variation", stats.coefficient_of_variation_opening)
        with Timer("Midgame coefficient of variation time"):
            print("Midgame coefficient of variation", stats.coefficient_of_variation_midgame)
        with Timer("Endgame coefficient of variation time"):
            print("Endgame coefficient of variation: ", stats.coefficient_of_variation_endgame)

    """with Timer("opening name check"):
        for game in test.Games:
            print(game.opening_name)"""

    with Timer("development check"):
        """for i, game in enumerate(test.Games):
            if game.which_color_developed_faster() == chess.WHITE:
                print("White was faster")
                print(game.transition_opening_to_mid)
                print(i)
                print()
            elif game.which_color_developed_faster() == chess.BLACK:
                print("Black was faster")
                print(game.transition_opening_to_mid)
                print(i)
                print()"""
        """for i, game in enumerate(test.Games):
            print("White" if game.which_color_attacked() == chess.WHITE else "Black")"""

        print(f"how often you get developed faster: {stats.development_advantage_percentage}%")

    with Timer("Volatilities check"):
        print(f"mean of volatilities: {stats.mean_of_volatilities}")
        print(f"volatility index for calculation: {stats.volatility_index()}")

    """with Timer("sacrifice percentage"):
        print(f"percentage of sacced games: {stats.sacrifice_percentage()}%")"""

    with Timer("percentage of game forcing moves analysis"):
        print(f"percentage of forced moves: {stats.percentage_of_forcing_moves}%")

    with Timer("mobile moves"):
        print(f"percentage of mobile moves: {stats.percentage_of_mobile_moves}%")

    with Timer("pressure gains"):
        print(f"Average of pressure gains: {stats.mean_of_development_gains}")

    with Timer("Performance"):
        print(f"Mean enemy rating: {stats.mean_enemy_rating}")
        print(f"Performance measure: {stats.performance}")

        """    with Timer("Gambit Check"):
        for nr, game in enumerate(test.Games[:1000]):
            if game.is_gambit:
                print(game.opening_name)
                print(nr)
                print()"""


if __name__ == "__main__":
    asyncio.run(main())
