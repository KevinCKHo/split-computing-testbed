"""Length-prefixed binary framing for tensors over TCP (no pickle).

Frame = 4-byte magic | 4-byte header length | JSON header | payload bytes.
Header: {"req", "dtype", "shape", "nbytes", "t_send_ns", plus optional meta such as "split"}.
"""
from __future__ import annotations

import json
import socket
import struct

import numpy as np

MAGIC = b"SPLT"
_HDR = struct.Struct("!4sI")


def encode(req: int, arr: np.ndarray, t_send_ns: int = 0, meta: dict | None = None) -> bytes:
    arr = np.ascontiguousarray(arr)
    header = json.dumps({"req": req, "dtype": str(arr.dtype), "shape": list(arr.shape),
                         "nbytes": arr.nbytes, "t_send_ns": t_send_ns, **(meta or {})}).encode()
    return _HDR.pack(MAGIC, len(header)) + header + arr.tobytes()


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray(n)
    view = memoryview(buf)
    got = 0
    while got < n:
        k = sock.recv_into(view[got:], n - got)
        if k == 0:
            raise ConnectionError("peer closed connection")
        got += k
    return bytes(buf)


def recv_frame(sock: socket.socket) -> tuple[dict, np.ndarray]:
    magic, hlen = _HDR.unpack(_recv_exact(sock, _HDR.size))
    if magic != MAGIC:
        raise ValueError("bad frame magic")
    header = json.loads(_recv_exact(sock, hlen))
    payload = _recv_exact(sock, header["nbytes"])
    arr = np.frombuffer(payload, dtype=header["dtype"]).reshape(header["shape"])
    return header, arr


def send_frame(sock: socket.socket, req: int, arr: np.ndarray, t_send_ns: int = 0,
               meta: dict | None = None) -> int:
    data = encode(req, arr, t_send_ns, meta)
    sock.sendall(data)
    return len(data)
