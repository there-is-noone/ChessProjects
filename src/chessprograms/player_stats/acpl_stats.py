import asyncio
from dataclasses import dataclass, field

import numpy as np

import chessprograms.utils.math_stat as math_stats
from chessprograms.player import Player


@dataclass
class AcplStats:
    player: Player

    _acpl: list | None = field(default=None)
    _acpl_standard_deviation: float | None = field(default=None)
    _coefficient_of_variation: float | None = field(default=None)

    _acpl_opening_list: list | None = field(default=None)
    _coefficient_of_variation_opening: float | None = field(default=None)

    _acpl_midgame_list: list | None = field(default=None)
    _coefficient_of_variation_midgame: float | None = field(default=None)

    _acpl_endgame_list: list | None = field(default=None)
    _coefficient_of_variation_endgame: float | None = field(default=None)

    async def acpl_game_stand_dev(self):
        """returns standard deviation for all of the games"""

        acpl = await self.get_acpl_list()
        if acpl:
            self._acpl_standard_deviation = self.compute_acpl_standard_deviation(acpl)
        return self._acpl_standard_deviation if self._acpl_standard_deviation else 0

    @property
    def acpl_opening_list(self) -> list[float]:
        """Gathers all of the acpl computed for the moves in the openings"""

        if self._acpl_opening_list is not None:
            return self._acpl_opening_list
        self._acpl_opening_list = []

        for game in self.player.Games:
            val = game.acpl_opening
            if val is not None:
                self._acpl_opening_list.append(val)

        return self._acpl_opening_list

    @staticmethod
    def compute_acpl_standard_deviation(values: list[float]) -> float:
        """Generic function that will always calculate the standard deviation of a given list"""

        values = [v for v in values if v is not None]

        if len(values) < 2:
            return 0.0

        return float(np.std(values, ddof=1))

    def acpl_opening_stand_dev(self):
        return self.compute_acpl_standard_deviation(self.acpl_opening_list)

    async def get_acpl_list(self) -> list[float] | None:
        """Compiles all of the game's acpl calculations into a list"""

        if self._acpl is None:
            self._acpl = []
            tasks = [game.calculate_acpl() for game in self.player.iterate_games()]

            results = await asyncio.gather(*tasks)

            self._acpl = [r for r in results if r is not None]
        return self._acpl

    def compute_coefficient_of_variation(self, values):
        """Generic function that will always calculate the coefficient of variation of a given list"""

        values = [v for v in values if v is not None]

        if len(values) < 2:
            return 0.0

        mean = math_stats.mean(values)
        if mean == 0:
            return 0.0

        return self.compute_acpl_standard_deviation(values) / mean

    async def coefficient_of_variation(self):
        """Calculate a coefficient of variation for all of the games"""

        acpl = await self.get_acpl_list()
        self._coefficient_of_variation = self.compute_coefficient_of_variation(acpl)
        return self._coefficient_of_variation

    @property
    def coefficient_of_variation_opening(self):
        """Calculate a coefficient of variation for game only in the opening"""

        return self.compute_coefficient_of_variation(self.acpl_opening_list)

    @property
    def acpl_endgame_list(self):
        if self._acpl_endgame_list is None:
            self._acpl_endgame_list = []
            for game in self.player.iterate_games():
                self._acpl_endgame_list.append(game.acpl_endgame)
        return self._acpl_endgame_list

    @property
    def coefficient_of_variation_endgame(self):
        if not self._coefficient_of_variation_endgame:
            self._coefficient_of_variation_endgame = self.compute_coefficient_of_variation(
                self.acpl_endgame_list
            )
        return self._coefficient_of_variation_endgame

    @property
    def acpl_midgame_list(self):
        if self._acpl_midgame_list is None:
            self._acpl_midgame_list = []
            for game in self.player.iterate_games():
                self._acpl_midgame_list.append(game.acpl_midgame)
        return self._acpl_midgame_list

    @property
    def coefficient_of_variation_midgame(self):
        if not self._coefficient_of_variation_midgame:
            self._coefficient_of_variation_midgame = self.compute_coefficient_of_variation(
                self.acpl_midgame_list
            )
        return self._coefficient_of_variation_midgame
