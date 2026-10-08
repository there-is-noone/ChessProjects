import asyncio
import pickle
from io import StringIO

import aiohttp
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
                        pressure_gain=pressure_gain,
                    )
                    for idx, (
                        m_uci,
                        loss_val,
                        eval_before_val,
                        eval_after_val,
                        dev_adv,
                        piece_type,
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
                            pickled_game["is_mobile"],
                            pickled_game["development_gains"],
                            strict=True,
                        )
                    )
                ]
                player.add_game(analyzed)


async def get_games_from_lichess(
    username: str,
    perf_types: list[str] | None = None,
    max_games: int | None = 50,
    rated_only: bool | None = True,
) -> list[chess.pgn.Game]:

    url = f"https://lichess.org/api/games/user/{username}"

    headers = {
        "Accept": "application/x-chess-pgn",
        "User-Agent": "chessprograms/1.0 (https://https://github.com/there-is-noone/ChessProjects)",
    }

    params = {
        "moves": "true",
        "finished": "true",
        "clocks": "true",
        "evals": "true",
        "opening": "true",
    }

    if max_games is not None:
        params["max"] = str(max_games)

    if perf_types:
        params["perfType"] = ",".join(perf_types)

    if rated_only is not None:
        params["rated"] = str(rated_only).lower()

    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(
                url,
                headers=headers,
                params=params,
            ) as response:
                if response.status == 404:
                    raise ValueError(f"Lichess user '{username}' was not found")

                if response.status == 429:
                    print("429")
                    retry_after = response.headers.get("Retry-After", "10")

                    wait_time = int(retry_after)
                    print(wait_time)
                    await asyncio.sleep(wait_time)
                    print()
                    continue

                response.raise_for_status()

                pgn_text = await response.text()

                break

        games = []
        pgn_io = StringIO(pgn_text)

    while game := chess.pgn.read_game(pgn_io):
        games.append(game)

    print(len(games))
    return games


async def analyze(
    data: list[chess.pgn.Game], player: Player, analyzer: EngineAnalyzer, pickle_file
):
    print("start Analyzing")
    with Timer("game analysis"):
        all_games_data = []
        for game in data:
            analyzed_game = AnalyzedGame(game, analyzer, player.which_color_is_player(game))
            await analyzed_game.calculate_acpl()
            player.add_game(analyzed_game)

            all_games_data.append(serialize_game(analyzed_game))

    with Timer("pickling the games"):
        with open(pickle_file, "wb") as f:
            pickle.dump(all_games_data, f)
