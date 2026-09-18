import asyncio
import os
import os.path

import chess.engine
import chess.pgn
import loading
from engineanalyzer import EngineAnalyzer
from player import Player
from player_stats.player_stats import PlayerStats
from utils.Config import ConfigData
from utils.EngineStrategies import STRATEGIES
from utils.stopwatch import Timer


async def main():

    player_name = input("Insert the player lichess nickname: ").strip() or ConfigData.PLAYER_NAME

    # initializing the objects used througout the program
    transport, engine = await chess.engine.popen_uci(ConfigData.ENGINE_PATH)
    await engine.configure({"Threads": ConfigData.THREADS})
    strategy = STRATEGIES[ConfigData.ENGINE_ANALYSIS_TYPE]
    analyzer = EngineAnalyzer(engine, strategy)
    test = Player(player_name)
    stats = PlayerStats(test)

    pickle_file = f"data/analysis{player_name}{ConfigData.ENGINE_ANALYSIS_TYPE}.pkl"
    file_path = f"/home/kkrec/chessgames/{player_name}.pgn"

    # loading/saving analyzed games
    if os.path.exists(pickle_file):
        all_games_data = loading.load_from_pickle(pickle_file)
        loading.decode_from_pickle(all_games_data, test, analyzer)

    elif os.path.exists(file_path):
        games_list = loading.load_from_file(file_path, test, analyzer, pickle_file)
        await loading.analyze(games_list, test, analyzer, pickle_file)

    else:
        print("Found the profile")
        data = await loading.get_games_from_lichess(
            player_name, ["rapid", "blitz", "classical, bullet"]
        )
        print("Found the games")
        await loading.analyze(data, test, analyzer, pickle_file)

    # everything under it is just testing how the program has calculated the stats
    # will be changed a lot, will take shape after having a distinct first alpha version

    with Timer("basic stats"):
        print("Winrate:", stats.winrate_stats.winrate, "%")
        print("Short game rate:", stats.winrate_stats.short_game_rate, "%")
        print("Short game winrate:", stats.winrate_stats.short_game_win_rate, "%")
        print("Endgame rate:", stats.winrate_stats.endgame_rate, "%")
        print("Endgame win rate:", stats.winrate_stats.endgame_win_rate, "%")
    await engine.quit()

    with Timer("stats based on acpl"):
        with Timer("Coefficient of variation time"):
            print("Coefficient of variation: ", await stats.acpl_stats.coefficient_of_variation())

        with Timer("Opening coefficient of variation time"):
            print(
                "Opening coefficient of variation",
                stats.acpl_stats.coefficient_of_variation_opening,
            )
        with Timer("Midgame coefficient of variation time"):
            print(
                "Midgame coefficient of variation",
                stats.acpl_stats.coefficient_of_variation_midgame,
            )
        with Timer("Endgame coefficient of variation time"):
            print(
                "Endgame coefficient of variation: ",
                stats.acpl_stats.coefficient_of_variation_endgame,
            )

        with Timer("All game blunder sev"):
            print(
                "Blunder severity",
                stats.tactical_stats.average_blunder_rate,
            )
            print("Opening severity", stats.tactical_stats.opening_mistake_rate)
            print("Midgame severity", stats.tactical_stats.midgame_mistake_rate)
            print("Endgame severity", stats.tactical_stats.endgame_mistake_rate)

    with Timer("opening name check"):
        print("Winrate_per_eco: ", stats.opening_stats.winrate_per_eco, "%")
        print("Three best performing openings", stats.opening_stats.three_best_performing_openings)

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

        print(
            f"how often you get developed faster: {stats.development_stats.development_advantage_percentage}%"
        )

    with Timer("Volatilities check"):
        print(f"mean of volatilities: {stats.volatility_stats.mean}")
        print(f"volatility index for calculation: {stats.volatility_stats.index()}")

    with Timer("Blunder check"):
        print(
            f"amount of moves: {sum(len(game.move_analysis) for game in stats.player.iterate_games())}"
        )
        print(
            f"amount of blunders: {sum(game.blunder_count for game in stats.player.iterate_games())}"
        )

        print(f"blunder rate: {stats.tactical_stats.blunder_rate}%")

    """with Timer("sacrifice percentage"):
        print(f"percentage of sacced games: {stats.sacrifice_percentage()}%")"""

    with Timer("percentage of game forcing moves analysis"):
        print(f"percentage of forced moves: {stats.tactical_stats.percentage_of_forcing_moves}%")

    with Timer("mobile moves"):
        print(f"percentage of mobile moves: {stats.tactical_stats.percentage_of_mobile_moves}%")

    with Timer("pressure gains"):
        print(f"Average of pressure gains: {stats.development_stats.mean_of_development_gains}")

    with Timer("Performance"):
        print(f"Mean enemy rating: {stats.performance_stats.mean_enemy_rating}")
        print(f"Performance measure: {stats.performance_stats.performance}")

    with Timer("piece type analysis"):
        dist = stats.piece_stats.piece_type_distribution
        pct = stats.piece_stats.piece_type_percentages

        print("\n=== Piece Type Distribution ===")
        for piece_type, count in sorted(dist.items(), key=lambda x: x[1], reverse=True):
            percentage = pct[piece_type]
            print(f"{piece_type:8} {count:4} moves ({percentage:5.1f}%)")

        print("\nInterpretation:")
        knight_pct = pct.get(chess.KNIGHT, 0)
        bishop_pct = pct.get(chess.BISHOP, 0)
        if knight_pct + bishop_pct > 33:
            print("  → Tactical player (lots of minor pieces)")

        pawn_pct = pct.get(chess.PAWN, 0)
        if pawn_pct > 33:
            print("  → Positional player (lots of pawn moves)")

        queen_pct = pct.get(chess.QUEEN, 0)
        if queen_pct > 15:
            print("  → Aggressive player (lots of queen moves)")

    with Timer("Comeback rate analysis"):
        print(f"Comeback rate: {stats.comeback_stats.comeback_rate}%")

    with Timer("Lost chances analysis"):
        print(f"Lost chances rate: {stats.comeback_stats.lost_chances_rate}%")

        """    with Timer("Gambit Check"):
        for nr, game in enumerate(test.Games[:1000]):
            if game.is_gambit:
                print(game.opening_name)
                print(nr)
                print()"""


if __name__ == "__main__":
    asyncio.run(main())
