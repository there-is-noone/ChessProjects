from dataclasses import dataclass, field

import chess

import chessprograms.utils.math_stat as math_stats
from chessprograms.player import Player
from chessprograms.player_stats.winrate_stats import WinrateStats


@dataclass
class PerformanceStats:
    player: Player
    winrate: WinrateStats

    _score: float | None = field(default=None)

    @property
    def score(self) -> float | None:
        if not self._score:
            score = 0
            for game in self.player.iterate_games():
                score += self.player.did_player_win(game)
            self._score = score
        return self._score

    @property
    def mean_enemy_rating(self):
        enemy_elo = []
        for game in self.player.iterate_games():
            color = self.player.which_color_is_player(game.game)
            elo_key = "BlackElo" if color == chess.WHITE else "WhiteElo"
            elo_str = game.game.headers[elo_key]
            if elo_str and elo_str.strip().isdigit():
                enemy_elo.append(int(elo_str))
        return math_stats.mean(enemy_elo)

    @property
    def performance(self):
        return round(
            self.mean_enemy_rating + ((self.score / len(self.player.Games)) - 0.5) * 400, 2
        )
