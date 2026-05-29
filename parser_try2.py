import time
from dataclasses import dataclass
import chess.pgn
import chess
import chess.engine


class Timer:
    def __init__(self, name="Timer"):
        self.name = name

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter()
        print(f"{self.name}: {(self.end - self.start):.4f}s")


@dataclass
class MoveAnalysis:
    move: chess.Move
    loss: float
    eval_before: float
    eval_after: float


@dataclass
class EngineAnalyzer:
    engine: chess.engine.SimpleEngine
    cache: dict = None

    def __post_init__(self):
        self.cache = {}

    def get_eval(self, board):
        fen = board.fen()

        if fen in self.cache:
            return self.cache[fen]

        info = self.engine.analyse(board, chess.engine.Limit(depth=12))

        score = info["score"].relative

        if score.is_mate():
            value = 10000 if score.mate() > 0 else -10000
        else:
            value = score.score()

        self.cache[fen] = value

        return value

    def analyze_game(self, game):
        board = game.board()
        result = []
        prev_eval = self.get_eval(board)

        for move in game.mainline_moves():
            board.push(move)
            if abs(prev_eval) > 500:
                current_eval = prev_eval
                loss = 0
            else:
                current_eval = self.get_eval(board)
                loss = abs(prev_eval - current_eval)

            result.append(MoveAnalysis(move, loss, prev_eval, current_eval))
            prev_eval = current_eval

        return result


@dataclass
class AnalyzedGame:
    game: chess.pgn.Game
    _move_analysis: list[MoveAnalysis]
    engine: chess.engine.SimpleEngine

    def __init__(self, game, engine):
        self.game = game
        self._move_analysis = []
        self.engine = engine

    def get_result(self) -> str:
        return self.game.headers["Result"]

    def __str__(self):
        return self.game.headers

    def how_many_moves(self) -> int:
        return self.game.end().ply() // 2

    def find_ending_flag(self) -> str:
        board = self.game.end().board()
        outcome = board.outcome()

        if outcome:
            return outcome.termination.name.lower()

        return self.game.headers.get("Termination", "unknown").lower()

    def analysis(self):
        if not self._move_analysis:
            analyzer = EngineAnalyzer(self.engine)
            self._move_analysis = analyzer.analyze_game(self.game)
        return self._move_analysis

    def get_acpl(self):
        moves = self.analysis()
        return round(sum(m.loss for m in moves) / len(moves), 2) if moves else 0


@dataclass
class Player:
    PlayerName: str
    GamesWhite: list[AnalyzedGame]
    GamesBlack: list[AnalyzedGame]
    Games: list[AnalyzedGame]

    def add_game(self, game: AnalyzedGame):
        self.Games.append(game)

        if game.game.headers["White"] == self.PlayerName:
            self.GamesWhite.append(game)

        elif game.game.headers["Black"] == self.PlayerName:
            self.GamesBlack.append(game)

    def __str__(self):
        result = ""
        for whitegame in self.GamesWhite:
            result += f"{whitegame.game.headers['White']} vs {whitegame.game.headers['Black']}:{whitegame.get_result()}\n"
        for blackgame in self.GamesBlack:
            result += f"{blackgame.game.headers['White']} vs {blackgame.game.headers['Black']}:{blackgame.get_result()}\n"
        return result

    def winrate_white(self) -> float:
        result = 0
        count = 0
        for whitegame in self.GamesWhite:
            result += self.did_player_win(whitegame, 1)
            count += 1
        return round((result / count * 100), 2) if count else 0

    def winrate_black(self) -> float:
        result = 0
        count = 0
        for blackgame in self.GamesBlack:
            result += self.did_player_win(blackgame, 0)
            count += 1
        return round((result / count) * 100, 2) if count else 0

    def winrate(self) -> float:
        count = 0
        total = 0

        for g in self.GamesWhite:
            total += self.did_player_win(g, 1)
            count += 1
        for g in self.GamesBlack:
            total += self.did_player_win(g, 0)
            count += 1
        return round((total / count) * 100, 2) if count else 0

    def did_player_win(self, game: AnalyzedGame, color: int) -> float | None:
        """Checks if the player that we're searching for won or lost
        returns:
        1.0 if won
        0.0 if lost
        0.5 for a draw"""

        if game.get_result() == "1-0":
            return 1.0 if color else 0.0
        elif game.get_result() == "0-1":
            return 0.0 if color else 1.0
        else:
            return 0.5

    def short_game_rate(self) -> float:
        counter_short = 0
        counter = 0
        for games in self.GamesWhite + self.GamesBlack:
            if games.how_many_moves() <= 25:
                counter_short += 1
            counter += 1

        return round((counter_short / counter) * 100, 2) if counter else 0

    def short_game_win_rate(self) -> float:
        counter_short_wins = 0
        counter = 0
        for games in self.GamesWhite:
            if games.how_many_moves() <= 25 and self.did_player_win(games, 1):
                counter_short_wins += 1
            counter += 1

        for games in self.GamesBlack:
            if games.how_many_moves() <= 25 and self.did_player_win(games, 0):
                counter_short_wins += 1
            counter += 1

        return round((counter_short_wins / counter) * 100, 2) if counter else 0


if __name__ == "__main__":
    stockfish = chess.engine.SimpleEngine.popen_uci(
        "/home/kkrec/stockfish/stockfish-ubuntu-x86-64-avx2"
    )
    """stockfish = Stockfish(
        "/home/kkrec/stockfish/stockfish-ubuntu-x86-64-avx2",
        depth=15,
        parameters={"Threads": 4, "Hash": 2048},
    )"""
    test = Player("gracznumerx", [], [], [])
    with open(
        "/home/kkrec/chessgames/lichess_gracznumerx_2026-05-25.pgn", encoding="utf-8"
    ) as games:
        nr = 1
        while game := chess.pgn.read_game(games):
            test.add_game(game=AnalyzedGame(game, stockfish))
            nr += 1
        print("Winrate:", test.winrate(), "%")
        print("Short game rate:", test.short_game_rate(), "%")
        print("Short game winrate:", test.short_game_win_rate(), "%")
    with Timer("All game analysis time"):
        for i, game in enumerate(test.Games[:100]):
            with Timer("ACPL timer"):
                print(i)
                print("ACPL:", game.get_acpl())
    stockfish.close()
