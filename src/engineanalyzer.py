from dataclasses import dataclass, field

import chess.engine
import chess
from utils.moveanalysis import MoveAnalysis
from utils.EngineStrategies import EngineStrategies
import chess.engine
import chess.pgn


@dataclass
class EngineAnalyzer:
    engine: chess.engine.Protocol
    strategy: EngineStrategies
    cache: dict = field(default_factory=dict)

    @staticmethod
    def _score_to_value(score: chess.engine.Score) -> float:
        if score.is_mate():
            value = 10000 if score.mate() > 0 else -10000
        else:
            value = score.score()
        return value

    async def get_eval(self, board: chess.Board) -> float:

        if self.strategy.time_limit:
            limit = chess.engine.Limit(time=self.strategy.time_limit)
        else:
            limit = chess.engine.Limit(nodes=self.strategy.nodes)

        fen = board.fen()

        if fen in self.cache:
            return self.cache[fen]

        info = await self.engine.analyse(
            board,
            limit,
            info=chess.engine.INFO_SCORE,
        )

        score = info["score"].relative

        if score.is_mate():
            value = 10000 if score.mate() > 0 else -10000
        else:
            value = score.score()

        self.cache[fen] = value
        return value

    async def analyze_game(self, game: chess.pgn.Game) -> list[MoveAnalysis]:
        board = game.board()
        result = []
        if game.eval():
            prev_eval = game.eval().pov(board.turn)
        else:
            prev_eval = await self.get_eval(board)
        node = game

        while not node.is_end():
            move = node.variations[0].move
            node = node.variations[0]
            board.push(move)
            if node.eval():
                score = node.eval().pov(board.turn)
                current_eval = self._score_to_value(score)
                loss = abs(prev_eval - current_eval)
            if (
                abs(prev_eval) > self.strategy.evaluation_threshold
                or board.ply() % self.strategy.eval_every_n_moves != 0
            ):
                current_eval = prev_eval
                loss = 0

            else:
                current_eval = await self.get_eval(board)
                loss = abs(prev_eval - current_eval)

            result.append(MoveAnalysis(move, loss, prev_eval, current_eval))
            prev_eval = current_eval

        return result
