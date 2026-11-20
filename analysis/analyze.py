"""Deliverables 1-3 from a run: stats table, payload profile, stage breakdown, crossover map.

    python analysis/analyze.py --raw results/raw.csv --outdir results/ [--label "two-laptop testbed"]

Inputs : one or more raw CSVs from splitbench.client (glob allowed), profile names like bw10_d20
         (rate in Mbit/s, one-way delay in ms; emulated RTT = 2 x delay).
Outputs: summary.csv            n, payload, median of each stage, p95/p99 end-to-end
         winners.csv            fastest configuration per measured profile (by median)
         fig1_payload.png       Deliverable 1: bytes on the wire per configuration
         fig2_crossover.png     Deliverable 2: fastest strategy over 1-100 Mbit/s x 5-150 ms RTT,
                                modelled from measured medians, with measured winners overlaid
         fig3_stages.png        Deliverable 3: where the time goes (median stage breakdown)
         fig4_tail.png          Deliverable 3: median vs p99 end-to-end per configuration
Model used for the map (check it against the measured cells in winners.csv):
    T(config) = edge + serialize + server + RTT + bytes * 8 / bandwidth     (full local: edge only)
"""
from __future__ import annotations

import argparse
import glob
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Fixed categorical order (colour follows the entity, never its rank).
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
CONFIG_ORDER = ["full_local", "full_offload", "split_A_early", "split_B_mid", "split_C_late", "split_D_layer4"]
STAGES = [("edge_compute_ms", "Edge compute"), ("serialize_ms", "Serialize"),
          ("network_ms", "Network (RTT + transfer)"), ("server_total_ms", "Server")]
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3dd"


def color_of(cfg: str) -> str:
    return PALETTE[CONFIG_ORDER.index(cfg)] if cfg in CONFIG_ORDER else PALETTE[-1]


def style(ax) -> None:
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelcolor=INK, labelsize=9)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def parse_profile(name: str) -> tuple[float, float]:
    m = re.match(r"bw([\d.]+)_d([\d.]+)", name)
    return (float(m.group(1)), 2 * float(m.group(2))) if m else (np.nan, np.nan)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df.warmup == 0]
    agg = df.groupby(["config", "profile"]).agg(
        n=("e2e_ms", "size"), payload_bytes=("payload_bytes", "median"),
        **{f"{s}_p50": (s, "median") for s, _ in STAGES},
        e2e_ms_p50=("e2e_ms", "median"),
        e2e_ms_p95=("e2e_ms", lambda s: s.quantile(0.95)),
        e2e_ms_p99=("e2e_ms", lambda s: s.quantile(0.99))).reset_index()
    agg[["rate_mbit", "rtt_ms"]] = agg.profile.apply(lambda p: pd.Series(parse_profile(p)))
    agg["order"] = agg.config.map(lambda c: CONFIG_ORDER.index(c) if c in CONFIG_ORDER else 99)
    return agg.sort_values(["rate_mbit", "rtt_ms", "order"]).drop(columns="order")


def model_latency(per: pd.Series, bw: np.ndarray, rtt: np.ndarray) -> np.ndarray:
    if per.payload_bytes == 0:
        return np.full(np.broadcast(bw, rtt).shape, per.edge)
    return per.edge + per.ser + per.srv + rtt + per.payload_bytes * 8 / (bw * 1e6) * 1e3


def fig_payload(s: pd.DataFrame, out: Path, label: str) -> None:
    p = s[s.payload_bytes > 0].groupby("config").payload_bytes.median()
    p = p.reindex([c for c in CONFIG_ORDER if c in p.index])
    raw = p.get("full_offload", np.nan)
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    y = np.arange(len(p))[::-1]
    ax.barh(y, p.values / 1e3, height=0.6, color=[PALETTE[1] if c == "full_offload" else PALETTE[0] for c in p.index])
    for yi, (c, b) in zip(y, p.items()):
        ax.text(b / 1e3 * 1.08, yi, f"{b/1e3:,.0f} KB  ({b/raw:.1f}x raw)" if c != "full_offload" else f"{b/1e3:,.0f} KB  raw uint8 frame",
                va="center", fontsize=9, color=INK)
    ax.set_yticks(y, [c.replace("_", " ") for c in p.index])
    ax.set_xscale("log"); ax.set_xlim(right=p.max() / 1e3 * 8)
    ax.set_xlabel("Bytes sent per request (KB, log scale)", color=INK)
    style(ax)
    ax.set_title(f"Every lossless split sends more than the raw frame\n{label}", loc="left", fontsize=11, color=INK)
    fig.tight_layout(); fig.savefig(out / "fig1_payload.png", dpi=200); plt.close(fig)


