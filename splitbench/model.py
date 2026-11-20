"""Split a torchvision ResNet into an edge part and a server part.

The edge part runs every module up to and including `split`; the server part runs
everything after it. mode='local' -> edge runs all; mode='offload' -> server runs all.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torchvision

# Execution order of ResNet top-level modules (flatten is applied before fc).
RESNET_ORDER = ["conv1", "bn1", "relu", "maxpool", "layer1", "layer2", "layer3", "layer4", "avgpool", "fc"]
SPLIT_POINTS = ["layer1", "layer2", "layer3", "layer4", "avgpool"]


class _Seq(nn.Module):
    def __init__(self, model: nn.Module, names: list[str]):
        super().__init__()
        self.names = names
        self.mods = nn.ModuleDict({n: getattr(model, n) for n in names})

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for n in self.names:
            if n == "fc":
                x = torch.flatten(x, 1)
            x = self.mods[n](x)
        return x


def load_backbone(name: str = "resnet50", pretrained: bool = True) -> nn.Module:
    weights = "DEFAULT" if pretrained else None
    model = getattr(torchvision.models, name)(weights=weights)
    return model.eval()


def split_model(model: nn.Module, split: str | None) -> tuple[nn.Module, nn.Module]:
    """Return (edge, server). split=None -> edge empty (offload); split='fc' -> server empty (local)."""
    if split is None:
        cut = 0
    elif split == "fc":
        cut = len(RESNET_ORDER)
    else:
        if split not in RESNET_ORDER:
            raise ValueError(f"unknown split {split!r}; choose from {SPLIT_POINTS}")
        cut = RESNET_ORDER.index(split) + 1
    return _Seq(model, RESNET_ORDER[:cut]).eval(), _Seq(model, RESNET_ORDER[cut:]).eval()


def split_for_mode(mode: str, split: str | None = None) -> str | None:
    return {"local": "fc", "offload": None, "split": split}[mode]
