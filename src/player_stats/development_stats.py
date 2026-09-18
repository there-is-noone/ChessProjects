from dataclasses import dataclass

import utils.math_stat as math_stats
from player import Player


@dataclass
class DevelopmentStats:
    player: Player

    @property
    def mean_of_development_gains(self):
        accumulator = 0
        moves = 0
        for game in self.player.iterate_games():
            change_moves, change_accumulator = game.pressure_gains_accumulation
            accumulator += change_accumulator
            moves += change_moves
        return round(accumulator / moves, 2) if moves != 0 else 0

    @property
    def development_advantage_percentage(self):
        counter = 0
        counter_faster = 0
        for game in self.player.iterate_games():
            if game.which_color_developed_faster() == self.player.which_color_is_player(game.game):
                counter_faster += 1
            if game.which_color_developed_faster() is not None:
                counter += 1
        return math_stats.percentage(counter_faster, counter)
