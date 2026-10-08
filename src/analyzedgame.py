import functools
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import chess.pgn

import enums
import utils.math_stat as math_stats
from engineanalyzer import EngineAnalyzer
from openings.ecocode import ECOCode
from utils import moveanalysis
from utils.Config import ConfigData
from utils.moveanalysis import MoveAnalysis

if TYPE_CHECKING:
    from player import Player


@dataclass(repr=False)
class AnalyzedGame:
    game: chess.pgn.Game
    analyzer: EngineAnalyzer
    player_color: chess.Color
    move_analysis: list[MoveAnalysis] = field(default_factory=list)

    _acpl_player: float | None = field(default=None)
    _acpl_opening: float | None = field(default=None)
    _acpl_endgame: float | None = field(default=None)
    _acpl_midgame: float | None = field(default=None)

    def get_result(self) -> str:
        return self.game.headers["Result"]

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
        if not self.move_analysis:
            self.move_analysis = await self.analyzer.analyze_game(self.game)
        return self.move_analysis

    async def calculate_acpl(self):
        """Computes the acpl for a game for each of the colors separately"""
        if self._acpl_player is not None:
            return self._acpl_player
        moves = await self.get_analysis()

        player_moves = [m for m in moves if m.color == self.player_color]
        self._acpl_player = math_stats.mean([m.loss for m in player_moves]) if player_moves else 0.0
        return self._acpl_player

    def is_endgame(self, board: chess.Board) -> bool:
        if self.is_opening(board):
            return False

        pieces = board.piece_map()

        non_pawn = sum(1 for piece in pieces.values() if piece.piece_type != chess.PAWN)

        queens = sum(1 for piece in pieces.values() if piece.piece_type == chess.QUEEN)

        return queens == 0 or non_pawn <= 6

    def ends_in_endgame(self) -> bool:
        """Checks if the game ends in an endgame"""

        board = self.game.end().board()
        return self.is_endgame(board)

    def is_opening(self, board: chess.Board) -> bool:
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

    @functools.cached_property
    def transition_opening_to_mid(self):
        """Finds the move that is the assumed breakpoint between the opening and middlegame"""

        board = chess.Board()
        for move in self.game.mainline_moves():
            board.push(move)

            if not self.is_opening(board):
                return board.ply()

        return board.ply()

    @property
    def opening_moves(self) -> list[chess.Move]:
        board = chess.Board()
        opening = []

        for move in self.game.mainline_moves():
            if not self.is_opening(board):
                break
            opening.append(move)
            board.push(move)

        return opening

    @property
    def opening_name(self) -> str | None:
        return self.game.headers.get("Opening", "Unknown")

    def _calculate_phase_acpl(self, start: int, end: int, cache_attr: str) -> float | None:
        cached = getattr(self, cache_attr)
        if cached is not None:
            return cached
        phase_moves = [
            m
            for i, m in enumerate(self.move_analysis)
            if start <= i < end and m.color == self.player_color
        ]

        res = math_stats.mean([m.loss for m in phase_moves]) if phase_moves else 0.0
        setattr(self, cache_attr, res)
        if res == 0:
            return None
        return res

    @property
    def acpl_opening(self):
        return self._calculate_phase_acpl(0, self.transition_opening_to_mid, "_acpl_opening")

    @property
    def acpl_midgame(self):
        return self._calculate_phase_acpl(
            self.transition_opening_to_mid, self.transition_mid_to_endgame, "_acpl_midgame"
        )

    @property
    def acpl_endgame(self):
        return self._calculate_phase_acpl(
            self.transition_mid_to_endgame, len(self.move_analysis), "_acpl_endgame"
        )

    @functools.cached_property
    def transition_mid_to_endgame(self):
        """Finds the move that is the assumed breakpoint between the opening and middlegame"""

        board = chess.Board()
        node = self.game
        while not node.is_end():
            node = node.variations[0]
            board.push(node.move)

            if self.is_endgame(board):
                return board.ply()
        return board.ply()

    @property
    def mistake_list(self):
        return [
            move
            for move in self.move_analysis
            if move.severity != moveanalysis.BlunderSeverity.NONE
            and move.color == self.player_color
        ]

    def mistake_severity_counter_per_phase(
        self, start: int = 0, end: int | None = None
    ) -> tuple[int, int]:
        if end is None:
            end = len(self.move_analysis)
        return sum(
            move.severity.value
            for move in (self.move_analysis[start:end])
            if move.color == self.player_color
        ), (end - start)

    @property
    def mistake_severity_opening(self):
        return self.mistake_severity_counter_per_phase(0, self.transition_opening_to_mid)

    @property
    def mistake_severity_midgame(self):
        return self.mistake_severity_counter_per_phase(
            self.transition_opening_to_mid, self.transition_mid_to_endgame
        )

    @property
    def mistake_severity_endgame(self):
        return self.mistake_severity_counter_per_phase(self.transition_mid_to_endgame)

    @property
    def blunder_count(self):
        return sum(
            move.severity == moveanalysis.BlunderSeverity.BLUNDER
            for move in self.mistake_list
            if move.color == self.player_color
        )

    def had_comeback(self, player: "Player", color: chess.Color, threshold: int = -200):
        if self.move_analysis is None or not self.move_analysis:
            return None
        evals_from_players_perspective = []
        for move in self.move_analysis:
            if color == chess.WHITE:
                evals_from_players_perspective.append(move.eval_after)
            else:
                evals_from_players_perspective.append(-move.eval_after)

        worst_eval = min(evals_from_players_perspective)
        was_in_trouble = worst_eval < threshold
        won = player.did_player_win(self) == 1.0
        return won and was_in_trouble

    def had_advantage_and_lost(self, player: "Player", color: chess.Color, threshold: int = 200):
        if self.move_analysis is None or not self.move_analysis:
            return None
        evals_from_players_perspective = []
        for move in self.move_analysis:
            if color == chess.WHITE:
                evals_from_players_perspective.append(move.eval_after)
            else:
                evals_from_players_perspective.append(-move.eval_after)

        best_eval = max(evals_from_players_perspective)
        was_winning = best_eval > threshold
        lost = player.did_player_win(self) == 0.0
        return lost and was_winning

    def which_color_developed_faster(self):
        move = self.transition_opening_to_mid - 2

        development_advantage_at_move = self.move_analysis[move].development_advantage

        if development_advantage_at_move > ConfigData.DEVELOPMENT_DIFFERENCE:
            return chess.WHITE
        elif development_advantage_at_move < -ConfigData.DEVELOPMENT_DIFFERENCE:
            return chess.BLACK
        else:
            return None

    def which_color_attacked(self):
        if self.transition_opening_to_mid is None:
            return None

        if self.move_analysis is None:
            return None
        move = min(self.game.end().ply(), self.transition_opening_to_mid + 1)

        if move < 2:
            return self.move_analysis[0].color

        prev = self.move_analysis[move - 2]
        curr = self.move_analysis[move - 1]

        if curr.pieces_offensive > prev.pieces_offensive:
            return curr.color
        elif curr.pieces_offensive < prev.pieces_offensive:
            return prev.color
        else:
            return None

    def volatilities(self, color):
        volatilities = []
        for move in self.move_analysis:
            if move.color == color:
                volatilities.append(move.volatility)
        return volatilities

    @property
    def forcing_moves(self):
        board = self.game.board()
        counter = 0
        counter_forcing = 0
        for move in self.move_analysis:
            if move.color == self.player_color:
                counter += 1
                if board.gives_check(move.move) or board.is_capture(move.move):
                    counter_forcing += 1
            board.push(move.move)
        return counter, counter_forcing

    @property
    def mobile_moves(self):
        counter = 0
        counter_mobile = 0
        for move in self.move_analysis:
            if move.color != self.player_color:
                continue
            if move.is_mobile:
                counter_mobile += 1
            counter += 1
        return counter, counter_mobile

    @property
    def pressure_gains_accumulation(self):
        accumulator = 0
        moves = 0
        for move in self.move_analysis:
            if move.color != self.player_color:
                continue
            accumulator += move.pressure_gain
            moves += 1
        return moves, accumulator

    @property
    def eco_code(self) -> ECOCode:
        return ECOCode(self.game.headers.get("ECO", "unknown"))


