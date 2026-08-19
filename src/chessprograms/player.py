from dataclasses import dataclass, field

import chess

from chessprograms.analyzedgame import AnalyzedGame


@dataclass
class Player:
    PlayerName: str
    GamesWhite: list[AnalyzedGame] = field(default_factory=list)
    GamesBlack: list[AnalyzedGame] = field(default_factory=list)
    Games: list[AnalyzedGame] = field(default_factory=list)

    def iterate_games(self):
        for game in self.Games:
            yield game

    def add_game(self, game: AnalyzedGame):
        if game._move_analysis is None:
            return
        if len(game._move_analysis) >= 2:
            self.Games.append(game)

    def __str__(self):
        result = ""
        for game in self.Games:
            result += f"{game.game.headers['White']} vs {game.game.headers['Black']}:{game.get_result()}\n"
        return result

    def which_color_is_player(self, game: AnalyzedGame):
        if game.game.headers["White"] == self.PlayerName:
            return chess.WHITE
        elif game.game.headers["Black"] == self.PlayerName:
            return chess.BLACK
        else:
            return None

    def did_player_win(self, game: AnalyzedGame) -> float:
        """Checks if the player that we're searching for won or lost
        returns:
        1.0 if won
        0.0 if lost
        0.5 for a draw"""

        color = self.which_color_is_player(game)

        if game.get_result() == "1-0":
            return 1.0 if color == chess.WHITE else 0.0
        elif game.get_result() == "0-1":
            return 0.0 if color == chess.WHITE else 1.0
        else:
            return 0.5
