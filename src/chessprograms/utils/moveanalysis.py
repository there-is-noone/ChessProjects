from dataclasses import dataclass
from enum import Enum
import chess

from chessprograms.utils.Config import ConfigData


@dataclass
class MoveAnalysis:
    move: chess.Move
    loss: float
    eval_before: int | None
    eval_after: int | None
    color: chess.Color
    development_advantage: float
    # is_sacrifice: bool
    is_mobile: bool
    pressure_gain: int

    @property
    def is_blunder(self) -> bool:
        return self.loss >= ConfigData.BLUNDER_THRESHOLD

    @property
    def severity(self) -> BlunderSeverity:
        if self.loss >= ConfigData.INACCURACY_THRESHOLD:
            return BlunderSeverity.INACCURACY
        if self.loss >= ConfigData.MISTAKE_THRESHOLD:
            return BlunderSeverity.MISTAKE
        if self.loss >= ConfigData.BLUNDER_THRESHOLD:
            return BlunderSeverity.BLUNDER
        return BlunderSeverity.NONE

    @property
    def volatility(self):
        if self.eval_before is not None and self.eval_after is not None:
            swing = abs(self.eval_after - self.eval_before)
            return min(swing, ConfigData.VOLATILITY_UPPER_BOUND)
        return self.eval_before if self.eval_before is not None else self.eval_after


class BlunderSeverity(Enum):
    NONE = 0
    INACCURACY = 1  # 50–100cp
    MISTAKE = 2  # 100–300cp
    BLUNDER = 3  # >300cp
