from collections import OrderedDict
from dataclasses import dataclass, field

import chess
import chess.engine
import chess.pgn

import enums as enums
import analyzedgame
from utils.Config import ConfigData
from utils.EngineStrategies import EngineStrategies
from utils.moveanalysis import MoveAnalysis


@dataclass
class EngineAnalyzer:
    engine: chess.engine.Protocol
    strategy: EngineStrategies
    cache: OrderedDict = field(default_factory=OrderedDict)

    def _cache_get(self, fen: str) -> tuple[int | None, list[chess.Move]] | None:
        if fen in self.cache:
            self.cache.move_to_end(fen)
            return self.cache[fen]
        return None

    def _cache_set(self, fen: str, value: tuple[int | None, list[chess.Move]]) -> None:
        if fen in self.cache:
            self.cache.move_to_end(fen)
        else:
            if len(self.cache) >= ConfigData.MAX_CACHE_SIZE:
                self.cache.popitem(last=False)
        self.cache[fen] = value

    @staticmethod
    def _score_to_value(score: chess.engine.Score) -> int | None:
        """Changes the engine score into a float taking into consideration
        mate values"""

        if score.is_mate():
            value = 10000 if score.mate() > 0 else -10000
        else:
            value = score.score()
        return value

    async def get_eval_and_pv(self, board: chess.Board) -> tuple[int | None, list[chess.Move]]:
        """Gets an engine evaluation and full principal variation for a position."""

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
            info=chess.engine.INFO_SCORE | chess.engine.INFO_PV,
        )
        score = self._score_to_value(info["score"].white())
        pv = info.get("pv") or []

        self._cache_set(fen, (score, pv))
        return score, pv

    async def get_eval_and_best_move(
        self, board: chess.Board
    ) -> tuple[int | None, chess.Move | None]:

        score, pv = await self.get_eval_and_pv(board)
        best_move = pv[0] if pv else None
        return score, best_move

    async def analyze_game(self, game: chess.pgn.Game) -> list[MoveAnalysis]:
        """Gathers all of the evaluations for a single game"""
        board = game.board()
        result = []
        development = {
            chess.WHITE: {
                "developed": set(),
                "castled": False,
                "early_queen": False,
                "center_pawns": set(),
                "lost_tempos": 0,
                "rook_moves": 0,
            },
            chess.BLACK: {
                "developed": set(),
                "castled": False,
                "early_queen": False,
                "center_pawns": set(),
                "lost_tempos": 0,
                "rook_moves": 0,
            },
        }

        prev_eval, best_move = await self.get_eval_and_best_move(board)
        node = game
        best_board = board.copy(stack=False)
        if best_move is not None:
            best_board.push(best_move)

            best_eval, _ = await self.get_eval_and_best_move(best_board)

        while not node.is_end():
            moving_color = board.turn

            node = node.variations[0]
            move = node.move
            piece = board.piece_at(move.from_square)
            piece_type = piece.piece_type
            color = piece.color

            match piece.piece_type:
                case chess.BISHOP | chess.KNIGHT:
                    start_piece = enums.STARTING_PIECES[color].get(move.from_square)

                    if start_piece and start_piece not in development[color]["developed"]:
                        development[color]["developed"].add(start_piece)
                    elif start_piece in development[color]["developed"]:
                        development[color]["lost_tempos"] += 1
                case chess.QUEEN:
                    if (
                        not development[color]["early_queen"]
                        and len(development[color]["developed"]) < 4
                    ):
                        development[color]["early_queen"] = True

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
                        development[color]["rook_moves"] += 1

            if board.is_castling(move):
                development[color]["castled"] = True

            mobility_before = analyzedgame.mobility(board, color)
            king_pressure_before = analyzedgame.king_pressure(board, color)

            board.push(move)

            current_eval, response_pv = await self.get_eval_and_pv(board)

            if move == best_move:
                loss = 0
            elif best_eval is None:
                loss = 0
            elif moving_color == chess.WHITE:
                loss = max(0, best_eval - current_eval)
            else:
                loss = max(0, current_eval - best_eval)

            mobility_after = analyzedgame.mobility(board, color)
            king_pressure_after = analyzedgame.king_pressure(board, color)

            is_mobile = mobility_after > mobility_before
            pressure_gain = king_pressure_after - king_pressure_before

            development_adv = self.development_score(
                development[chess.WHITE]
            ) - self.development_score(development[chess.BLACK])
            result.append(
                MoveAnalysis(
                    move,
                    loss,
                    prev_eval,
                    current_eval,
                    moving_color,
                    piece_type,
                    development_adv,
                    is_mobile,
                    pressure_gain,
                )
            )

            prev_eval = current_eval
        return result

    @staticmethod
    def color_half_control(board, color):
        return sum(
            1
            for sq, piece in board.piece_map().items()
            if piece.color == color and chess.square_rank(sq) >= 4
        )

    @staticmethod
    def development_score(dev):
        score = 0.0

        score += len(dev["developed"]) * ConfigData.DEVELOPED_PIECE_BONUS
        score -= dev["lost_tempos"] * ConfigData.TEMPO_LOSS
        score += len(dev["center_pawns"]) * ConfigData.CENTER_PAWN_BONUS
        score -= dev["rook_moves"] * ConfigData.ROOK_MOVE_LOSS

        if dev["castled"]:
            score += ConfigData.CASTLING_BONUS

        if dev["early_queen"] and len(dev["developed"]) < 4:
            score -= ConfigData.QUEEN_LOSS

        return score
