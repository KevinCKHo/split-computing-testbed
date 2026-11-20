"""Timing helpers: host monotonic clock and CUDA events."""
from __future__ import annotations

import time
from contextlib import contextmanager

import torch


def now_ns() -> int:
    return time.perf_counter_ns()


@contextmanager
def host_timer(out: dict, key: str):
    t0 = time.perf_counter_ns()
    yield
    out[key] = (time.perf_counter_ns() - t0) / 1e6  # ms


def cuda_time_ms(fn, *args):
    """Run fn on GPU and return (result, elapsed ms) measured with CUDA events."""
    start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
    start.record()
    out = fn(*args)
    end.record()
    torch.cuda.synchronize()
    return out, start.elapsed_time(end)
