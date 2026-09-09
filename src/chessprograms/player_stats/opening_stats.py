from collections import defaultdict
from dataclasses import dataclass, field

import chessprograms.utils.math_stat as math_stats
from chessprograms.openings.ecocode import ECOCode
from chessprograms.player import Player
from chessprograms.utils.Config import ConfigData


@dataclass
class OpeningData:
    opening_name: str = "Unknown"
    amount_of_games: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0

    @property
    def winrate(self):
        return math_stats.percentage(self.wins, self.amount_of_games)

    @property
    def lossrate(self):
        return math_stats.percentage(self.losses, self.amount_of_games)

    @property
    def drawrate(self):
        return math_stats.percentage(self.draws, self.amount_of_games)


@dataclass
class OpeningStats:
    player: Player

    _stats_per_eco: dict[ECOCode, OpeningData] | None = field(default=None)
    _winrate_per_eco: dict | None = field(default=None)
    _total_games: int = 0

    @property
    def stats_per_eco(self):
        if self._stats_per_eco is not None:
            return self._stats_per_eco

        eco_data = defaultdict(OpeningData)
        for game in self.player.iterate_games():
            eco_code = game.eco_code

            if eco_data[eco_code].opening_name == "Unknown":
                eco_data[eco_code].opening_name = game.opening_name

            eco_data[eco_code].amount_of_games += 1
            self._total_games += 1

            if self.player.did_player_win(game) == 1.0:
                eco_data[eco_code].wins += 1
            elif self.player.did_player_win(game) == 0.5:
                eco_data[eco_code].draws += 1
            else:
                eco_data[eco_code].losses += 1

        self._stats_per_eco = eco_data
        return self._stats_per_eco

    @property
    def winrate_per_eco(self):
        """Gives full knowledge about winrate
        dependent on the opening chosen by the players"""

        if self._winrate_per_eco is not None:
            return self._winrate_per_eco
        eco_data = self.stats_per_eco
        self._winrate_per_eco: dict[str, list[float]] = {}

        self._winrate_per_eco = {
            eco: [stats.winrate, stats.drawrate, stats.lossrate] for eco, stats in eco_data.items()
        }
        return self._winrate_per_eco

    @property
    def three_best_performing_openings(self):
        candidates = [
            (eco, stats)
            for eco, stats in self.stats_per_eco.items()
            if eco != "Unknown"
            and stats.amount_of_games > ConfigData.MINIMUM_GAMES_FOR_VALID_WINRATE
        ]
        sorted_candidates = sorted(candidates, key=lambda item: item[1].winrate, reverse=True)
        return [res.opening_name for _, res in sorted_candidates[:3]]
