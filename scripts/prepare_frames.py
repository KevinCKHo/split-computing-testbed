"""Build the fixed input set: N images -> resize 256, center-crop 224 -> uint8 (N,3,224,224).

    python scripts/prepare_frames.py --images path/to/imagenet_val_subset --n 200 --out data/frames.npy
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from torchvision import transforms

ap = argparse.ArgumentParser()
ap.add_argument("--images", required=True)
ap.add_argument("--n", type=int, default=200)
ap.add_argument("--out", default="data/frames.npy")
a = ap.parse_args()

tf = transforms.Compose([transforms.Resize(256), transforms.CenterCrop(224)])
paths = sorted(p for p in Path(a.images).rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png"})[: a.n]
if len(paths) < a.n:
    raise SystemExit(f"found only {len(paths)} images, need {a.n}")
frames = np.stack([np.asarray(tf(Image.open(p).convert("RGB"))).transpose(2, 0, 1) for p in paths])
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
np.save(a.out, frames.astype(np.uint8))
print(f"saved {frames.shape} to {a.out}")
