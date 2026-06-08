from dataclasses import dataclass
from utils.Config import ConfigData

STRATEGIES = {}


@dataclass(frozen=True)
class EngineStrategies:
    name: str
    eval_every_n_moves: int = 1
    time_limit: float | None = None
    nodes: int | None = ConfigData.NODES
    evaluation_threshold: int = ConfigData.EVALUATION_LIMIT

    def __post_init__(self):
        STRATEGIES[self.name] = self


ACPL_FAST = EngineStrategies(
    name="acpl_fast", eval_every_n_moves=2, evaluation_threshold=500
)

ACPL_DEEP = EngineStrategies(
    name="acpl_deep", eval_every_n_moves=1, evaluation_threshold=300
)

BLUNDER_SEARCH = EngineStrategies(
    name="blunder_search", time_limit=0.01, evaluation_threshold=200
)
