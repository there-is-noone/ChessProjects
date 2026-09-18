from dataclasses import dataclass
from enum import Enum

import chess

from chessprograms.utils.Config import ConfigData


class BlunderSeverity(Enum):
    NONE = 0
    INACCURACY = 1  # 50–100cp
    MISTAKE = 1.5  # 100–300cp
    BLUNDER = 2  # >300cp


@dataclass
class MoveAnalysis:
    move: chess.Move
    loss: float
    eval_before: int | None
    eval_after: int | None
    color: chess.Color
    piece_type: chess.PieceType
    development_advantage: float
    is_mobile: bool
    pressure_gain: int

    @property
    def severity(self) -> BlunderSeverity:

        if self.loss >= ConfigData.BLUNDER_THRESHOLD:
            return BlunderSeverity.BLUNDER

        elif self.loss >= ConfigData.MISTAKE_THRESHOLD:
            return BlunderSeverity.MISTAKE

        elif self.loss >= ConfigData.INACCURACY_THRESHOLD:
            return BlunderSeverity.INACCURACY

        else:
            return BlunderSeverity.NONE

    @property
    def volatility(self):
        if self.eval_before is not None and self.eval_after is not None:
            swing = abs(self.eval_after - self.eval_before)
            return min(swing, ConfigData.VOLATILITY_UPPER_BOUND)
        return self.eval_before if self.eval_before is not None else self.eval_after
