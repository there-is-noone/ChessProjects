from dataclasses import dataclass, field

import chess

import chessprograms.utils.math_stat as math_stats
from chessprograms.player import Player
from chessprograms.utils.Config import ConfigData


@dataclass
class WinrateStats:
    player: Player

    _winrate: float | None = field(default=None)

    _winrate_white: float | None = field(default=None)
    _winrate_black: float | None = field(default=None)

    _ending_rate: float | None = field(default=None)
    _ending_winrate: float | None = field(default=None)

    _short_game_likeness: float | None = field(default=None)
    _short_game_winrate: float | None = field(default=None)

    @property
    def winrate_white(self) -> float | None:
        """Returns the winrate only for the games played with white"""

        if self._winrate_white is None:
            result = 0
            count = 0
            for game in self.player.iterate_games():
                if self.player.which_color_is_player(game) == chess.WHITE:
                    result += self.player.did_player_win(game) == 1.0
                    count += 1
            self._winrate_white = math_stats.percentage(result, count) if count else 0
        return self._winrate_white

    @property
    def winrate_black(self) -> float | None:
        """Returns the winrate only for the games played with black"""

        if self._winrate_black is None:
            result = 0
            count = 0
            for game in self.player.iterate_games():
                if self.player.which_color_is_player(game) == chess.BLACK:
                    result += self.player.did_player_win(game) == 1.0
                    count += 1
            self._winrate_black = math_stats.percentage(result, count) if count else 0
        return self._winrate_black

    @property
    def winrate(self) -> float | None:
        if self._winrate is None:
            count = 0
            total = 0

            for game in self.player.iterate_games():
                total += self.player.did_player_win(game) == 1.0
                count += 1
            self._winrate = math_stats.percentage(total, count) if count else 0
        return self._winrate

    @property
    def short_game_rate(self) -> float | None:
        """Gathers how many games played were short game, under 25 moves"""
        if self._short_game_likeness is None:
            counter_short = 0
            counter = 0
            for game in self.player.iterate_games():
                if game.how_many_moves() <= ConfigData.SHORT_GAME_THRESHOLD:
                    counter_short += 1
                counter += 1

            self._short_game_likeness = (
                math_stats.percentage(counter_short, counter) if counter else 0
            )
        return self._short_game_likeness

    @property
    def short_game_win_rate(self) -> float | None:
        """Checks how many games of the short ones were actually won"""

        if self._short_game_winrate is None:
            counter_short_wins = 0
            counter = 0
            for game in self.player.iterate_games():
                if game.how_many_moves() <= ConfigData.SHORT_GAME_THRESHOLD:
                    if self.player.did_player_win(game) == 1.0:
                        counter_short_wins += 1
                    counter += 1

            self._short_game_winrate = (
                math_stats.percentage(counter_short_wins, counter) if counter else 0
            )
        return self._short_game_winrate

    @property
    def endgame_rate(self) -> float | None:
        """Checks how many games have moved to an endgame"""

        if self._ending_rate is None:
            counter_endgame = 0
            counter = 0
            for game in self.player.iterate_games():
                if game.ends_in_endgame():
                    counter_endgame += 1
                counter += 1
            self._ending_rate = math_stats.percentage(counter_endgame, counter) if counter else 0
        return self._ending_rate

    @property
    def endgame_win_rate(self) -> float | None:
        """Checks how many of the games that finished in an endgame phase were won"""

        if self._ending_winrate is None:
            counter = 0
            counter_endgame_wins = 0
            for game in self.player.iterate_games():
                if game.ends_in_endgame():
                    if self.player.did_player_win(game) == 1.0:
                        counter_endgame_wins += 1
                    counter += 1
            self._ending_winrate = (
                math_stats.percentage(counter_endgame_wins, counter) if counter else 0
            )
        return self._ending_winrate
