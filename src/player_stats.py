from dataclasses import dataclass, field
from collections import defaultdict
from player import Player
import chess
import chess.pgn
import utils.math_stat as math_stats
import numpy


@dataclass
class PlayerStats:
    player: Player
    _winrate: float | None = field(default=None)
    _winrate_white: float | None = field(default=None)
    _winrate_black: float | None = field(default=None)
    _ending_winrate: float | None = field(default=None)
    _ending_rate: float | None = field(default=None)
    _short_game_likeness: float | None = field(default=None)
    _short_game_winrate: float | None = field(default=None)
    _acpl: list | None = field(default=None)
    _acpl_standard_deviation: float | None = field(default=None)
    _coefficient_of_variation: float | None = field(default=None)
    _winrate_per_eco: dict | None = field(default=None)

    @property
    def winrate_white(self) -> float:
        if self._winrate_white is None:
            result = 0
            count = 0
            for whitegame in self.player.GamesWhite:
                result += self.player.did_player_win(whitegame, chess.WHITE)
                count += 1
            self._winrate_white = math_stats.percentage(result, count) if count else 0
        return self._winrate_white

    @property
    def winrate_black(self) -> float:
        if self._winrate_black is None:
            result = 0
            count = 0
            for blackgame in self.player.GamesBlack:
                result += self.player.did_player_win(blackgame, chess.BLACK)
                count += 1
            self._winrate_black = math_stats.percentage(result, count) if count else 0
        return self._winrate_black

    @property
    def winrate(self) -> float | None:
        if self._winrate is None:
            count = 0
            total = 0

            for game, color in self.player._iterate_games():
                total += self.player.did_player_win(game, color) == 1.0
                count += 1
            self._winrate = math_stats.percentage(total, count) if count else 0
        return self._winrate

    @property
    def short_game_rate(self) -> float | None:
        if self._short_game_likeness is None:
            counter_short = 0
            counter = 0
            for game in self.player.Games:
                if game.how_many_moves() <= 25:
                    counter_short += 1
                counter += 1

            self._short_game_likeness = (
                math_stats.percentage(counter_short, counter) if counter else 0
            )
        return self._short_game_likeness

    @property
    def short_game_win_rate(self) -> float | None:
        if self._short_game_winrate is None:
            counter_short_wins = 0
            counter = 0
            for game, color in self.player._iterate_games():
                if game.how_many_moves() <= 25:
                    if self.player.did_player_win(game, color) == 1.0:
                        counter_short_wins += 1
                    counter += 1

            self._short_game_winrate = (
                math_stats.percentage(counter_short_wins, counter) if counter else 0
            )
        return self._short_game_winrate

    @property
    def endgame_rate(self) -> float | None:
        if self._ending_rate is None:
            counter_endgame = 0
            counter = 0
            for game in self.player.Games:
                if game.ends_in_endgame():
                    counter_endgame += 1
                counter += 1
            self._ending_rate = (
                math_stats.percentage(counter_endgame, counter) if counter else 0
            )
        return self._ending_rate

    @property
    def endgame_win_rate(self) -> float | None:
        if self._ending_winrate is None:
            counter = 0
            counter_endgame_wins = 0
            for game, color in self.player._iterate_games():
                if game.ends_in_endgame():
                    if self.player.did_player_win(game, color) == 1.0:
                        counter_endgame_wins += 1
                    counter += 1
            self._ending_winrate = (
                math_stats.percentage(counter_endgame_wins, counter) if counter else 0
            )
        return self._ending_winrate

    @property
    def winrate_per_eco(self):
        if self._winrate_per_eco is None:
            eco_data = defaultdict(
                lambda: {"wins": 0, "draw": 0, "loss": 0, "total": 0}
            )
            self._winrate_per_eco: dict[str, list[float]] = {}
            for game, color in self.player._iterate_games():
                eco_code = game.game.headers.get("ECO", "unknown")
                if self.player.did_player_win(game, color) == 1.0:
                    eco_data[eco_code]["wins"] += 1
                elif self.player.did_player_win(game, color) == 0.5:
                    eco_data[eco_code]["draw"] += 1
                else:
                    eco_data[eco_code]["loss"] += 1
                eco_data[eco_code]["total"] += 1

            self._winrate_per_eco = {
                eco: [
                    math_stats.percentage(stats["wins"], stats["total"]),
                    math_stats.percentage(stats["draw"], stats["total"]),
                    math_stats.percentage(stats["loss"], stats["total"]),
                ]
                for eco, stats in eco_data.items()
            }
        return self._winrate_per_eco

    @property
    def acpl_standard_deviation(self):
        acpl_for_dev = [acpl for acpl in self._acpl if acpl]
        return numpy.std(acpl_for_dev)

    async def get_acpl_list(self) -> list[float]:
        if self._acpl is None:
            self._acpl = []

            for game, color in self.player._iterate_games():
                acpl = await game.get_acpl_for_color(color)
                if acpl != 0:
                    self._acpl.append(acpl)
        return self._acpl

    @property
    def coefficient_of_variation(self):
        return self.acpl_standard_deviation / math_stats.mean(self._acpl)
