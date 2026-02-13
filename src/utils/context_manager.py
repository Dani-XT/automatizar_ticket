from contextlib import contextmanager
from time import perf_counter

@contextmanager
def timed(label: str):
    t0 = perf_counter()
    try:
        yield
    finally:
        dt = perf_counter() - t0
        print(f"⏱️ {label}: {dt:.3f}s")
