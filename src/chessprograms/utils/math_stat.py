import numpy


def percentage(part: int, total: int, decimals: int = 2) -> float:
    return round((part / total) * 100, decimals) if total else 0.0


def mean(values: list[float | int] | None, decimals: int = 2) -> float:
    if values is not None:
        return round(sum(values) / len(values), decimals) if values else 0.0
    else:
        return 0.0
