# testing.py
import asyncio
import chess
import chess.engine
from utils.Config import ConfigData
import loading


ENGINE_PATH = ConfigData.ENGINE_PATH
PLAYER_NAME = "gracznumerx"

PERF_TYPES = [
    "rapid",
    "blitz",
    "classical",
]

NUMBER_OF_GAMES = 50

# High-quality reference.
REFERENCE_NODES = 500000

# Start cheap and double.
START_NODES = 10_000
MULTIPLIER = 2

# ACPL must be within this percentage of the reference.
ACPL_TOLERANCE = 0.05

# Require several consecutive successful node levels.
CONSECUTIVE_MATCHES = 3

# Keep CPU usage under control.
THREADS = 7


def evaluate(engine, board, nodes):
    result = engine.analyse(
        board,
        chess.engine.Limit(nodes=nodes),
    )

    return result["score"].pov(board.turn).score(
        mate_score=100000
    )


def calculate_acpl(engine, game, nodes):
    board = game.board()

    total_loss = 0
    move_count = 0

    for move in game.mainline_moves():

        # Evaluation before the player's move.
        before = evaluate(
            engine,
            board,
            nodes,
        )

        player = board.turn

        board.push(move)

        # Evaluate from the perspective of the player
        # who just made the move.
        after = evaluate(
            engine,
            board,
            nodes,
        )

        if before is None or after is None:
            continue

        loss = max(0, before - after)

        total_loss += loss
        move_count += 1

    if move_count == 0:
        return None

    return total_loss / move_count


def relative_difference(value, reference):
    if reference == 0:
        return 0 if value == 0 else float("inf")

    return abs(value - reference) / abs(reference)


async def main():

    print("Loading games from Lichess...")

    games = await loading.get_games_from_lichess(
        PLAYER_NAME,
        PERF_TYPES,
        max_games=NUMBER_OF_GAMES,
    )

    games = games[:NUMBER_OF_GAMES]

    print(f"Loaded {len(games)} games.")

    engine = chess.engine.SimpleEngine.popen_uci(
        ENGINE_PATH
    )

    engine.configure({
        "Threads": THREADS,
    })

    try:

        # --------------------------------------------------
        # REFERENCE
        # --------------------------------------------------

        print("\n" + "=" * 70)
        print("REFERENCE ANALYSIS")
        print("=" * 70)

        reference_acpl = []

        for index, game in enumerate(games, start=1):

            print(
                f"Reference game "
                f"{index}/{len(games)}..."
            )

            acpl = calculate_acpl(
                engine,
                game,
                REFERENCE_NODES,
            )

            reference_acpl.append(acpl)

            print(f"ACPL: {acpl:.2f}")

        # --------------------------------------------------
        # TEST DIFFERENT NODE COUNTS
        # --------------------------------------------------

        print("\n" + "=" * 70)
        print("NODE CALIBRATION")
        print("=" * 70)

        nodes = START_NODES
        consecutive = 0

        while nodes <= REFERENCE_NODES:

            print("\n" + "-" * 70)
            print(f"TESTING {nodes:,} NODES")
            print("-" * 70)

            differences = []
            test_acpl = []

            for index, game in enumerate(games):

                print(
                    f"Game "
                    f"{index + 1}/{len(games)}...",
                    end=" ",
                    flush=True,
                )

                acpl = calculate_acpl(
                    engine,
                    game,
                    nodes,
                )

                reference = reference_acpl[index]

                difference = relative_difference(
                    acpl,
                    reference,
                )

                test_acpl.append(acpl)
                differences.append(difference)

                print(
                    f"ACPL={acpl:.2f} "
                    f"reference={reference:.2f} "
                    f"difference={difference * 100:.2f}%"
                )

            # ----------------------------------------------
            # Whole dataset statistics
            # ----------------------------------------------

            mean_difference = (
                sum(differences) / len(differences)
            )

            matching_games = sum(
                difference <= ACPL_TOLERANCE
                for difference in differences
            )

            matching_percentage = (
                matching_games / len(differences)
            )

            print()
            print(
                f"Mean ACPL difference: "
                f"{mean_difference * 100:.2f}%"
            )

            print(
                f"Games within 5%: "
                f"{matching_games}/{len(games)} "
                f"({matching_percentage * 100:.1f}%)"
            )

            # ----------------------------------------------
            # Stability criterion
            # ----------------------------------------------

            if matching_percentage >= 0.95:
                consecutive += 1

                print(
                    f"PASS "
                    f"({consecutive}/{CONSECUTIVE_MATCHES})"
                )

                if consecutive >= CONSECUTIVE_MATCHES:

                    print("\n" + "=" * 70)
                    print(
                        f"STABLE NODE COUNT: "
                        f"{nodes:,}"
                    )
                    print("=" * 70)

                    break

            else:
                consecutive = 0

                print("FAIL")

            nodes *= MULTIPLIER

        else:

            print("\nNo stable node count found.")

    finally:
        engine.quit()


if __name__ == "__main__":
    asyncio.run(main())
