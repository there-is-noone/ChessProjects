import pickle

import chess.pgn

from analyzedgame import AnalyzedGame, serialize_game
from engineanalyzer import EngineAnalyzer
from player import Player
from utils.moveanalysis import MoveAnalysis
from utils.stopwatch import Timer


def load_from_file(file, player: Player, analyzer: EngineAnalyzer, pickle_file):
    with open(file, encoding="utf-8") as games:
        with Timer("Full analysis time"):
            games_list = []

            while game := chess.pgn.read_game(games):
                # If moves are broken/from different starting board, throws an error
                if "correspondence" in game.headers["Event"]:
                    continue
                games_list.append(game)
            return games_list


def load_from_pickle(file):
    with Timer("pickle read"):
        with open(file, "rb") as f:
            all_games_data = pickle.load(f)
    return all_games_data


def decode_from_pickle(all_games_data: list, player: Player, analyzer: EngineAnalyzer):
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
            analyzed = AnalyzedGame(game, analyzer, player.which_color_is_player(game))
            piece_types = pickled_game.get("piece_types")
            analyzed._acpl_player = pickled_game.get("acpl_white")
            analyzed._acpl_opening = pickled_game.get("acpl_opening")

            if "losses" in pickled_game and "moves" in pickled_game:
                development = pickled_game.get("development")
                if development is None:
                    development = [0.0] * len(pickled_game["moves"])

                # gathering all information from decoding in one big list of moves
                analyzed.move_analysis = [
                    MoveAnalysis(
                        move=chess.Move.from_uci(m_uci),
                        loss=loss_val,
                        eval_before=eval_before_val,
                        eval_after=eval_after_val,
                        color=chess.WHITE if idx % 2 == 0 else chess.BLACK,
                        piece_type=piece_type,
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
                        piece_type,
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
                            piece_types,
                            # pickled_game["is_sacrifices"],
                            pickled_game["is_mobile"],
                            pickled_game["development_gains"],
                            strict=True,
                        )
                    )
                ]
                player.add_game(analyzed)


async def analyze(
    data: list[chess.pgn.Game],
    player: Player,
    analyzer: EngineAnalyzer,
    pickle_file: str | None = None,
):
    print("start Analyzing")
    with Timer("game analysis"):
        all_games_data = []
        for game in data:
            analyzed_game = AnalyzedGame(game, analyzer, player.which_color_is_player(game))
            await analyzed_game.calculate_acpl()
            player.add_game(analyzed_game)

            all_games_data.append(serialize_game(analyzed_game))
    if pickle_file is not None:
        with Timer("pickling the games"):
            with open(pickle_file, "wb") as f:
                pickle.dump(all_games_data, f)
