from dataclasses import dataclass

import chess

from chessprograms.player import Player


@dataclass
class PieceStats:
    player: Player

    @property
    def piece_type_distribution(self) -> dict[chess.PieceType, int]:
        distribution = {name: 0 for name in chess.PIECE_TYPES}
        for game in self.player.iterate_games():
            if game.move_analysis is None:
                continue
            for move_analysis in game.move_analysis:
                distribution[move_analysis.piece_type] += 1
        return distribution

    @property
    def piece_type_percentages(self) -> dict[chess.PieceType, float]:
        distribution = self.piece_type_distribution
        total = sum(distribution.values())
        if total == 0:
            return {k: 0.0 for k in distribution}

        return {k: round((v / total) * 100, 2) for k, v in distribution.items()}
