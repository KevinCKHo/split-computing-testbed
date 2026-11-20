"""Inference server (RTX 4060 laptop). Runs on Windows or Linux: standard-library sockets only.

Receives either a raw uint8 frame (full offload) or an intermediate activation
(split), runs the remaining layers on the GPU, and returns top-5 class ids plus
its own timings.

    python -m splitbench.server --host 0.0.0.0 --port 50051
"""
from __future__ import annotations

import argparse
import socket

import numpy as np
import torch

from . import protocol
from .model import load_backbone, split_model
from .preprocess import normalize
from .timing import cuda_time_ms, now_ns


class Server:
    def __init__(self, model_name: str, pretrained: bool, device: str):
        self.device = device
        self.model = load_backbone(model_name, pretrained).to(device)
        self._parts: dict[str | None, torch.nn.Module] = {}

    def part(self, split: str | None) -> torch.nn.Module:
        if split not in self._parts:
            self._parts[split] = split_model(self.model, split)[1].to(self.device)
        return self._parts[split]

    @torch.inference_mode()
    def handle(self, header: dict, arr: np.ndarray) -> tuple[np.ndarray, dict]:
        t_recv = now_ns()
        split = header.get("split")  # None = full offload
        if split is None:
            x = normalize(arr, self.device)
        else:
            x = torch.from_numpy(arr.copy()).to(self.device).float()
        net = self.part(split)
        if self.device.startswith("cuda"):
            logits, gpu_ms = cuda_time_ms(net, x)
        else:
            t0 = now_ns(); logits = net(x); gpu_ms = (now_ns() - t0) / 1e6
        top5 = logits.topk(5, dim=1).indices.cpu().numpy().astype(np.int32)
        return top5, {"server_compute_ms": gpu_ms,
                      "server_total_ms": (now_ns() - t_recv) / 1e6}


def serve(host: str, port: int, model_name: str, pretrained: bool, device: str) -> None:
    srv = Server(model_name, pretrained, device)
    with socket.create_server((host, port)) as ls:
        # Short accept timeout so Ctrl+C works on Windows, where a blocking accept() ignores it.
        ls.settimeout(1.0)
        print(f"listening on {host}:{port} device={device}")
        while True:
            try:
                conn, addr = ls.accept()
            except socket.timeout:
                continue
            conn.settimeout(None)
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print(f"client {addr}")
            with conn:
                try:
                    while True:
                        header, arr = protocol.recv_frame(conn)
                        top5, stats = srv.handle(header, arr)
                        protocol.send_frame(conn, header["req"], top5, meta=stats)
                except (ConnectionError, OSError):
                    print("client disconnected")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=50051)
    ap.add_argument("--model", default="resnet50")
    ap.add_argument("--no-pretrained", action="store_true")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--threads", type=int, default=0, help="CPU threads for torch (0 = default)")
    a = ap.parse_args()
    if a.threads:
        torch.set_num_threads(a.threads)
    serve(a.host, a.port, a.model, not a.no_pretrained, a.device)


if __name__ == "__main__":
    main()
