from dataclasses import dataclass
from analyzedgame import AnalyzedGame


@dataclass
class Player:
    PlayerName: str
    GamesWhite: list[AnalyzedGame]
    GamesBlack: list[AnalyzedGame]
    Games: list[AnalyzedGame]

    def _iterate_games(self):
        for game in self.GamesWhite:
            yield game, True
        for game in self.GamesBlack:
            yield game, False

    def add_game(self, game: AnalyzedGame):
        self.Games.append(game)

        if game.game.headers["White"] == self.PlayerName:
            self.GamesWhite.append(game)

        elif game.game.headers["Black"] == self.PlayerName:
            self.GamesBlack.append(game)

    def __str__(self):
        result = ""
        for whitegame in self.GamesWhite:
            result += f"{whitegame.game.headers['White']} vs {whitegame.game.headers['Black']}:{whitegame.get_result()}\n"
        for blackgame in self.GamesBlack:
            result += f"{blackgame.game.headers['White']} vs {blackgame.game.headers['Black']}:{blackgame.get_result()}\n"
        return result

    def winrate_white(self) -> float:
        result = 0
        count = 0
        for whitegame in self.GamesWhite:
            result += self.did_player_win(whitegame, 1)
            count += 1
        return round((result / count * 100), 2) if count else 0

    def winrate_black(self) -> float:
        result = 0
        count = 0
        for blackgame in self.GamesBlack:
            result += self.did_player_win(blackgame, 0)
            count += 1
        return round((result / count) * 100, 2) if count else 0

    def winrate(self) -> float:
        count = 0
        total = 0

        for game, color in self._iterate_games():
            total += self.did_player_win(game, color) == 1.0
            count += 1
        return round((total / count) * 100, 2) if count else 0

    def did_player_win(self, game: AnalyzedGame, color: bool) -> float | None:
        """Checks if the player that we're searching for won or lost
        returns:
        1.0 if won
        0.0 if lost
        0.5 for a draw"""

        if game.get_result() == "1-0":
            return 1.0 if color else 0.0
        elif game.get_result() == "0-1":
            return 0.0 if color else 1.0
        else:
            return 0.5

    def short_game_rate(self) -> float:
        counter_short = 0
        counter = 0
        for game in self.Games:
            if game.how_many_moves() <= 25:
                counter_short += 1
            counter += 1

        return round((counter_short / counter) * 100, 2) if counter else 0

    def short_game_win_rate(self) -> float:
        counter_short_wins = 0
        counter = 0
        for game, color in self._iterate_games():
            if game.how_many_moves() <= 25:
                if self.did_player_win(game, color) == 1.0:
                    counter_short_wins += 1
                counter += 1

        return round((counter_short_wins / counter) * 100, 2) if counter else 0

    def endgame_rate(self) -> float:
        counter_endgame = 0
        counter = 0
        for game in self.Games:
            if game.ends_in_endgame():
                counter_endgame += 1
            counter += 1
        return round((counter_endgame / counter) * 100, 2) if counter else 0

    def endgame_win_rate(self) -> float:
        counter = 0
        counter_endgame_wins = 0
        for game, color in self._iterate_games():
            if game.ends_in_endgame():
                if self.did_player_win(game, color) == 1.0:
                    counter_endgame_wins += 1
                counter += 1
        return round((counter_endgame_wins / counter) * 100, 2) if counter else 0
