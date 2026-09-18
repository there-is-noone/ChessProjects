import re
from typing import Self


class ECOCode(str):
    """Type-safe ECO code."""

    def __new__(cls, value: str) -> Self:
        if not isinstance(value, str) or not re.match(r"^[A-E]\d{2}$", value):
            return super().__new__(cls, "Unknown")
        return super().__new__(cls, value)
