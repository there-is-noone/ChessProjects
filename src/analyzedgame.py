from dataclasses import dataclass, field
import utils.math_stat as math_stats
from engineanalyzer import EngineAnalyzer
import chess.pgn
from utils.moveanalysis import MoveAnalysis


@dataclass(repr=False)
class AnalyzedGame:
    game: chess.pgn.Game
    analyzer: EngineAnalyzer
    _move_analysis: list[MoveAnalysis] = field(default_factory=list)
    _acpl_white: float | None = field(default=None)
    _acpl_black: float | None = field(default=None)
    _acpl_opening: float | None = field(default=None)
    _acpl_ending: float | None = field(default=None)
    _transition_opening_to_mid: int | None = field(default=None)
    _transition_mid_to_endgame:int | None = field(default=None)
    def get_result(self) -> str:
        return self.game.headers["Result"]

    def __str__(self):
        return self.game.headers

    def how_many_moves(self) -> int:
        return self.game.end().ply() // 2

    def find_ending_flag(self) -> str:
        """checks for the way that the game ended with"""

        board = self.game.end().board()
        outcome = board.outcome()

        if outcome:
            return outcome.termination.name.lower()

        return self.game.headers.get("Termination", "unknown").lower()

    async def get_analysis(self):
        """returns the analysis of the Game"""
        if not self._move_analysis:
            self._move_analysis = await self.analyzer.analyze_game(self.game)
        return self._move_analysis

    async def precompute_acpl(self):
        """Computes the acpl for a game for each of the colors separately"""
        if self._acpl_white is not None and self._acpl_black is not None:
            return
        moves = await self.get_analysis()

        white_moves = [m for m in moves if m.color == chess.WHITE]
        black_moves = [m for m in moves if m.color == chess.BLACK]
        self._acpl_white = (
            math_stats.mean([m.loss for m in white_moves]) if white_moves else 0.0
        )
        self._acpl_black = (
            math_stats.mean([m.loss for m in black_moves]) if black_moves else 0.0
        )

    async def get_acpl_for_color(self, color: chess.Color) -> float | None:
        """Return cached per-color ACPL. Triggers precompute_acpl if not yet done."""

        if self._acpl_white is None or self._acpl_black is None:
            await self.precompute_acpl()
        return self._acpl_white if color == chess.WHITE else self._acpl_black

    async def get_acpl(self) -> float:
        """Overall average centipawn loss (both sides combined)."""
        moves = await self.get_analysis()
        return math_stats.mean([m.loss for m in moves]) if moves else 0.0

    @staticmethod
    def is_endgame(board: chess.Board) -> bool:
        pieces = board.piece_map()

        non_pawn = sum(1 for piece in pieces.values() if piece.piece_type != chess.PAWN)

        queens = sum(1 for piece in pieces.values() if piece.piece_type == chess.QUEEN)

        return queens == 0 or non_pawn <= 6

    def ends_in_endgame(self) -> bool:
        """Checks if the game ends in an endgame"""

        board = self.game.end().board()
        return self.is_endgame(board)

    @staticmethod
    def is_opening(board: chess.Board) -> bool:
        """checks if the position is in the opening using heuristics"""

        if board.ply() < 14:
            return True
        elif board.ply() > 40:
            return False

        is_developed = False
        white_opening_pieces = (
            board.pieces(chess.KNIGHT, chess.WHITE)
            | board.pieces(chess.BISHOP, chess.WHITE)
            | board.pieces(chess.QUEEN, chess.WHITE)
        )
        black_opening_pieces = (
            board.pieces(chess.KNIGHT, chess.BLACK)
            | board.pieces(chess.BISHOP, chess.BLACK)
            | board.pieces(chess.QUEEN, chess.BLACK)
        )
        white_undeveloped = white_opening_pieces & chess.BB_RANK_1
        black_undeveloped = black_opening_pieces & chess.BB_RANK_8
        if len(white_undeveloped) <= 2 and len(black_undeveloped) <= 2:
            is_developed = True

        kings_castled = not board.has_castling_rights(chess.WHITE) and (
            not board.has_castling_rights(chess.BLACK)
        )

        return not (is_developed or kings_castled)

    @property
    def transition_opening_to_mid(self):
        """Finds the move that is the assumed breakpoint between the opening and middlegame"""

        if self._transition_opening_to_mid is None:
            board = chess.Board()

            for move in self.game.mainline_moves():
                board.push(move)

                if not self.is_opening(board):
                    self._transition_opening_to_mid = board.ply()
                    break

            if self._transition_opening_to_mid is None:
                self._transition_opening_to_mid = board.ply()
        return self._transition_opening_to_mid

    @property
    def acpl_opening(self):
        """calculates the acpl for entire opening phase of the game"""

        if self._acpl_opening is None:
            if not self._move_analysis:
                return 0.0

            opening_moves = []
            current_ply = 0

            for m in self._move_analysis:
                if current_ply < self.transition_opening_to_mid:
                    opening_moves.append(m)
                current_ply += 1

            if not opening_moves:
                self._acpl_opening = 0.0
            else:
                self._acpl_opening = math_stats.mean([m.loss for m in opening_moves])

        return self._acpl_opening

    @property
    def transition_mid_to_end(self):
        """Finds the move that is the assumed breakpoint between the opening and middlegame"""

        if not self._transition_mid_to_end:
            board = chess.Board()
            node = self.game
            while not node.is_end():
                node = node.variations[0]
                board.push(node.move)

                if not self.is_endgame(board):
                    self._transition_mid_to_endgame = board.ply()
                    break

            if not self._transition_mid_to_endgame :
                self._transition_opening_to_mid = board.ply()
        return self._transition_opening_to_mid
    @property
    def acpl_ending(self):
        if self._acpl_opening is None:
            if not self._move_analysis:
                return 0.0

            endgame_moves = []
            current_ply = 0

            for m in self._move_analysis:
                if current_ply >= self.transition_mid_to_end:
                    endgame_moves.append(m)
                current_ply += 1

            if not endgame_moves:
                self._acpl_endgame = 0.0
            else:
                self._acpl_endgame = math_stats.mean([m.loss for m in endgame_moves])

        return self._acpl_endgame

def serialize_game(analyzed: AnalyzedGame):
    """makes AnalyzedGame easier to pickle"""

    analysis = analyzed._move_analysis

    return {
        "headers": dict(analyzed.game.headers),
        "moves": [m.move.uci() for m in analysis],
        "evals": [m.eval_after for m in analysis],
        "losses": [m.loss for m in analysis],
        "acpl_opening": analyzed.acpl_opening,
        "acpl_white": analyzed._acpl_white,
        "acpl_black": analyzed._acpl_black,
    }
