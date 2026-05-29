import time


class Timer:
    def __init__(self, name="Timer"):
        self.name = name

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter()
        print(f"{self.name}: {(self.end - self.start):.4f}s")
