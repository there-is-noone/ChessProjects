from dataclasses import dataclass, field
from collections import defaultdict
from player import Player
import chess
import chess.pgn



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
    _acpl:list | None = field(default=None)
    _winrate_per_eco:dict | None=field(default=None)


    @property
    def winrate_white(self) -> float:
        if self._winrate_white is None:
            result = 0
            count = 0
            for whitegame in self.player.GamesWhite:
                result += self.player.did_player_win(whitegame, chess.WHITE)
                count += 1
            self._winrate_white = round((result / count * 100), 2) if count else 0
        return self._winrate_white

    @property
    def winrate_black(self) -> float:
        if self._winrate_black is None:
            result = 0
            count = 0
            for blackgame in self.player.GamesBlack:
                result += self.player.did_player_win(blackgame, chess.BLACK)
                count += 1
            self._winrate_black = round((result / count) * 100, 2) if count else 0
        return self._winrate_black

    @property
    def winrate(self) -> float | None:
        if self._winrate is None:
            count = 0
            total = 0

            for game, color in self.player._iterate_games():
                total += self.player.did_player_win(game, color) == 1.0
                count += 1
            self._winrate = round((total / count) * 100, 2) if count else 0
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
                round((counter_short / counter) * 100, 2) if counter else 0
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
                round((counter_short_wins / counter) * 100, 2) if counter else 0
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
                round((counter_endgame / counter) * 100, 2) if counter else 0
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
                round((counter_endgame_wins / counter) * 100, 2) if counter else 0
            )
        return self._ending_winrate

    @property
    def winrate_per_eco(self):
        if self._winrate_per_eco is None:
            eco_data = defaultdict(lambda: {"wins": 0,"draw": 0,"loss":0, "total": 0})
            self._winrate_per_eco: dict[str,list[float]]={}
            for game,color in self.player._iterate_games():
                eco_code=game.game.headers.get("ECO","unknown")
                if self.player.did_player_win(game,color)==1.0:
                    eco_data[eco_code]["wins"]+=1
                elif self.player.did_player_win(game,color)==0.5:
                    eco_data[eco_code]["draw"]+=1
                else:
                    eco_data[eco_code]["loss"]+=1
                eco_data[eco_code]["total"]+=1


            self._winrate_per_eco={
                eco : [round((stats["wins"]/stats["total"]) *100, 2),round((stats["draw"]/stats["total"]) *100, 2),round((stats["loss"]/stats["total"]) *100, 2)]
                for eco,stats in eco_data.items()
            }
        return self._winrate_per_eco

    async def get_acpl_list(self) -> list[float]:
        if self._acpl is None:
            self._acpl = []

            for game, color in self.player._iterate_games():
                acpl=await game.get_acpl_for_color(color)
                self._acpl.append(acpl)
        return self._acpl