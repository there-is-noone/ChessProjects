from collections import deque
from dataclasses import dataclass
from utils.moveanalysis import MoveAnalysis
import chess.engine
import chess.pgn


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

        info = self.engine.analyse(board, chess.engine.Limit(depth=10))

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
