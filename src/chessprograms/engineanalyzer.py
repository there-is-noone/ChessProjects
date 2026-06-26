from collections import OrderedDict
from dataclasses import dataclass, field

import chess
import chess.engine
import chess.pgn
from chessprograms.utils.Config import ConfigData
from chessprograms.utils.EngineStrategies import EngineStrategies
from chessprograms.utils.moveanalysis import MoveAnalysis


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
        """Changes the engine score into a float taking into consideration
        mate values"""

        if score.is_mate():
            value = 10000 if score.mate() > 0 else -10000
        else:
            value = score.score()
        return value

    async def get_eval(self, board: chess.Board) -> float:
        """Gets an engine evaluation for a single move"""

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
        """Gathers all of the evaluations for a single game"""

        board = game.board()
        result = []

        prev_eval = await self.get_eval(board)

        node = game

        while not node.is_end():
            moving_color = board.turn

            node = node.variations[0]
            move = node.move
            board.push(move)

            current_eval = await self.get_eval(board)

            if moving_color == chess.WHITE:
                loss = max(0.0, prev_eval - current_eval)
            else:
                loss = max(0.0, current_eval - prev_eval)

            result.append(
                MoveAnalysis(
                    move,
                    loss,
                    prev_eval,
                    current_eval,
                    moving_color,
                )
            )

            prev_eval = current_eval

        return result
