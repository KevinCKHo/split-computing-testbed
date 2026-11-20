# splitbench: split-computing latency testbed

Measures when running the first layers of a CNN on an edge laptop and the rest on a GPU
server beats full local inference or raw-frame offloading, under emulated uplinks
(Linux `tc`/`netem`). Built from *Proposal V2* (Network-Aware Split Computing for Edge AI).

```
edge laptop (Intel CPU, Linux)                server laptop (RTX 4060, Windows)
splitbench.client                             splitbench.server
 frame -> edge layers -> serialize --TCP-->   deserialize -> remaining layers (CUDA)
          ^ tc htb+netem on egress            -> top-5 back to client
```

## Layout

| Path | What it is |
| --- | --- |
| `configs/experiment.yaml` | model, split points, network profiles, N, server address |
| `splitbench/model.py` | splits torchvision ResNet into edge / server parts |
| `splitbench/protocol.py` | length-prefixed binary tensor framing over TCP (no pickle) |
| `splitbench/server.py` | GPU inference server, CUDA-event timing |
| `splitbench/client.py` | edge client, per-stage timing, one CSV row per request |
| `scripts/netem.sh` | apply / clear a rate + delay (+ loss, jitter) profile |
| `scripts/run_matrix.py` | every config x every profile, writes `results/raw.csv` |
| `scripts/payload_profile.py` | Deliverable 1: raw vs activation bytes per split point |
| `scripts/prepare_frames.py` | builds the fixed 200-frame input set |
| `analysis/analyze.py` | Deliverables 2-3: median/p95/p99, crossover map |
| `tests/` | split correctness + protocol round-trip (no GPU / network needed) |

## Setup

### Edge laptop (Linux, Ubuntu 22.04/24.04)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python -m pytest -q
sudo ip addr add 192.168.50.1/24 dev <edge-iface>
```

Set the CPU governor to `performance`, turn off Wi-Fi during runs, and disable NIC offloads
if you capture packets (`sudo ethtool -K <iface> tso off gso off gro off`).

### Server laptop (Windows 10/11, PowerShell)

```powershell
py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1
# CUDA build of torch: pick the index URL for your driver on pytorch.org, e.g.
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
python -m pytest -q
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Static IP on the Ethernet adapter (admin PowerShell; check the adapter name with `Get-NetAdapter`):

```powershell
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.50.2 -PrefixLength 24
New-NetFirewallRule -DisplayName "splitbench" -Direction Inbound -Protocol TCP -LocalPort 50051 -Action Allow
```

Plug in AC power, choose the "Best performance" power mode, and pause Windows Update and
other background downloads during runs. Then from the edge: `ping 192.168.50.2`.

All `tc` shaping happens on the Linux edge; nothing on the Windows side needs root or tc.

## Run

```bash
# once: fixed input set (any 200 ImageNet val images)
python scripts/prepare_frames.py --images ~/imagenet_val_200 --out data/frames.npy

# Deliverable 1 (either machine)
python scripts/payload_profile.py --csv results/payload_profile.csv

# server laptop (Windows PowerShell, venv active)
python -m splitbench.server --host 0.0.0.0 --port 50051

# edge laptop: baseline with no shaping (Phase 1)
python -m splitbench.client --profile none --out results/raw.csv
# edge laptop: full MVS matrix (Phase 2, uses sudo for tc)
python scripts/run_matrix.py --out results/raw.csv

# analysis (Phase 3)
python analysis/analyze.py --raw results/raw.csv --outdir results/
```

Packet traces for the bottleneck analysis: `sudo tcpdump -i <iface> -w results/<profile>.pcap port 50051`
alongside a run, and `ss -tin dst 192.168.50.2` for cwnd, RTT and retransmits.

## Notes

- `network_ms` = end-to-end minus edge compute, serialization and server time, so no clock
  sync is needed. For one-way transit, sync both clocks with `chrony`/PTP and compare
  `t_send_ns` against the server receive time.
- `scripts/netem.sh` shapes edge egress only. Because the server is Windows, put the whole added
  RTT on the edge uplink; for one request/response this gives the same end-to-end latency.
- The proposal says both machines run Linux. With a Windows server, state the change in the
  report: shaping and the timers that matter for network time are on the Linux edge, and
  server compute is timed with CUDA events, which work the same on Windows.
- One-way transit needs synced clocks; Windows time sync is coarse, so rely on `network_ms`.
- Lossless fp32 activations at layer1-layer4 are larger than the uint8 raw frame
  (see `payload_profile.py`). `payload_dtype: float16` is available as a variant.
