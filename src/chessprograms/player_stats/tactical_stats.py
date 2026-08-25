from dataclasses import dataclass

import chessprograms.utils.math_stat as math_stats
from chessprograms.player import Player


@dataclass
class TacticalStats:
    player: Player

    def sacrifice_percentage(self):
        counter = 0
        counter_sacrificed = 0
        for game in self.player.iterate_games():
            if game.has_a_sacrifice:
                counter_sacrificed += 1
            counter += 1
        print(counter)
        print(counter_sacrificed)
        return math_stats.percentage(counter_sacrificed, counter)

    @property
    def percentage_of_forcing_moves(self):
        total_counter, total_counter_forcing = 0, 0
        for game in self.player.iterate_games():
            games_counter, games_counter_forcing = game.forcing_moves
            total_counter += games_counter
            total_counter_forcing += games_counter_forcing
        return math_stats.percentage(total_counter_forcing, total_counter)

    @property
    def percentage_of_mobile_moves(self):
        total_counter, total_counter_mobile = 0, 0
        for game in self.player.iterate_games():
            games_counter, games_counter_mobile = game.mobile_moves
            total_counter += games_counter
            total_counter_mobile += games_counter_mobile
        return math_stats.percentage(total_counter_mobile, total_counter)