def fig_crossover(s: pd.DataFrame, out: Path, label: str) -> pd.DataFrame:
    per = s.groupby("config").agg(edge=("edge_compute_ms_p50", "median"), ser=("serialize_ms_p50", "median"),
                                  srv=("server_total_ms_p50", "median"), payload_bytes=("payload_bytes", "median"))
    names = [c for c in CONFIG_ORDER if c in per.index] + [c for c in per.index if c not in CONFIG_ORDER]
    bws, rtts = np.logspace(0, 2, 200), np.linspace(5, 150, 200)
    B, R = np.meshgrid(bws, rtts)
    T = np.stack([model_latency(per.loc[n], B, R) for n in names])
    win = np.argmin(T, axis=0)
    present = sorted(set(win.ravel()))
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap([color_of(n) for n in names])
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.pcolormesh(bws, rtts, win, cmap=cmap, vmin=-0.5, vmax=len(names) - 0.5, shading="auto", alpha=0.35, linewidth=0)
    ax.contour(bws, rtts, win, levels=np.arange(len(names)) + 0.5, colors=INK, linewidths=0.8)
    # measured cells
    meas = s.loc[s.groupby("profile").e2e_ms_p50.idxmin()]
    for _, r in meas.iterrows():
        ax.scatter(r.rate_mbit, r.rtt_ms, s=90, color=color_of(r.config), edgecolor="white", linewidth=2, zorder=3)
        ax.annotate(f"measured: {r.config.replace('_', ' ')}\n{r.e2e_ms_p50:.0f} ms", (r.rate_mbit, r.rtt_ms),
                    textcoords="offset points", xytext=(8, 6), fontsize=8, color=INK)
    handles = [plt.Rectangle((0, 0), 1, 1, color=color_of(names[i]), alpha=0.6) for i in present]
    ax.legend(handles, [names[i].replace("_", " ") for i in present], title="Fastest (model)",
              loc="upper right", fontsize=8, title_fontsize=8, frameon=False)
    ax.set_xscale("log"); ax.set_xlabel("Uplink bandwidth (Mbit/s, log scale)", color=INK)
    ax.set_ylabel("Round-trip time (ms)", color=INK); style(ax); ax.grid(False)
    ax.set_title(f"Fastest strategy by bandwidth and RTT\n{label}", loc="left", fontsize=11, color=INK)
    fig.tight_layout(); fig.savefig(out / "fig2_crossover.png", dpi=200); plt.close(fig)
    # model check on measured cells
    chk = []
    for prof, g in s.groupby("profile"):
        bw, rtt = parse_profile(prof)
        pred = {n: float(model_latency(per.loc[n], np.array(bw), np.array(rtt))) for n in names}
        best = g.loc[g.e2e_ms_p50.idxmin()]
        chk.append({"profile": prof, "measured_winner": best.config, "measured_ms": round(best.e2e_ms_p50, 1),
                    "model_winner": min(pred, key=pred.get), "model_ms": round(min(pred.values()), 1)})
    return pd.DataFrame(chk)


