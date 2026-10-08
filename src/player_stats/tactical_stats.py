from dataclasses import dataclass

import utils.math_stat as math_stats
from player import Player


@dataclass
class TacticalStats:
    player: Player

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

    @property
    def blunder_rate(self):
        return math_stats.percentage(
            sum(game.blunder_count for game in self.player.iterate_games()),
            sum(len(game.move_analysis) for game in self.player.iterate_games()),
        )

    @property
    def average_blunder_rate(self) -> float:
        blunder_sev = 0
        move_count = 0
        for game in self.player.iterate_games():
            curr_sev, curr_move = game.mistake_severity_counter_per_phase()
            blunder_sev += curr_sev
            move_count += curr_move
        return blunder_sev / move_count if move_count else 0.0

    @property
    def opening_mistake_rate(self) -> float:
        blunder_sev = 0
        move_count = 0
        for game in self.player.iterate_games():
            curr_sev, curr_move = game.mistake_severity_opening
            blunder_sev += curr_sev
            move_count += curr_move
        return blunder_sev / move_count if move_count else 0.0

    @property
    def midgame_mistake_rate(self) -> float:
        blunder_sev = 0
        move_count = 0
        for game in self.player.iterate_games():
            curr_sev, curr_move = game.mistake_severity_midgame
            blunder_sev += curr_sev
            move_count += curr_move
        return blunder_sev / move_count if move_count else 0.0

    @property
    def endgame_mistake_rate(self) -> float:
        blunder_sev = 0
        move_count = 0
        for game in self.player.iterate_games():
            curr_sev, curr_move = game.mistake_severity_endgame
            blunder_sev += curr_sev
            move_count += curr_move
        return blunder_sev / move_count if move_count else 0.0
