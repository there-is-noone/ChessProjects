"""
Tests for chessprograms.utils.math_stat

This is the easiest module in the project to start with because both
functions are "pure": given the same input they always return the same
output, and they don't touch the engine, the filesystem, or any other
class. No setup, no mocking, no fixtures needed.
"""

import pytest

from chessprograms.utils import math_stat


class TestPercentage:
    def test_typical_case(self):
        # 1 out of 4 is 25%
        assert math_stat.percentage(1, 4) == 25.0

    def test_zero_part(self):
        # 0 wins out of some games is 0%, not an error
        assert math_stat.percentage(0, 10) == 0.0

    def test_all_wins(self):
        assert math_stat.percentage(10, 10) == 100.0

    def test_total_zero_returns_zero_not_crash(self):
        # This is the whole reason the function has an `if total` guard:
        # dividing by zero games played should never raise ZeroDivisionError.
        assert math_stat.percentage(0, 0) == 0.0

    def test_rounding_uses_decimals_argument(self):
        # 1/3 = 33.333...%, default rounding is 2 decimals
        assert math_stat.percentage(1, 3) == 33.33

    def test_custom_decimals(self):
        assert math_stat.percentage(1, 3, decimals=0) == 33.0


class TestMean:
    def test_typical_case(self):
        assert math_stat.mean([1, 2, 3]) == 2.0

    def test_empty_list_returns_zero_not_crash(self):
        # Same idea as percentage(): an empty list of ACPL values (e.g. a
        # player with zero analyzed games) should not raise ZeroDivisionError.
        assert math_stat.mean([]) == 0.0

    def test_single_value(self):
        assert math_stat.mean([42.0]) == 42.0

    def test_rounding_uses_decimals_argument(self):
        assert math_stat.mean([1, 2], decimals=0) == 2.0

    def test_negative_values(self):
        # Not expected in real ACPL/eval data, but the function makes no
        # assumption about sign, so it should still work correctly.
        assert math_stat.mean([-1, 1]) == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])