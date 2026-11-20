"""Deliverable 1: activation payload profile (runs on one machine, no network).

Prints raw-frame size vs. activation size at every candidate split point, plus how
long each payload would take to transmit at the MVS rates.

    python scripts/payload_profile.py [--no-pretrained] [--csv results/payload_profile.csv]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from splitbench.model import SPLIT_POINTS, load_backbone, split_model  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="resnet50")
ap.add_argument("--size", type=int, default=224)
ap.add_argument("--no-pretrained", action="store_true")
ap.add_argument("--csv")
a = ap.parse_args()

model = load_backbone(a.model, not a.no_pretrained)
x = torch.randn(1, 3, a.size, a.size)
raw_u8 = 3 * a.size * a.size
rows = [{"point": "raw frame (uint8)", "shape": f"3x{a.size}x{a.size}", "bytes_fp32": raw_u8, "bytes_fp16": raw_u8}]
with torch.inference_mode():
    for sp in SPLIT_POINTS:
        out = split_model(model, sp)[0](x)
        n = out.numel()
        rows.append({"point": sp, "shape": "x".join(map(str, out.shape[1:])), "bytes_fp32": 4 * n, "bytes_fp16": 2 * n})
df = pd.DataFrame(rows)
df["vs_raw_fp32"] = (df.bytes_fp32 / raw_u8).round(2)
for mbit in (10, 100):
    df[f"tx_ms@{mbit}Mbps_fp32"] = (df.bytes_fp32 * 8 / (mbit * 1e6) * 1e3).round(1)
print(df.to_string(index=False))
if a.csv:
    Path(a.csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.csv, index=False)
