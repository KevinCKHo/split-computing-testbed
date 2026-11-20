"""Run every configuration under every network profile from the edge laptop.

    python scripts/run_matrix.py --shaper app      # any OS: app-level rate + delay (default on Windows)
    python scripts/run_matrix.py --shaper qos      # Windows: OS QoS rate limit + app-level delay (admin)
    python scripts/run_matrix.py --shaper netem    # Linux: tc htb + netem (sudo)
    python scripts/run_matrix.py --dry-run         # print commands only

Delay convention everywhere: profile delay_ms is ONE-WAY and is paid in both directions,
so the emulated RTT = 2 x delay_ms on top of the physical link.
"""
from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def sh(cmd: list[str], dry: bool) -> None:
    print("+", " ".join(cmd), flush=True)
    if not dry:
        subprocess.run(cmd, check=True, cwd=ROOT)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/experiment.yaml")
    ap.add_argument("--frames", default="data/frames.npy")
    ap.add_argument("--out", default="results/raw.csv")
    ap.add_argument("--shaper", choices=["app", "qos", "netem", "none"],
                    default="app" if platform.system() == "Windows" else "netem")
    ap.add_argument("--profiles", nargs="*", help="only these profile names")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("client_args", nargs=argparse.REMAINDER, help="extra args after -- go to the client")
    a = ap.parse_args()
    exp = yaml.safe_load((ROOT / a.config).read_text())
    iface = exp["edge"].get("iface", "")
    extra = [x for x in a.client_args if x != "--"]
    ps = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "scripts/win_qos.ps1")]
    netem = ["sudo", str(ROOT / "scripts/netem.sh")]
    try:
        for p in exp["profiles"]:
            if a.profiles and p["name"] not in a.profiles:
                continue
            rate, delay = p["rate_mbit"], p["delay_ms"]
            shaping: list[str] = []
            if a.shaper == "app":
                shaping = ["--rate-mbit", str(rate), "--delay-ms", str(delay)]
            elif a.shaper == "qos":
                sh(ps + ["-RateMbit", str(rate)], a.dry_run)
                shaping = ["--delay-ms", str(delay)]
            elif a.shaper == "netem":  # whole RTT on edge egress
                sh(netem + ["apply", iface, str(rate), str(2 * delay),
                            str(p.get("loss_pct", 0)), str(p.get("jitter_ms", 0))], a.dry_run)
            sh([sys.executable, "-m", "splitbench.client", "--config", a.config, "--profile", p["name"],
                "--frames", a.frames, "--out", a.out, *shaping, *extra], a.dry_run)
    finally:
        if a.shaper == "qos":
            sh(ps + ["-Clear"], a.dry_run)
        elif a.shaper == "netem":
            sh(netem + ["clear", iface], a.dry_run)


if __name__ == "__main__":
    main()
