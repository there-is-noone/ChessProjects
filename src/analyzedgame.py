from dataclasses import dataclass, field
from engineanalyzer import EngineAnalyzer
import chess.pgn
from utils.moveanalysis import MoveAnalysis


def serialize_game(analyzed: AnalyzedGame):
    analysis = analyzed._move_analysis

    return {
        "headers": dict(analyzed.game.headers),
        "moves": [m.move.uci() for m in analysis],
        "evals": [m.eval_after for m in analysis],
        "losses": [m.loss for m in analysis],
        "acpl_white": analyzed._acpl_white,
        "acpl_black": analyzed._acpl_black,
    }


@dataclass
class AnalyzedGame:
    game: chess.pgn.Game
    analyzer: EngineAnalyzer
    _move_analysis: list[MoveAnalysis] = field(default_factory=list)
    _acpl_white: float | None = field(default=None)
    _acpl_black: float | None = field(default=None)

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

    async def get_analysis(self):
        if not self._move_analysis:
            self._move_analysis = await self.analyzer.analyze_game(self.game)
        return self._move_analysis

    async def precompute_acpl(self):
        if self._acpl_white is not None and self._acpl_black is not None:
            return
        moves = await self.get_analysis()

        white_moves = [m for m in moves if m.color == chess.WHITE]
        black_moves = [m for m in moves if m.color == chess.BLACK]
        self._acpl_white = (
            round(sum(m.loss for m in white_moves) / len(white_moves), 2)
            if white_moves
            else 0.0
        )
        self._acpl_black = (
            round(sum(m.loss for m in black_moves) / len(black_moves), 2)
            if black_moves
            else 0.0
        )

    async def get_acpl_for_color(self, color: chess.Color) -> float | None:
        """Return cached per-color ACPL. Triggers precompute_acpl if not yet done."""

        if self._acpl_white is None or self._acpl_black is None:
            await self.precompute_acpl()
        return self._acpl_white if color == chess.WHITE else self._acpl_black

    async def get_acpl(self) -> float:
        """Overall average centipawn loss (both sides combined)."""
        moves = await self.get_analysis()
        return round(sum(m.loss for m in moves) / len(moves), 2) if moves else 0.0

    @staticmethod
    def is_endgame(board: chess.Board) -> bool:
        pieces = board.piece_map()

        non_pawn = sum(1 for piece in pieces.values() if piece.piece_type != chess.PAWN)

        queens = sum(1 for piece in pieces.values() if piece.piece_type == chess.QUEEN)

        return queens == 0 or non_pawn <= 6

    def ends_in_endgame(self) -> bool:
        board = self.game.end().board()
        return self.is_endgame(board)