def serialize_game(analyzed: AnalyzedGame):
    """makes AnalyzedGame easier to pickle"""

    analysis = analyzed.move_analysis

    return {
        "headers": dict(analyzed.game.headers),
        "moves": [m.move.uci() for m in analysis],
        "moves": [m.move.uci() for m in analysis],
        "evals_before": [m.eval_before for m in analysis],
        "evals_after": [m.eval_after for m in analysis],
        "losses": [m.loss for m in analysis],
        "piece_types": [m.piece_type for m in analysis],
        "development": [m.development_advantage for m in analysis],
        "acpl_opening": analyzed.acpl_opening,
        "acpl_player": analyzed._acpl_player,
        "is_mobile": [m.is_mobile for m in analysis],
        "development_gains": [m.pressure_gain for m in analysis],
    }


def total_material(board: chess.Board, color: chess.Color | None = None) -> int:
    total = 0

    colors = [color] if color is not None else [chess.WHITE, chess.BLACK]

    for piece_color in colors:
        for piece_type, value in ConfigData.PIECE_VALUES.items():
            total += len(board.pieces(piece_type, piece_color)) * value

    return total


def material_diff(board: chess.Board, color: chess.Color) -> int:
    """Net material for `color` minus their opponent's."""
    return total_material(board, color) - total_material(board, not color)


def mobility(board: chess.Board, color: chess.Color):
    attacked = chess.SquareSet()

    for square, piece in board.piece_map().items():
        if piece.color == color:
            attacked |= board.attacks(square)

    return len(attacked)


def king_pressure(board: chess.Board, attacker: chess.Color) -> int:
    enemy = not attacker
    king_square = board.king(enemy)

    if king_square is None:
        print("no king")
        return 0

    pressure = 0

    king_zone = chess.SquareSet(chess.BB_KING_ATTACKS[king_square])

    for square in king_zone:
        for attacker_square in board.attackers(attacker, square):
            piece = board.piece_at(attacker_square)
            pressure += enums.PIECE_ATTACK_WEIGHTS[piece.piece_type]

    return pressure
