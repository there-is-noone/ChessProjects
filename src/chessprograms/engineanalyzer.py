from collections import OrderedDict
from dataclasses import dataclass, field

import chess
import chess.engine
import chess.pgn
from chessprograms.utils.Config import ConfigData
from chessprograms.utils.EngineStrategies import EngineStrategies
from chessprograms.utils.moveanalysis import MoveAnalysis
import chessprograms.enums as enums

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
        development = {
            chess.WHITE: {
                "developed": set(),
                "castled": False,
                "queen_moved": False,
                "early_queen":False,
                "center_pawns": set(),
                "lost_tempos": 0,
                "rook_moves" : 0
            },
            chess.BLACK: {
                "developed": set(),
                "castled": False,
                "queen_moved": False,
                "early_queen":False,
                "center_pawns": set(),
                "lost_tempos" : 0,
                "rook_moves": 0
            },
        }

        prev_eval = await self.get_eval(board)

        node = game

        while not node.is_end():
            moving_color = board.turn

            node = node.variations[0]
            move = node.move
            piece = board.piece_at(move.from_square)
            color = piece.color
            match piece.piece_type:
                case chess.BISHOP | chess.KNIGHT:
                    start_piece = enums.STARTING_PIECES[color].get(move.from_square)

                    if (
                            start_piece
                            and start_piece not in development[color]["developed"]
                    ):
                        development[color]["developed"].add(start_piece)
                    elif start_piece in development[color]["developed"]:
                        development[color]["lost_tempos"]+=1
                case chess.QUEEN:
                    if (
                            not development[color]["queen_moved"]
                            and len(development[color]["developed"]) < 4
                    ):
                        development[color]["early_queen"] = True

                    development[color]["queen_moved"] = True



                case chess.PAWN:
                    if move.from_square in (
                            chess.D2,
                            chess.E2,
                            chess.D7,
                            chess.E7,
                    ):
                        development[color]["center_pawns"].add(move.from_square)
                case chess.ROOK:
                    if not development[color]["castled"]:
                        development[color]["rook_moves"]+=1


            if board.is_castling(move):
                development[color]["castled"] = True


            board.push(move)

            current_eval = await self.get_eval(board)

            if moving_color == chess.WHITE:
                loss = max(0.0, prev_eval - current_eval)
            else:
                loss = max(0.0, current_eval - prev_eval)

            development_adv=self.development_score(development[chess.WHITE])-self.development_score(development[chess.BLACK])
            result.append(
                MoveAnalysis(
                    move,
                    loss,
                    prev_eval,
                    current_eval,
                    moving_color,
                    development_adv
                )
            )

            prev_eval = current_eval

        return result

    @staticmethod
    def development_score(dev):
        score = 0.0

        score += len(dev["developed"])
        score -= dev["lost_tempos"]*0.5
        score += len(dev["center_pawns"])*0.5
        score -= dev["rook_moves"]

        if dev["castled"]:
            score += 2

        if dev["early_queen"] and len(dev["developed"]) < 4:
            score -= 1


        return score