def fig_stages(s: pd.DataFrame, out: Path, label: str) -> None:
    profs = s.drop_duplicates("profile").sort_values(["rate_mbit", "rtt_ms"]).profile.tolist()
    fig, axes = plt.subplots(len(profs), 1, figsize=(7.5, 1.9 * len(profs) + 0.8), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, prof in zip(axes, profs):
        g = s[s.profile == prof].set_index("config")
        g = g.reindex([c for c in CONFIG_ORDER if c in g.index])
        y = np.arange(len(g))[::-1]
        left = np.zeros(len(g))
        for i, (col, name) in enumerate(STAGES):
            v = g[f"{col}_p50"].clip(lower=0).values
            ax.barh(y, v, left=left, height=0.62, color=PALETTE[i], label=name, edgecolor="white", linewidth=1)
            left += v
        for yi, tot in zip(y, g.e2e_ms_p50.values):
            ax.text(tot * 1.12, yi, f"{tot:,.0f} ms", va="center", fontsize=8, color=INK)
        ax.set_yticks(y, [c.replace("_", " ") for c in g.index], fontsize=8)
        bw, rtt = parse_profile(prof)
        ax.set_title(f"{bw:g} Mbit/s, {rtt:g} ms RTT", loc="left", fontsize=9, color=INK)
        ax.set_xscale("symlog", linthresh=10); style(ax)
    axes[-1].set_xlabel("Median latency per request (ms, symlog scale)", color=INK)
    axes[0].legend(loc="lower right", bbox_to_anchor=(1, 1.25), ncol=4, fontsize=8, frameon=False)
    fig.suptitle(f"Where the time goes\n{label}", x=0.02, ha="left", fontsize=11, color=INK)
    fig.tight_layout(); fig.savefig(out / "fig3_stages.png", dpi=200); plt.close(fig)


def fig_tail(s: pd.DataFrame, out: Path, label: str) -> None:
    profs = s.drop_duplicates("profile").sort_values(["rate_mbit", "rtt_ms"]).profile.tolist()
    cfgs = [c for c in CONFIG_ORDER if c in s.config.unique()]
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    w = 0.8 / len(cfgs)
    for i, c in enumerate(cfgs):
        g = s[s.config == c].set_index("profile").reindex(profs)
        x = np.arange(len(profs)) + (i - (len(cfgs) - 1) / 2) * w
        ax.vlines(x, g.e2e_ms_p50, g.e2e_ms_p99, color=color_of(c), linewidth=2)
        ax.scatter(x, g.e2e_ms_p50, color=color_of(c), s=22, zorder=3, label=c.replace("_", " "))
        ax.scatter(x, g.e2e_ms_p99, color=color_of(c), s=22, marker="_", zorder=3)
    ax.set_xticks(range(len(profs)), [f"{parse_profile(p)[0]:g} Mbit/s\n{parse_profile(p)[1]:g} ms RTT" for p in profs], fontsize=8)
    ax.set_yscale("log"); ax.set_ylabel("End-to-end latency (ms, log)\ndot = median, tick = p99", color=INK)
    style(ax); ax.grid(axis="y", color=GRID); ax.grid(axis="x", visible=False)
    ax.legend(fontsize=8, frameon=False, ncol=3, loc="upper left", bbox_to_anchor=(0, -0.22))
    ax.set_title(f"Median to p99 spread per configuration\n{label}", loc="left", fontsize=11, color=INK)
    fig.tight_layout(); fig.savefig(out / "fig4_tail.png", dpi=200); plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", nargs="+", default=["results/raw.csv"])
    ap.add_argument("--outdir", default="results")
    ap.add_argument("--label", default="two-laptop testbed")
    a = ap.parse_args()
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    files = [f for pat in a.raw for f in sorted(glob.glob(pat))]
    s = summarize(pd.concat([pd.read_csv(f) for f in files], ignore_index=True))
    s.round(3).to_csv(out / "summary.csv", index=False)
    fig_payload(s, out, a.label)
    chk = fig_crossover(s, out, a.label)
    chk.to_csv(out / "winners.csv", index=False)
    fig_stages(s, out, a.label)
    fig_tail(s, out, a.label)
    cols = ["config", "profile", "n", "payload_bytes", "edge_compute_ms_p50", "network_ms_p50", "e2e_ms_p50", "e2e_ms_p99"]
    print(s[cols].round(1).to_string(index=False)); print(); print(chk.to_string(index=False))


if __name__ == "__main__":
    main()
