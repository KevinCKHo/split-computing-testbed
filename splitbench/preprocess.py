"""Input frames: identical uint8 224x224 frames for every configuration."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
STD = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)


def normalize(frame_u8: np.ndarray, device: str = "cpu") -> torch.Tensor:
    """uint8 (3,H,W) -> normalized float32 (1,3,H,W) on device."""
    x = torch.from_numpy(np.asarray(frame_u8)).to(device).float().div_(255).unsqueeze(0)
    return (x - MEAN.to(device)) / STD.to(device)


def load_frames(path: str | None, n: int, size: int = 224, seed: int = 0) -> np.ndarray:
    """Load frames.npy (N,3,H,W uint8) made by scripts/prepare_frames.py, else synthetic frames."""
    if path and Path(path).exists():
        frames = np.load(path)
        return frames[:n]
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, size=(n, 3, size, size), dtype=np.uint8)
