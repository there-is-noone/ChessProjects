from dataclasses import dataclass
import chess.pgn
import chess
from Enum import Color
from stockfish import Stockfish

@dataclass
class MoveAnalysis:
    def __init__(self,move,loss,eval_before,eval_after):
        self.move=move
        self.loss=loss
        self.eval_before=eval_before
        self.eval_after=eval_after

@dataclass
class EngineAnalyzer:
    engine:Stockfish
    def analyze_game(self, game):
        board=game.board()
        result=[]
        for move in game.mainline_moves():
            loss,eval_before,eval_after=self.analyze_move(board,move)
            result.append(MoveAnalysis(move,loss,eval_before,eval_after))
            board.push(move)
        return result




@dataclass
class AnalyzedGame:
    game:chess.pgn.Game
    _move_analysis:list
    engine:Stockfish
    def __init__(self, game,engine):
        self.game = game
        self._move_analysis = []
        self.engine=engine
    def get_result(self) -> str:
        return self.game.headers["Result"]

    def __str__(self):
        return self.game.headers

    def how_many_moves(self) -> int:
        return self.game.end().ply() // 2

    def find_ending_flag(self):
        board = self.game.end().board()
        outcome = board.outcome()

        if outcome:
            return outcome.termination.name.lower()

        return self.game.headers.get("Termination", "unknown").lower()
    def analyze_game(self):
        if not self._move_analysis:
            analyzing=EngineAnalyzer(self.engine)
            analyzing.analyze_game(game)


@dataclass
class Player:
    PlayerName: str
    GamesWhite: list[AnalyzedGame]
    GamesBlack: list[AnalyzedGame]
    Games: list[AnalyzedGame]

    def __init__(self, playername: str):
        self.GamesWhite = [
            game1
            for game1 in gameList.values()
            if game1.game.headers["White"] == playername
        ]
        self.GamesBlack = [
            game1
            for game1 in gameList.values()
            if game1.game.headers["Black"] == playername
        ]
        self.Games = self.GamesBlack + self.GamesWhite

    def __str__(self):
        result = ""
        for whitegame in self.GamesWhite:
            result += f"{whitegame.game.headers['White']} vs {whitegame.game.headers['Black']}:{whitegame.get_result()}\n"
        for blackgame in self.GamesBlack:
            result += f"{blackgame.game.headers['White']} vs {blackgame.game.headers['Black']}:{blackgame.get_result()}\n"
        return result

    def winrate_white(self):
        result = 0
        count = 0
        for whitegame in self.GamesWhite:
            result += self.did_player_win(whitegame, 1)
            count += 1
        return round((result / count * 100), 2)

    def winrate_black(self):
        result = 0
        count = 0
        for blackgame in self.GamesBlack:
            result += self.did_player_win(blackgame, 0)
            count += 1
        return round((result / count) * 100, 2)

    def winrate(self):
        result = 0
        count = 0
        for game in self.Games:
            result += self.did_player_win(game, 0)
            count += 1
        return round((result / count) * 100, 2)

    def did_player_win(self, game: AnalyzedGame, color: int) -> float | None:
        """Checks if the player that we're searching for won or lost
        returns:
        1.0 if won
        0.0 if lost
        0.5 for a draw"""

        if game.get_result() == "1-0":
            return 1.0 if Color.WHITE else 0.0
        elif game.get_result() == "0-1":
            return 0.0 if Color.WHITE else 1.0
        else:
            return 0.5

    def short_game_rate(self):
        counter_short = 0
        counter = 1
        for games in self.GamesWhite + self.GamesBlack:
            if games.how_many_moves() <= 25:
                counter_short += 1
            counter += 1

        return round((counter_short / counter) * 100, 2)

    def short_game_win_rate(self):
        counter_short_wins = 0
        counter = 0
        for games in self.GamesWhite:
            if games.how_many_moves() <= 25 and self.did_player_win(games, 1):
                counter_short_wins += 1
            counter += 1

        for games in self.GamesBlack:
            if games.how_many_moves() <= 25 and self.did_player_win(games, 0):
                counter_short_wins += 1
            counter += 1

        return round((counter_short_wins / counter) * 100, 2)


if __name__ == "__main__":
    stockfish = Stockfish("/home/kkrec/stockfish/stockfish-ubuntu-x86-64-avx2")
    gameList = {}
    with open(
        "/home/kkrec/chessgames/lichess_gracznumerx_2026-05-25.pgn", encoding="utf-8"
    ) as games:
        nr = 1
        while game := chess.pgn.read_game(games):
            gameList[nr] = AnalyzedGame(game,stockfish)
            nr += 1
    test = Player("gracznumerx")
    print(test)
    print(test.winrate_white())
    print(test.winrate_black())
    print(test.winrate())
    print(test.short_game_rate())
    print(test.short_game_win_rate())
    print(test.GamesBlack[13].find_ending_flag())
    stockfish.send_quit_command()