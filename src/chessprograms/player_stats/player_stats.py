from dataclasses import dataclass, field

from chessprograms.openings.openingbook import OpeningBook
from chessprograms.player import Player
from chessprograms.player_stats.acpl_stats import AcplStats
from chessprograms.player_stats.comeback_stats import ComebackStats
from chessprograms.player_stats.development_stats import DevelopmentStats
from chessprograms.player_stats.opening_stats import OpeningStats
from chessprograms.player_stats.performance_stats import PerformanceStats
from chessprograms.player_stats.piece_stats import PieceStats
from chessprograms.player_stats.tactical_stats import TacticalStats
from chessprograms.player_stats.volatility_stats import VolatilityStats
from chessprograms.player_stats.winrate_stats import WinrateStats


@dataclass
class PlayerStats:
    player: Player

    opening_stats: OpeningStats = field(init=False)
    acpl_stats: AcplStats = field(init=False)
    winrate_stats: WinrateStats = field(init=False)
    comeback_stats: ComebackStats = field(init=False)
    development_stats: DevelopmentStats = field(init=False)
    performance_stats: PerformanceStats = field(init=False)
    piece_stats: PieceStats = field(init=False)
    tactical_stats: TacticalStats = field(init=False)
    volatility_stats: VolatilityStats = field(init=False)

    def __post_init__(self):
        self.opening_stats = OpeningStats(self.player)
        self.acpl_stats = AcplStats(self.player)
        self.winrate_stats = WinrateStats(self.player)
        self.comeback_stats = ComebackStats(self.player)
        self.development_stats = DevelopmentStats(self.player)
        self.performance_stats = PerformanceStats(self.player, self.winrate_stats)
        self.piece_stats = PieceStats(self.player)
        self.tactical_stats = TacticalStats(self.player)
        self.volatility_stats = VolatilityStats(self.player)
