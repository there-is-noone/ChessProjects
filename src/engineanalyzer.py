from dataclasses import dataclass, field

import chess.engine
import chess
from utils.moveanalysis import MoveAnalysis
from utils.EngineStrategies import EngineStrategies
import chess.engine
import chess.pgn
from utils.Config import ConfigData
from collections import OrderedDict


@dataclass
class EngineAnalyzer:
    engine: chess.engine.Protocol
    strategy: EngineStrategies
    cache: OrderedDict = field(default_factory=OrderedDict)

    def _cache_get(self, fen: str) -> float | None:
        if fen in self.cache:
            self.cache.move_to_end(fen)
            return self.cache[fen]
        return None

    def _cache_set(self, fen: str, value: float) -> None:
        if fen in self.cache:
            self.cache.move_to_end(fen)
        else:
            if len(self.cache) >= ConfigData._MAX_CACHE_SIZE:
                self.cache.popitem(last=False)
        self.cache[fen] = value

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

        cached = self._cache_get(fen)
        if cached is not None:
            return cached
        info = await self.engine.analyse(
            board,
            limit,
            info=chess.engine.INFO_SCORE,
        )

        score = self._score_to_value(info["score"].relative)

        self._cache_set(fen, score)
        return score

    async def analyze_game(self, game: chess.pgn.Game) -> list[MoveAnalysis]:
        board = game.board()
        result = []
        if game.eval():
            prev_eval = self._score_to_value(game.eval().pov(board.turn))
        else:
            prev_eval = await self.get_eval(board)
        node = game

        while not node.is_end():
            moving_color = board.turn
            node = node.variations[0]
            move = node.move
            board.push(move)

            if node.eval():
                score = node.eval().pov(moving_color)
                current_eval = self._score_to_value(score)
            elif (
                abs(prev_eval) > self.strategy.evaluation_threshold
                or board.ply() % self.strategy.eval_every_n_moves != 0
            ):
                current_eval = prev_eval
            else:
                raw_eval = await self.get_eval(board)
                current_eval = raw_eval if board.turn == moving_color else -raw_eval
            loss = max(0.0, prev_eval - current_eval)


            result.append(
                MoveAnalysis(move, loss, prev_eval, current_eval, moving_color)
            )

            prev_eval = -current_eval

        return result
