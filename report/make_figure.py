"""Compact stage-breakdown figure for the checkpoint report (two profiles side by side).

    python report/make_figure.py results/simulated/summary.csv report/fig_stages_compact.png
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
STAGES = [("edge_compute_ms_p50", "Edge compute"), ("serialize_ms_p50", "Serialize"),
          ("network_ms_p50", "Network (RTT + transfer)"), ("server_total_ms_p50", "Server")]
ORDER = ["full_local", "full_offload", "split_A_early", "split_B_mid", "split_C_late", "split_D_layer4"]
NAMES = ["Full local", "Full offload", "Split A (layer1)", "Split B (layer2)", "Split C (layer3)", "Split D (layer4)"]
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3dd"

s = pd.read_csv(sys.argv[1])
profiles = [("bw10_d20", "10 Mbit/s, 20 ms one-way (40 ms RTT)"), ("bw100_d20", "100 Mbit/s, 20 ms one-way (40 ms RTT)")]
fig, axes = plt.subplots(1, 2, figsize=(7.6, 2.5))
for ax, (prof, title) in zip(axes, profiles):
    g = s[s.profile == prof].set_index("config").reindex(ORDER)
    y = np.arange(len(g))[::-1]
    left = np.zeros(len(g))
    for i, (col, name) in enumerate(STAGES):
        v = g[col].clip(lower=0).values
        ax.barh(y, v, left=left, height=0.62, color=PALETTE[i], label=name, edgecolor="white", linewidth=0.8)
        left += v
    mx = g.e2e_ms_p50.max()
    for yi, tot in zip(y, g.e2e_ms_p50.values):
        ax.text(tot + mx * 0.02, yi, f"{tot:,.0f}", va="center", fontsize=7.5, color=INK)
    ax.set_xlim(0, mx * 1.18)
    ax.set_title(title, loc="left", fontsize=9, color=INK)
    ax.set_xlabel("Median latency (ms)", fontsize=8, color=INK)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelcolor=INK, labelsize=7.5)
    ax.grid(axis="x", color=GRID, linewidth=0.7); ax.set_axisbelow(True)
axes[0].set_yticks(np.arange(len(ORDER))[::-1], NAMES)
axes[1].set_yticks(np.arange(len(ORDER))[::-1], [])
axes[0].legend(loc="lower left", bbox_to_anchor=(0, 1.13), ncol=4, fontsize=7.5, frameon=False)
fig.subplots_adjust(left=0.15, right=0.98, bottom=0.17, top=0.78, wspace=0.08); fig.savefig(sys.argv[2], dpi=220)
