from dataclasses import dataclass, field
import csv
import pickle
from io import StringIO
from typing import Iterable
from utils.Config import ConfigData
import chess.pgn


@dataclass
class OpeningNode:
    children: dict = field(default_factory=dict)
    opening: str = ""


@dataclass
class OpeningBook:
    trie: OpeningNode
    epd_map: dict


    def save(self, path=ConfigData.OPENING_BOOK_PATH):
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path=ConfigData.OPENING_BOOK_PATH):
        with open(path, "rb") as f:
            return pickle.load(f)

    @classmethod
    def build_trie(cls):
        root = OpeningNode()
        epd_map = {}
        for x in "abcde":
            for opening in load_games(f"../openings/base/{x}.tsv"):
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
                epd_map[board.epd()] = opening
        return cls(root, epd_map)


    def get_opening_from_position(self, board: chess.Board) -> str | None:
        """O(1) lookup by board position. Best when you already have a board."""
        entry = self.epd_map.get(board.epd())  # epd() strips move counters — more reliable than fen()
        return entry.get("name") if entry else None

    def get_opening_from_moves(self, moves: Iterable[chess.Move]) -> str | None:
        """Walk the trie, return the deepest named node. Best when replaying a game."""
        node = self.trie
        last_named = ""
        for move in moves:
            if move not in node.children:
                break
            node = node.children[move]
            if node.opening:
                last_named = node.opening
        return last_named or None

def load_games(path):
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            yield row

games=OpeningBook.build_trie()
games.save()