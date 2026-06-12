from dataclasses import dataclass, field
import csv
import pickle
from io import StringIO
import chess.pgn


@dataclass
class OpeningNode:
    children: dict = field(default_factory=dict)
    opening: str = ""


@dataclass
class OpeningBook:
    trie: OpeningNode
    epd_map: dict

    def save(self, path="opening_book.pkl"):
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path="opening_book.pkl"):
        with open(path, "rb") as f:
            return pickle.load(f)

    @classmethod
    def build_trie(cls):
        root = OpeningNode()
        epd_map = {}
        for x in "abcde":
            for opening in load_games(f"../openings/base/{x}.tsv"):
                node = root
                pgn_text = opening.get("pgn")
                game = chess.pgn.read_game(StringIO(pgn_text))
                if game is None:
                    continue
                board = game.board()
                node = root
                for move in game.mainline_moves():
                    node = node.children.setdefault(move, OpeningNode())
                    board.push(move)
                node.opening = opening.get("name", "")
                epd_map[board.fen()] = opening

        return cls(root, epd_map)


def load_games(path):
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            yield row
