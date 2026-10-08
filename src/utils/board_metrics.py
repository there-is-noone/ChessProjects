import chess

import enums
from utils.Config import ConfigData


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
