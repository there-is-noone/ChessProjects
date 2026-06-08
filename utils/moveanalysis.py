from dataclasses import dataclass
import chess


@dataclass
class MoveAnalysis:
    move: chess.Move
    loss: float
    eval_before: float
    eval_after: float
    color:chess.Color