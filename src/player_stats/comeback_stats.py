from dataclasses import dataclass

from player import Player


@dataclass
class ComebackStats:
    player: Player

    @property
    def comeback_rate(self) -> float:
        comebacks = 0
        total = 0

        for game in self.player.iterate_games():
            color = self.player.which_color_is_player(game.game)

            if color is None:
                continue

            if game.move_analysis is None or not game.move_analysis:
                continue

            if game.had_comeback(self.player, color):  # ← parametr gracza
                comebacks += 1
            total += 1

        return round((comebacks / total * 100), 2) if total > 0 else 0.0

    @property
    def lost_chances_rate(self) -> float:
        lost_chances = 0
        total = 0

        for game in self.player.iterate_games():
            color = self.player.which_color_is_player(game.game)

            if color is None:
                continue

            if game.move_analysis is None or not game.move_analysis:
                continue

            if game.had_advantage_and_lost(self.player, color):  # ← parametr gracza
                lost_chances += 1
            total += 1

        return round((lost_chances / total * 100), 2) if total > 0 else 0.0
