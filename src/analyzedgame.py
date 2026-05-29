from dataclasses import dataclass
from engineanalyzer import EngineAnalyzer
import chess
from utils.moveanalysis import MoveAnalysis


@dataclass
class AnalyzedGame:
    game: chess.pgn.Game
    analyzer: EngineAnalyzer
    _move_analysis: list[MoveAnalysis]

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

    def get_analysis(self):
        if not self._move_analysis:
            self._move_analysis = self.analyzer.analyze_game(self.game)
        return self._move_analysis

    def get_acpl(self):
        moves = self.get_analysis()
        return round(sum(m.loss for m in moves) / len(moves), 2) if moves else 0

    @staticmethod
    def is_endgame(board: chess.Board) -> bool:
        pieces = board.piece_map()

        non_pawn = sum(1 for piece in pieces.values() if piece.piece_type != chess.PAWN)

        queens = sum(1 for piece in pieces.values() if piece.piece_type == chess.QUEEN)

        return queens == 0 or non_pawn <= 6

    def ends_in_endgame(self) -> bool:
        board = self.game.end().board()
        return self.is_endgame(board)
