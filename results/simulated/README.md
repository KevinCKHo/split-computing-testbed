# Draft results: SIMULATED, single machine

**Not the two-laptop testbed.** Client and server ran on one 4-core CPU-only Linux host over
loopback, with the link emulated by the app-level shaper (`splitbench/shaper.py`): uplink rate
paced by a token bucket, one-way delay paid in each direction (RTT = 2 x delay). ResNet-50 with
random weights (latency is unaffected; top-1 is meaningless), synthetic 224 x 224 frames,
20 warm-up + N = 200 measured requests per cell, 6 configurations x 4 profiles. The "server" is
a CPU with 2 threads, so server compute (about 68 ms for the full model) is far slower than the
RTX 4060 will be. Replace these files with a real run when you can.

Regenerate: see "Draft results on one machine" in the top-level README.

## Files

| File | Deliverable | What it shows |
| --- | --- | --- |
| `payload_profile.csv`, `fig1_payload.png` | 1 | bytes on the wire per split vs. the raw frame |
| `summary.csv`, `fig3_stages.png`, `fig4_tail.png` | 3 | median stage breakdown, p50 / p95 / p99 per cell |
| `fig2_crossover.png`, `winners.csv` | 2 | fastest strategy over 1-100 Mbit/s x 5-150 ms RTT (model from measured medians) |
| `fig2b_crossover_server_x15.png` | 2 | what-if: same, with server time / 15 as a stand-in for the GPU (assumption, not measured) |
| `raw_*.csv` | all | one row per request |

## Findings (simulated)

1. **Payload.** Lossless fp32 activations are 21.3x (layer1), 10.7x (layer2), 5.3x (layer3) and
   2.7x (layer4) the 150 KB uint8 frame. Only the pooled 2048-float vector (8 KB) is smaller.
2. **Network dominates every split.** At 10 Mbit/s, network time is 97 % of split A's 2.7 s and
   84 % of split D's 433 ms. Serialization is under 1 ms everywhere.
3. **No split wins any cell.** Full local (56-70 ms) is fastest in all four profiles, and the
   analytic model reproduces the measured winner in 4 of 4 cells. Among splits, later is always
   better (D < C < B < A), tracking payload size.
4. **With a GPU-speed server (what-if, x15)** full offload overtakes local only above about
   25 Mbit/s, and at 100 Mbit/s only below about 40 ms RTT; lossless splits still never win.
5. **Tails.** p99 / p50 ranges from 1.03x to 1.58x. The widest tails are compute-bound
   (full local 1.3-1.6x, split A at 10 Mbit/s 1.45x), likely from CPU contention on the shared
   host (two profiles ran in parallel). App-level shaping has no queueing or retransmission, so
   network tails on a real link will be wider.
