from dataclasses import dataclass, field

import chess
from chessprograms.analyzedgame import AnalyzedGame


@dataclass
class Player:
    PlayerName: str
    GamesWhite: list[AnalyzedGame] = field(default_factory=list)
    GamesBlack: list[AnalyzedGame] = field(default_factory=list)
    Games: list[AnalyzedGame] = field(default_factory=list)

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

    @staticmethod
    def did_player_win(game: AnalyzedGame, color: chess.Color) -> float:
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
