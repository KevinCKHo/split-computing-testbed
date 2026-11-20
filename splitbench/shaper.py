"""App-level link emulation, used where Linux tc/netem is not available (Windows).

LinkShaper wraps the client's send and receive:
  uplink:   wait delay_ms (propagation), then pace the bytes at rate_mbit (token bucket)
  downlink: after the reply arrives, wait delay_ms (propagation)
so one request/response pays RTT = 2 x delay_ms plus bytes*8/rate on the uplink.

It is deterministic and identical on every OS, which makes the compute vs. transfer
trade-off reproducible. It does NOT emulate packet-level effects (router queues,
cwnd growth, retransmissions); for those use the OS rate limit (scripts/win_qos.ps1)
or Linux tc (scripts/netem.sh) and set rate_mbit to 0 here.
"""
from __future__ import annotations

import socket
import time

_SPIN_NS = 2_000_000  # finish the last 2 ms of each wait by spinning: sleep() alone is ~1 ms coarse on Windows


def precise_sleep_until(t_ns: int) -> None:
    while True:
        left = t_ns - time.perf_counter_ns()
        if left <= 0:
            return
        if left > _SPIN_NS:
            time.sleep((left - _SPIN_NS) / 1e9)


class LinkShaper:
    def __init__(self, rate_mbit: float = 0.0, delay_ms: float = 0.0):
        self.rate_bps = rate_mbit * 1e6
        self.delay_ns = int(delay_ms * 1e6)
        # chunk ~ 1 ms of data at the shaped rate, at least one MSS
        self.chunk = max(1460, int(self.rate_bps / 8 / 1000)) if self.rate_bps else 0

    @property
    def active(self) -> bool:
        return bool(self.rate_bps or self.delay_ns)

    def send(self, sock: socket.socket, data: bytes) -> None:
        if self.delay_ns:
            precise_sleep_until(time.perf_counter_ns() + self.delay_ns)
        if not self.rate_bps:
            sock.sendall(data)
            return
        view = memoryview(data)
        t0 = time.perf_counter_ns()
        sent = 0
        while sent < len(view):
            end = min(sent + self.chunk, len(view))
            sock.sendall(view[sent:end])
            sent = end
            precise_sleep_until(t0 + int(sent * 8 / self.rate_bps * 1e9))

    def after_receive(self) -> None:
        if self.delay_ns:
            precise_sleep_until(time.perf_counter_ns() + self.delay_ns)
