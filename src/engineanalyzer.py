import asyncio
from dataclasses import dataclass,field
from utils.moveanalysis import MoveAnalysis
import chess.engine
import chess.pgn


@dataclass
class EngineAnalyzer:
    engine: chess.engine.Protocol
    cache: dict = field(default_factory=dict)

    async def get_eval(self, board):
        fen = board.fen()

        if fen in self.cache:
            return self.cache[fen]

        info = await self.engine.analyse(board, chess.engine.Limit(nodes=40000), info=chess.engine.INFO_SCORE)

        score = info["score"].relative

        if score.is_mate():
            value = 10000 if score.mate() > 0 else -10000
        else:
            value = score.score()

        self.cache[fen] = value

        return value

    async def analyze_game(self, game):
        board = game.board()
        result = []
        prev_eval = await self.get_eval(board)
        for move in game.mainline_moves():
            board.push(move)
            if abs(prev_eval) > 500:
                current_eval = prev_eval
                loss = 0
            else:
                current_eval = await self.get_eval(board)
                loss = abs(prev_eval - current_eval)

            result.append(MoveAnalysis(move, loss, prev_eval, current_eval))
            prev_eval = current_eval

        return result
