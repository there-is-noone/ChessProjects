from collections import OrderedDict
from dataclasses import dataclass, field

import chess
import chess.engine
import chess.pgn

import chessprograms.enums as enums
from chessprograms import analyzedgame
from chessprograms.utils.Config import ConfigData
from chessprograms.utils.EngineStrategies import EngineStrategies
from chessprograms.utils.moveanalysis import MoveAnalysis


@dataclass
class EngineAnalyzer:
    engine: chess.engine.Protocol
    strategy: EngineStrategies
    cache: OrderedDict = field(default_factory=OrderedDict)

    def _cache_get(self, fen: str) -> tuple[int, chess.Move | None] | None:
        if fen in self.cache:
            self.cache.move_to_end(fen)
            return self.cache[fen]
        return None

    def _cache_set(self, fen: str, value: tuple[int | None, chess.Move | None]) -> None:
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
        """Back-compat wrapper — same signature as before, first PV move only."""
        score, pv = await self.get_eval_and_pv(board)
        best_move = pv[0] if pv else None
        return score, best_move

    async def _walk_forward_until_settled(
        self,
        board: chess.Board,
        color: chess.Color,
        diff_before: int,
        max_plies: int,
        target_square: chess.Square,
    ) -> int:
        """Follows recaptures on target_square only — the square the
        triggering move just landed on. A capture or check elsewhere on the
        board is a separate tactical event and shouldn't be folded into this
        move's material verdict, even though it's technically 'forcing'."""
        pushed = 0
        while pushed < max_plies:
            _, pv = await self.get_eval_and_pv(board)
            if not pv:
                break
            candidate = pv[0]
            if not board.is_legal(candidate):
                break
            if not (board.is_capture(candidate) and candidate.to_square == target_square):
                break  # not a recapture on this square -- different event, stop here
            board.push(candidate)
            pushed += 1
            diff_now = analyzedgame.material_diff(board, color)
            if diff_before - diff_now <= ConfigData.SACRIFICE_MATERIAL_THRESHOLD:
                break
        return pushed

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

        pieces_offensive = self.color_half_control(board, board.turn)
        tmp = game
        count = 0

        while not node.is_end():
            moving_color = board.turn

            node = node.variations[0]
            move = node.move
            piece = board.piece_at(move.from_square)
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

            material_before = analyzedgame.total_material(board, color)
            mobility_before = analyzedgame.mobility(board, color)
            king_pressure_before = analyzedgame.king_pressure(board, color)

            board.push(move)

            current_eval, response_pv = await self.get_eval_and_pv(board)
            enemy_best_move = response_pv[0] if response_pv else None
            # is_sacrifice = False
            is_mobile = False
            pressure_gain = 0

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

            """if enemy_best_move is not None:
            
                has_capture_available = any(board.is_capture(m) for m in board.legal_moves)

                if has_capture_available:
                    diff_before = analyzedgame.material_diff(board, color)
                    print(board.fen())
                    plies_pushed = await self._walk_forward_until_settled(
                        board, color, diff_before, ConfigData.SACRIFICE_QUIESCENCE_PLIES,move.to_square
                    )

                    diff_after = analyzedgame.material_diff(board, color)

                    if diff_before - diff_after > ConfigData.SACRIFICE_MATERIAL_THRESHOLD:
                        if not analyzedgame.AnalyzedGame.is_endgame(board):
                            print("FOUND A SAC")
                            print(diff_before - diff_after)
                            print(board.fen())
                            print()
                            is_sacrifice = True

                    for _ in range(plies_pushed):
                        board.pop()"""

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
                    development_adv,
                    is_sacrifice,
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
