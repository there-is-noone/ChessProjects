"""# parser for the chess games
Games = {}


class Cleangame:
    def __init__(self, headers, move_list):
        self.headers = headers
        self.move_list = move_list

    def show(self):
        return f"This is a game between: {self.headers['White']} and {self.headers['Black']} moves: {self.show_moves()}"

    def show_moves(self):
        movestring = ""
        for ply in self.move_list:
            movestring += ply.show()
        return movestring


class Move:
    def __init__(
        self,
        piece,
        moveFile,
        moveRank,
        colour,
        takes,
        checkmate,
        startFile,
        startRank,
        promoPiece,
    ):
        self.piece = piece
        self.moveFile = moveFile
        self.moveRank = moveRank
        self.colour = colour
        self.takes = takes
        self.checkmate = checkmate
        self.startFile = startFile
        self.startRank = startRank
        self.promoPiece = promoPiece

    def show(self):
        if not self.takes:
            return f"{self.colour} {self.piece} to {self.moveFile}{self.moveRank}. {self.checkmate}\n"
        return f"{self.colour} {self.piece} takes on {self.moveFile}{self.moveRank}. {self.checkmate}\n"


def createmove(move, movenr):
    takes = 0
    cleaning_move = move
    if "O-O-O" in move:
        piece = "castle queenside"
        cleaning_move, checkmate = CHECK_IF_CHECKMATE(move)
        if movenr % 2:
            colour = "White"
            startFile = "e"
            startRank = 1
        else:
            colour = "Black"
            startFile = "e"
            startRank = 8
        return Move(piece, "O-O-O", "", colour, 0, checkmate, startFile, startRank, "")
    elif "O-O" in move:
        piece = "castle kingside"
        cleaning_move, checkmate = CHECK_IF_CHECKMATE(move)
        if movenr % 2:
            colour = "White"
            startFile = "e"
            startRank = 1
        else:
            colour = "Black"
            startFile = "e"
            startRank = 8

        return Move(piece, "O-O", "", colour, 0, checkmate, startFile, startRank, "")
    cleaning_move, checkmate = CHECK_IF_CHECKMATE(cleaning_move)
    if "=" in cleaning_move:
        promoPiece = cleaning_move.split("=")[1]
        cleaning_move = cleaning_move.split("=")[0]
    else:
        promoPiece = ""
    if "x" in cleaning_move:
        takes = 1
        start = cleaning_move.split("x")[0]
        target = cleaning_move.split("x")[1]
    else:
        target = cleaning_move[-2:]
        start = cleaning_move[:-2]
    moveFile = target[-2]
    moveRank = target[-1]
    if not start or start[0].islower():
        piece = "pawn"
    else:
        if start[0] == "N":
            piece = "knight"
        elif start[0] == "B":
            piece = "bishop"
        elif start[0] == "R":
            piece = "rook"
        elif start[0] == "Q":
            piece = "queen"
        elif start[0] == "K":
            piece = "king"
        start = start[1:]
    # to turn into switch soon
    if len(start) == 2:
        startFile = start[0]
        startRank = start[1]
    elif len(start) == 1:
        if start.isnumeric():
            startRank = start
            startFile = ""
        else:
            startFile = start
            startRank = ""
    else:
        startFile = ""
        startRank = ""

    if movenr % 2:
        colour = "White"
    else:
        colour = "Black"
    return Move(
        piece,
        moveFile,
        moveRank,
        colour,
        takes,
        checkmate,
        startFile,
        startRank,
        promoPiece,
    )


def separate(notation: list) -> list:
    game = []
    for nr, move in enumerate(notation):
        game.append(createmove(move, nr + 1))
    return game


def parse_games():
    headers = {}
    gamestart = False
    moves = []
    count = 0
    PARSER_STATE = "READING_HEADERS"
    with open("/home/kkrec/chessgames/Berliner.pgn", "r") as file:
        for line in file:
            if PARSER_STATE == "READING_HEADERS":
                if not line.startswith("["):
                    PARSER_STATE = "READING_MOVES"
                else:
                    line = READ_HEADERS(line).split(" ", 1)
                    headers[line[0]] = line[1]
            elif PARSER_STATE == "READING_MOVES":
                line1 = line.split(" ")
                line1 = [a.replace("\n", "").split(".")[-1] for a in line1]
                #            print(line1)
                moves += line1
                if line == "\n":
                    gamestart = False
                    moves = [a for a in moves if a]
                    game = separate(moves[:-1])
                    Games[count] = Cleangame(headers.copy(), game)
                    moves = []
                    headers.clear()
                    count += 1
                    PARSER_STATE = "READING_HEADERS"
    for nr, game in Games.items():
        print(f"Game number {nr}\n{Games[nr].show()}")


def READ_HEADERS(line):
    return line.replace("[", "").replace("]", "").replace("\n", "")


def CHECK_IF_CHECKMATE(cleaning_move):
    if not cleaning_move:
        return cleaning_move, ""
    elif cleaning_move[-1] == "#":
        cleaning_move = cleaning_move[:-1]
        return cleaning_move, "Checkmate!"
    elif cleaning_move[-1] == "+":
        cleaning_move = cleaning_move[:-1]
        return cleaning_move, "Check!"
    else:
        return cleaning_move, ""


def get():
    pass


def main():
    pass


if __name__ == "__main__":
    parse_games()
"""


from parser_try2 import AnalyzedGame,Player
from stockfish import Stockfish
import chess.pgn
stockfish=Stockfish("/home/kkrec/stockfish/")

"""gameList = {}
with open(
        "/home/kkrec/chessgames/lichess_gracznumerx_2026-05-25.pgn", encoding="utf-8"
) as games:
    nr = 1
    while game := chess.pgn.read_game(games):
        gameList[nr] = AnalyzedGame(game)
        nr += 1
test_subject=Player("gracznumerx")
test_game=Player.Games[12]"""
print(stockfish.get_engine_parameters())