from dataclasses import dataclass
from player import Player
import chess
import chess.pgn


@dataclass
class PlayerStats:
    player: Player
    _winrate: float
    _winrate_white: float
    _winrate_black: float
    _ending_winrate: float
    _ending_rate: float
    _short_game_likeness: float
    _short_game_winrate: float

    @property
    def winrate_white(self) -> float:
        result = 0
        count = 0
        for whitegame in self.player.GamesWhite:
            result += self.player.did_player_win(whitegame, chess.WHITE)
            count += 1
        return round((result / count * 100), 2) if count else 0

    @property
    def winrate_black(self) -> float:
        result = 0
        count = 0
        for blackgame in self.player.GamesBlack:
            result += self.player.did_player_win(blackgame, chess.BLACK)
            count += 1
        return round((result / count) * 100, 2) if count else 0

    @property
    def winrate(self) -> float | None:
        if self._winrate is None:
            count = 0
            total = 0

            for game, color in self.player._iterate_games():
                total += self.player.did_player_win(game, color) == 1.0
                count += 1
            return round((total / count) * 100, 2) if count else 0
        return None

    @property
    def short_game_rate(self) -> float | None:
        if self._short_game_likeness is None:
            counter_short = 0
            counter = 0
            for game in self.player.Games:
                if game.how_many_moves() <= 25:
                    counter_short += 1
                counter += 1

            return round((counter_short / counter) * 100, 2) if counter else 0

        return None

    @property
    def short_game_win_rate(self) -> float | None:
        if self._short_game_winrate is None:
            counter_short_wins = 0
            counter = 0
            for game, color in self.player._iterate_games():
                if game.how_many_moves() <= 25:
                    if self.did_player_win(game, color) == 1.0:
                        counter_short_wins += 1
                    counter += 1

            return round((counter_short_wins / counter) * 100, 2) if counter else 0
        return None

    @property
    def endgame_rate(self) -> float | None:
        if self._ending_rate is None:
            counter_endgame = 0
            counter = 0
            for game in self.player.Games:
                if game.ends_in_endgame():
                    counter_endgame += 1
                counter += 1
            return round((counter_endgame / counter) * 100, 2) if counter else 0
        return None

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
            return round((counter_endgame_wins / counter) * 100, 2) if counter else 0
        return None
