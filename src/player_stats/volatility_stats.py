from dataclasses import dataclass, field

import numpy as np

import utils.math_stat as math_stats
from player import Player
from utils.Config import ConfigData


@dataclass
class VolatilityStats:
    player: Player

    _variances: list[float] | None = field(default=None)

    @property
    def variances(self) -> list[float] | None:
        if self._variances is not None:
            return self._variances
        volatilities_variances = []

        for game in self.player.iterate_games():
            if len(game.move_analysis) <= 2:
                continue
            volatilities = game.volatilities(self.player.which_color_is_player(game.game))

            volatilities_variances.append(np.var(volatilities))

        self._variances = volatilities_variances

        return self._variances

    @property
    def mean(self) -> float:
        return math_stats.mean(self.variances)

    def index(self) -> float:
        return self.mean // ConfigData.HARDCODED_VALUE_TO_MEASURE_VOLATILITY
