from dataclasses import dataclass
from utils.Config import ConfigData

@dataclass
class EngineStrategies:
    eval_every_n_moves: int = 1
    time_limit: float | None = None
    nodes: int | None = ConfigData.NODES
    evaluation_threshold: int = ConfigData.EVALUATION_LIMIT