from dataclasses import dataclass
import chess
from utils.Config import ConfigData


@dataclass
class MoveAnalysis:
    move: chess.Move
    loss: float
    eval_before: float
    eval_after: float
    color: chess.Color

    @property
    def is_blunder(self) -> bool:
        return self.loss >= ConfigData.BLUNDER_THRESHOLD
