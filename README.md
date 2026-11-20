# splitbench: split-computing latency testbed

Measures when running the first layers of a CNN on an edge laptop and the rest on a GPU
server beats full local inference or raw-frame offloading, under emulated uplinks.
Built from *Proposal V2* (Network-Aware Split Computing for Edge AI).

```
edge laptop (Intel CPU, Windows)                server laptop (RTX 4060, Windows)
splitbench.client                               splitbench.server
 frame -> edge layers -> serialize --TCP-->     deserialize -> remaining layers (CUDA)
          ^ link shaping on the edge            -> top-5 back to client
```

Both laptops run Windows. Everything runs natively there; an Ubuntu live USB on the edge
is an optional, more precise path for link emulation (see [Link shaping](#link-shaping)).

## Layout

| Path | What it is |
| --- | --- |
| `configs/experiment.yaml` | model, split points, network profiles, N, server address |
| `configs/simulated_single_machine.yaml` | same matrix on one machine over loopback (draft results) |
| `splitbench/model.py` | splits torchvision ResNet into edge / server parts |
| `splitbench/protocol.py` | length-prefixed binary tensor framing over TCP (no pickle) |
| `splitbench/shaper.py` | app-level link emulation: token-bucket rate + one-way delay each way |
| `splitbench/server.py` | GPU inference server, CUDA-event timing |
| `splitbench/client.py` | edge client, per-stage timing, one CSV row per request |
| `scripts/run_matrix.py` | every config x every profile, writes `results/raw.csv` |
| `scripts/win_qos.ps1` | Windows built-in QoS uplink rate limit (OS-level) |
| `scripts/netem.sh` | Linux tc htb + netem (Ubuntu USB path) |
| `scripts/payload_profile.py` | Deliverable 1: raw vs activation bytes per split point |
| `scripts/prepare_frames.py` | builds the fixed 200-frame input set |
| `analysis/analyze.py` | Deliverables 1-3: stats, payload, crossover map, stage breakdown, tails |
| `tests/` | split correctness + protocol round-trip (no GPU / network needed) |

## Setup (both laptops, PowerShell)

Install Python 3.11 or 3.12 from python.org (tick "Add to PATH") and Git, then:

```powershell
git clone https://github.com/KevinCKHo/split-computing-testbed
cd split-computing-testbed
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1        # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Server (RTX 4060), CUDA build of PyTorch (pick the index URL matching your driver on pytorch.org):

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
python -m pytest -q
```

Edge (Intel CPU), CPU build:

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python -m pytest -q
```

Download the pretrained weights once on both machines while you still have internet:
`python -c "import torchvision; torchvision.models.resnet50(weights='DEFAULT')"`.

### Direct Ethernet link with static IPs (admin PowerShell)

Connect the laptops with one Ethernet cable (USB-Ethernet adapters are fine). Find the adapter
name with `Get-NetAdapter`, then:

```powershell
# edge laptop
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.50.1 -PrefixLength 24
# server laptop
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.50.2 -PrefixLength 24
New-NetFirewallRule -DisplayName "splitbench" -Direction Inbound -Protocol TCP -LocalPort 50051 -Action Allow
# both: allow ping for checks, mark the link private
New-NetFirewallRule -DisplayName "ICMPv4 in" -Protocol ICMPv4 -IcmpType 8 -Direction Inbound -Action Allow
Set-NetConnectionProfile -InterfaceAlias "Ethernet" -NetworkCategory Private
```

From the edge: `ping 192.168.50.2`. Turn Wi-Fi off during runs so traffic cannot take another
path. Optional: `iperf3` (Windows builds at iperf.fr) to confirm line rate and each shaped rate.

### Power and noise (replaces the Linux CPU governor)

On both laptops: plug in AC power, Settings > System > Power > Power mode = **Best performance**
(or `powercfg /setactive SCHEME_MIN` for High performance), pause Windows Update, close
browsers, OneDrive and game launchers. On the server, set the NVIDIA Control Panel power
management mode to "Prefer maximum performance". Let each run warm up (the client does 20
warm-up requests per configuration).

## Link shaping

Windows has no built-in equivalent of Linux `tc netem`. Three options, in order of setup effort:

| Option | Rate | Delay | Loss / jitter | Realism | Use for |
| --- | --- | --- | --- | --- | --- |
| `--shaper app` (default) | token bucket in the client | sleep each way | no | deterministic model of the link; no TCP queue or cwnd effects | Deliverables 1-2, the main matrix |
| `--shaper qos` | Windows QoS throttle (OS, real TCP) | app sleep each way | no | real TCP pacing on the uplink | bottleneck analysis (socket buffers) |
| Ubuntu live USB on the edge, `--shaper netem` | tc htb | netem | yes | packet level, the proposal's original design | loss, jitter, retransmission traces |

`clumsy` (WinDivert-based, GUI) can add loss and jitter on Windows if you need them without
Linux: filter `tcp.DstPort == 50051`, enable Drop / Lag. Its throttle is bursty, so do not use it
for the rate.

Delay convention for all options: a profile's `delay_ms` is one-way and paid in both directions,
so emulated RTT = 2 x `delay_ms` on top of the physical link (about 0.3 ms on a cable).

## Run

```powershell
# once: fixed input set (any 200 ImageNet val images); without it, synthetic frames are used
python scripts\prepare_frames.py --images C:\data\imagenet_val_200 --out data\frames.npy

# Deliverable 1 (either machine)
python scripts\payload_profile.py --csv results\payload_profile.csv

# server laptop
python -m splitbench.server --host 0.0.0.0 --port 50051

# edge laptop: Phase 1 baseline, no shaping
python -m splitbench.client --profile none --out results\raw.csv
# edge laptop: full MVS matrix (app-level shaping)
python scripts\run_matrix.py --shaper app --out results\raw.csv
# or with the OS rate limit (admin PowerShell)
python scripts\run_matrix.py --shaper qos --out results\raw_qos.csv

# analysis (Phase 3)
python analysis\analyze.py --raw results\raw.csv --outdir results --label "two-laptop testbed"
```

Packet traces for the bottleneck analysis: Wireshark (with Npcap) on the edge with capture
filter `tcp port 50051`, or the built-in `pktmon start --capture --pkt-size 128` / `pktmon stop` /
`pktmon etl2pcap PktMon.etl`. `Get-NetTCPConnection -RemotePort 50051` shows connection state.

### Draft results on one machine

`results/simulated/` holds a full-matrix run (findings in `results/simulated/README.md`) with client and server on one CPU-only host over
loopback with app-level shaping and random weights. It is **simulated**: server compute is a
CPU, not the RTX 4060. Regenerate it with:

```powershell
python -m splitbench.server --host 127.0.0.1 --port 50061 --no-pretrained --device cpu --threads 2
python scripts\run_matrix.py --config configs\simulated_single_machine.yaml --shaper app --frames none `
    --out results\simulated\raw.csv -- --threads 2 --port 50061 --no-pretrained
python analysis\analyze.py --raw "results\simulated\raw*.csv" --outdir results\simulated --server-speedup 15 `
    --label "SIMULATED: one CPU host over loopback, app-level link (not the two-laptop testbed)"
```

### Ubuntu live USB path (optional, edge only)

Boot the edge laptop from an Ubuntu 24.04 USB ("Try Ubuntu"), install Python and the CPU build of
PyTorch, set `edge.iface` in the config (`ip -br link`), then
`sudo ip addr add 192.168.50.1/24 dev <iface>` and `python scripts/run_matrix.py --shaper netem`.
The server stays on Windows. Set the governor with `sudo cpupower frequency-set -g performance`.

## Notes

- `network_ms` = end-to-end minus edge compute, serialization and server time, so no clock
  sync is needed (Windows time sync is too coarse for one-way timing).
- `time.perf_counter_ns` uses QueryPerformanceCounter on Windows (sub-microsecond).
  Server compute is timed with CUDA events.
- The proposal assumed Linux on both machines. State the change in the report: shaping is
  app-level or Windows QoS, and the Ubuntu USB path reproduces the original tc design.
- Lossless fp32 activations at layer1-layer4 are larger than the uint8 raw frame
  (see `payload_profile.py`). `payload_dtype: float16` is available as a variant.
