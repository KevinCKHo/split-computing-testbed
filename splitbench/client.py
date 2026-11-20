"""Edge client (Intel laptop).

Runs every configuration in the experiment config against the server and appends one
CSV row per measured request. Link emulation, either:
  * app-level (any OS, default on Windows): --rate-mbit / --delay-ms, see shaper.py
  * OS-level: apply scripts/win_qos.ps1 or scripts/netem.sh first, then run without them

    python -m splitbench.client --profile bw10_d20 --rate-mbit 10 --delay-ms 20 --out results/raw.csv
"""
from __future__ import annotations

import argparse
import csv
import socket
from pathlib import Path

import numpy as np
import torch
import yaml

from . import protocol
from .model import load_backbone, split_for_mode, split_model
from .preprocess import load_frames, normalize
from .shaper import LinkShaper
from .timing import now_ns

FIELDS = ["config", "profile", "req", "warmup", "payload_bytes", "edge_compute_ms",
          "serialize_ms", "send_block_ms", "server_compute_ms", "server_total_ms",
          "network_ms", "e2e_ms", "top1"]


@torch.inference_mode()
def run_config(cfg: dict, exp: dict, frames: np.ndarray, model, sock: socket.socket | None,
               profile: str, writer: csv.DictWriter, shaper: LinkShaper | None = None) -> None:
    shaper = shaper or LinkShaper()
    split = split_for_mode(cfg["mode"], cfg.get("split"))
    edge, _ = split_model(model, split)
    dtype = np.dtype(exp.get("payload_dtype", "float32"))
    warm = exp["warmup"]
    for i in range(warm + len(frames)):
        frame = frames[i % len(frames)]
        row = {"config": cfg["name"], "profile": profile, "req": i, "warmup": int(i < warm)}
        t_start = now_ns()

        # 1. edge compute
        if cfg["mode"] == "offload":
            payload = frame  # raw uint8 frame, normalized on the server
            row["edge_compute_ms"] = 0.0
        else:
            t0 = now_ns()
            out = edge(normalize(frame))
            row["edge_compute_ms"] = (now_ns() - t0) / 1e6
            if cfg["mode"] == "local":
                row.update(payload_bytes=0, serialize_ms=0.0, send_block_ms=0.0,
                           server_compute_ms=0.0, server_total_ms=0.0, network_ms=0.0,
                           e2e_ms=(now_ns() - t_start) / 1e6, top1=int(out.argmax()))
                writer.writerow(row)
                continue
            # 2. serialize (tensor -> contiguous bytes)
            t0 = now_ns()
            payload = out.numpy().astype(dtype, copy=False)
            data = protocol.encode(i, payload, now_ns(), meta={"split": split})
            row["serialize_ms"] = (now_ns() - t0) / 1e6

        if cfg["mode"] == "offload":
            t0 = now_ns()
            data = protocol.encode(i, payload, now_ns(), meta={"split": None})
            row["serialize_ms"] = (now_ns() - t0) / 1e6

        # 3. transmit + wait for result
        t0 = now_ns()
        shaper.send(sock, data)
        row["send_block_ms"] = (now_ns() - t0) / 1e6
        header, top5 = protocol.recv_frame(sock)
        shaper.after_receive()
        t_end = now_ns()

        row["payload_bytes"] = len(data)
        row["server_compute_ms"] = header["server_compute_ms"]
        row["server_total_ms"] = header["server_total_ms"]
        row["e2e_ms"] = (t_end - t_start) / 1e6
        # Network time without clock sync: everything not spent computing.
        row["network_ms"] = row["e2e_ms"] - row["edge_compute_ms"] - row["serialize_ms"] - row["server_total_ms"]
        row["top1"] = int(top5[0, 0])
        writer.writerow(row)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/experiment.yaml")
    ap.add_argument("--profile", required=True, help="label of the netem profile currently applied")
    ap.add_argument("--frames", default="data/frames.npy")
    ap.add_argument("--out", default="results/raw.csv")
    ap.add_argument("--only", nargs="*", help="run only these config names")
    ap.add_argument("--host"); ap.add_argument("--port", type=int)
    ap.add_argument("--no-pretrained", action="store_true")
    ap.add_argument("--threads", type=int, default=0, help="override edge.torch_threads")
    ap.add_argument("--rate-mbit", type=float, default=0.0, help="app-level uplink rate (0 = off)")
    ap.add_argument("--delay-ms", type=float, default=0.0, help="app-level one-way delay, applied each way")
    a = ap.parse_args()
    shaper = LinkShaper(a.rate_mbit, a.delay_ms)

    exp = yaml.safe_load(Path(a.config).read_text())
    ap_threads = exp["edge"].get("torch_threads", 4)
    torch.set_num_threads(a.threads or ap_threads)
    frames = load_frames(a.frames, exp["num_frames"], exp["input_size"])
    model = load_backbone(exp["model"], exp["pretrained"] and not a.no_pretrained)
    host, port = a.host or exp["server"]["host"], a.port or exp["server"]["port"]

    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    new = not out.exists()
    configs = [c for c in exp["configs"] if not a.only or c["name"] in a.only]
    with out.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        sock = None
        if any(c["mode"] != "local" for c in configs):
            sock = socket.create_connection((host, port))
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            for cfg in configs:
                print(f"[{a.profile}] {cfg['name']} ...", flush=True)
                run_config(cfg, exp, frames, model, sock, a.profile, w, shaper)
                f.flush()
        finally:
            if sock:
                sock.close()


if __name__ == "__main__":
    main()
