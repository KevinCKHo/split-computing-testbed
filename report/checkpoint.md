---
title: "Network-Aware Split Computing for Edge AI: Evaluating Latency Crossover Boundaries Under Constrained Links"
subtitle: "EE289 Course Project Checkpoint · Fall 2026 · Chih-Kuan Ho (individual project)"
---

> **Status of the evidence.** The results in Section 3 are **measurements from the two-laptop testbed** (Intel edge laptop on Wi-Fi, RTX 4060 server laptop wired, same subnet; Windows on both; app-level link shaping). Each cell is the median of 200 requests after 20 warm-up requests. A single-machine simulation run earlier is kept only as a cross-check.

## 1. Current question and scope

**Question (unchanged from Proposal v2).** For which combinations of uplink bandwidth (1–100 Mbit/s) and round-trip time (5–150 ms) does offloading an intermediate activation give lower end-to-end latency than full on-device inference or full raw-frame offloading, and which split point is most efficient?

**Scope (unchanged).** One pretrained CNN backbone (torchvision ResNet-50, 224 × 224 input, no fine-tuning, no compression or distillation), point-to-point edge-to-server link, N = 200 measured requests per configuration, minimum viable matrix of 10 / 100 Mbit/s uplink × 20 / 100 ms **one-way** propagation delay. The delay is applied in each direction, so the emulated RTT is 40 / 200 ms, on top of the physical link's own RTT (measured separately in the unshaped baseline). The 200 ms emulated RTT lies outside the question's 5–150 ms RTT range; it is kept as Proposal v2 specifies, as a distant-cloud bound, and the crossover map covers 5–150 ms.

**Changes since Proposal v2.** The testbed has moved from Linux to Windows on both laptops. This change has not yet been approved; it is reported here so the instructor can review it.

| Change | Reason |
| --- | --- |
| Both laptops run **Windows**, not Linux. Link emulation uses (a) an application-level shaper (token-bucket rate + fixed one-way delay each way) by default and (b) the Windows built-in QoS rate limit for real TCP pacing. Linux `tc`/`netem` is kept as an optional path by booting the edge laptop from an Ubuntu live USB. | Hardware availability. Windows has no `tc`/`netem` equivalent. |
| Added a fourth split point after `layer4` (2048 × 7 × 7). | The three proposed splits all send more bytes than the raw frame (Section 3), so a later split is needed to locate where the payload falls below the raw frame. |
| Main finding framed as *uncompressed activations never win* rather than a split-favourable region. | Follows from the payload measurement; keeps the no-compression scope of Proposal v2 intact. |

## 2. Work completed since Proposal v2

- **Testbed implemented** ([github.com/KevinCKHo/split-computing-testbed](https://github.com/KevinCKHo/split-computing-testbed)), in Python/PyTorch, running natively on Windows and Linux:
    - model partitioner that cuts ResNet-50 after any stage; a unit test checks edge + server output equals the full model for every split point;
    - edge client and GPU inference server over TCP with a length-prefixed binary tensor format (no pickle), `TCP_NODELAY`, per-stage timing (host `perf_counter_ns`, CUDA events on the server);
    - three link-shaping back ends (app-level, Windows QoS, Linux `tc` htb + `netem`) driven from one config file and a matrix runner;
    - analysis pipeline that produces all three proposed deliverables (payload profile, crossover map, stage / tail-latency breakdown).
- **Full minimum viable matrix measured on the two-laptop testbed:** 6 configurations × 4 network profiles × (20 warm-up + 200 measured) requests = **4,800 measured requests**, logged per request.
- **Cross-check in simulation:** the same matrix on one CPU-only host over loopback, which reproduced the same ranking and the same winner in every cell.
- **Setup documented** for both Windows laptops (static IPs, firewall rule, power plan) in the repository README.

## 3. Preliminary results (two-laptop testbed)

**Payload profile (Deliverable 1).** Bytes sent per request. Activations are lossless fp32; the raw frame is uint8.

| Configuration | Edge runs | Tensor sent | Bytes | vs. raw frame |
| --- | --- | --- | ---: | ---: |
| Full offload | nothing | 3 × 224 × 224 (uint8) | 150,528 | 1.0× |
| Split A, early | stem + layer1 | 256 × 56 × 56 | 3,211,264 | 21.3× |
| Split B, mid | through layer2 | 512 × 28 × 28 | 1,605,632 | 10.7× |
| Split C, late | through layer3 | 1024 × 14 × 14 | 802,816 | 5.3× |
| Split D, layer4 | through layer4 | 2048 × 7 × 7 | 401,408 | 2.7× |
| Full local | everything | nothing | 0 | – |

**End-to-end latency, two-laptop testbed (median / p99 of 200 requests, ms).** Fastest per profile in bold.

| Configuration | 10 Mbit/s, 20 ms one-way (40 ms RTT) | 10 Mbit/s, 100 ms one-way (200 ms RTT) | 100 Mbit/s, 20 ms one-way (40 ms RTT) | 100 Mbit/s, 100 ms one-way (200 ms RTT) |
| --- | ---: | ---: | ---: | ---: |
| Full local | **46.1** / 57.8 | **37.4** / 48.3 | **37.2** / 44.9 | **37.0** / 45.6 |
| Full offload | 199.8 / 208.0 | 360.5 / 374.8 | 91.4 / 133.6 | 252.5 / 287.2 |
| Split A, early | 2,668.2 / 2,727.8 | 2,823.8 / 2,861.9 | 353.0 / 408.7 | 513.4 / 628.1 |
| Split B, mid | 1,377.8 / 1,447.6 | 1,536.6 / 1,579.7 | 221.0 / 260.5 | 383.3 / 402.8 |
| Split C, late | 735.3 / 757.4 | 896.2 / 938.9 | 156.8 / 197.7 | 318.9 / 340.2 |
| Split D, layer4 | 409.2 / 420.7 | 569.7 / 597.0 | 118.6 / 131.9 | 279.7 / 296.4 |

![Figure 1. Median latency per request by stage at 20 ms one-way delay (40 ms emulated RTT), two-laptop testbed. Panels use different scales; the 200 ms RTT profiles look the same with about 160 ms more network time. Server time is end-to-end minus edge compute and network time, so it includes serialization.](fig_stages_real.png){width=88%}

**What it shows.**

1. **No split and no offload wins any cell.** Full local inference on the Intel edge laptop (37–46 ms) is fastest in all four profiles, and the additive model (edge + server + RTT + bytes × 8 / bandwidth, from the measured medians) predicts that winner in 4 of 4 cells.
2. **Payload decides the split ranking.** Every lossless split sends 2.7–21× more bytes than the raw frame, so later splits are always faster (D < C < B < A) and none beats raw offloading.
3. **Network time dominates.** It is 82–98 % of end-to-end latency for every offloaded configuration at 10 Mbit/s and 61–90 % at 100 Mbit/s.
4. **Physical link baseline.** ICMP ping to the server timed out (Windows blocks it by default), so the physical RTT was derived from the data instead. Network time minus the emulated RTT and the shaped transfer time leaves 2.6–4.6 ms in every cell: the Wi-Fi/LAN path adds about 3–4 ms per request.
5. **No region of the studied range favours offloading with this server.** The server's own time for the full model (about 36 ms) plus any RTT of 5 ms or more already exceeds full local (37 ms), and split D's edge compute alone (40–42 ms) exceeds it too.
6. **The simulation agrees.** The single-machine run gave the same winner in every cell and the same split ranking.

**What it does not yet establish.**

- **Server speed.** About 36 ms server-side for full ResNet-50 is slower than expected for an RTX 4060, and server time falls steadily with later splits (37, 29, 18, 3 ms), which looks more like CPU execution or a low GPU power state. Until CUDA execution is confirmed, the "no offload region" result holds for this server, not for GPUs in general. With the measured 3–4 ms link baseline, offloading would need a server under about 17 ms to win at 100 Mbit/s and 5 ms RTT.
- **Real network behaviour.** App-level shaping paces bytes deterministically; it has no router queue, congestion-window growth or retransmission, so socket-buffer queuing (Deliverable 3) is not yet measured.
- **Tail latency.** p99 is within 1.1× of the median for most network-bound cells but reaches 1.46× for full offload at 100 Mbit/s / 40 ms RTT. The edge was on Wi-Fi, and with N = 200 the p99 rests on the two slowest requests, so these tails are indicative only. (In the simulation, the 95 % bootstrap interval for one p99 of 93.6 ms ran from 91.6 to 140.8 ms.)
- **Edge noise.** Full local was 46 ms in the first profile and 37 ms in the other three, which suggests warm-up or a CPU frequency ramp rather than any network effect.

## 4. Challenges, blockers and risks

| Item | Impact | Mitigation |
| --- | --- | --- |
| No `tc`/`netem` on Windows | Packet-level loss, jitter and queuing cannot be emulated natively | App-level shaper for the main matrix; Windows QoS for real TCP pacing; Ubuntu live USB on the edge for `netem` loss/jitter runs |
| Activations larger than the raw frame | The crossover map may show no split region | Reported as a finding; the added layer4 split and the pooled-vector size bound where a split could win |
| Server slower than expected (~36 ms for ResNet-50) | Offloading looks worse than it may be on a GPU | Confirm the server runs on CUDA (startup log, `nvidia-smi`), set maximum-performance GPU power, re-run the offload baselines |
| Windows QoS throttling is driver- and edition-dependent | OS-level rate limit may be ignored | Verify every rate with `iperf3` before measuring; fall back to app-level or Ubuntu |
| Laptop noise (power states, background tasks) | Inflated tails | Best-performance power plan, AC power, warm-up, background apps closed |
| One-way delay vs. RTT | Ambiguity in reporting | One convention in config, CLI, figures and text: delay is one-way, applied each way; RTT = 2 × delay + physical RTT |
| Edge on Wi-Fi; ICMP blocked | 3–4 ms path overhead and jitter; no ping baseline | Physical baseline derived from the data (§3); allow ICMP on the server and repeat key cells on a direct Ethernet cable |
| p99 from N = 200 | Unstable tail estimates | Report bootstrap intervals; raise N to 1,000 for cells used in the tail analysis |

**Open question for feedback:** the testbed now runs on Windows with app-level / QoS shaping. Is that acceptable for the final results, or should they use the Ubuntu-USB `netem` path throughout?

## 5. Remaining tasks and timeline

| Dates | Task | Exit criterion |
| --- | --- | --- |
| Nov 21–23 | Confirm CUDA on the server; re-run baselines (full local, full offload) on a direct cable with ping/`iperf3` checks | GPU-verified baselines, N = 200 |
| Nov 23 | Review checkpoint feedback; adjust scope | Plan updated |
| Nov 24–28 | Phase 2: repeat the 2 × 2 matrix with the GPU-verified server and with the Windows QoS rate limit; packet captures (Wireshark/pktmon) at 10 Mbit/s; N = 1,000 for tail cells | All 24 cells measured; traces saved |
| Nov 28–30 | Denser measurements at the bandwidth/RTT points the analysis flags on the crossover boundary (`next_measurements.csv`); optional Ubuntu-USB `netem` loss runs | Boundary bracketed by measured points |
| Nov 30 – Dec 1 | Phase 3: final payload profile, crossover map, stage and p99 analysis | Figures final |
| Dec 2 or Dec 7 | Final presentation | Slides delivered |
| Dec 8–14 | Final report | Submitted by Dec 14, 3:00 PM |

## 6. How proposal feedback was considered

| Instructor feedback on Proposal v2 | Response in this checkpoint |
| --- | --- |
| Distinguish round-trip time from one-way propagation delay and document emulation settings consistently. | One convention everywhere: a profile's delay is the **one-way** propagation delay, applied on the uplink and again on the downlink, so emulated RTT = 2 × delay; the physical link's RTT is measured in the unshaped baseline and reported separately. The config file, the client's `--delay-ms` option, the Linux path (which puts the full 2 × delay on edge egress so the RTT matches), every figure axis and every table header now state this. §1 notes that 100 ms one-way gives a 200 ms RTT, outside the question's 5–150 ms range. |
| Use the initial experiments to identify regions that need additional measurements around the crossover boundaries. | The analysis fits an additive latency model from the measured medians, checks it against every measured cell (4 of 4 winners predicted on the testbed) and writes the bandwidth/RTT points on the modelled boundary to `next_measurements.csv`. The extended sweep will sample those points instead of a uniform grid (§5). With the current server the testbed shows no boundary inside 1–100 Mbit/s × 5–150 ms (full local always wins), so the next measurements go where a boundary can appear: a GPU-verified server, at high bandwidth and low RTT. |
| Be cautious when interpreting p99 latency from a limited number of runs. | Medians are the primary statistic. The analysis now reports p99 with a 95 % bootstrap interval, and §3 labels the testbed's p99 values as indicative. Tail claims will be made only where the interval is narrow, and the cells used for the tail analysis will be re-run with N = 1,000. |
| For the checkpoint, prioritize establishing the testbed and obtaining reliable baseline measurements before expanding the experiment matrix. | The testbed is complete and unit-tested, and it now produces real baselines on the two laptops. The first follow-up is making those baselines reliable (GPU confirmed, wired link, ping baseline). The matrix was expanded by only one split point, which costs no extra setup; the extended sweep, loss runs and compression remain deferred until after the baselines and this feedback round. |

## 7. Team contributions

Individual project: all work by Chih-Kuan Ho.

## AI assistance

Substantial AI assistance (Anthropic's Claude) was used to write the testbed code, run the simulation cross-check, produce the figures and draft this report. The two-laptop measurements were run by the author. All design choices, results and text were reviewed by the author, who is responsible for the content.

## References

1. Hemminger, S. (2005). Network emulation with NetEm. *Proceedings of the Linux Kongress*, 18–24.
2. Kang, Y., Hauswald, J., Gao, C., Rovinski, A., Mudge, T., Mars, J., & Tang, L. (2017). Neurosurgeon: Collaborative intelligence between the cloud and mobile edge. *ACM SIGPLAN Notices*, 52(4), 615–629. https://doi.org/10.1145/3037697.3037698
3. Matsubara, Y., Levorato, M., & Restuccia, F. (2022). Split computing and early exiting for deep learning applications: Survey and research challenges. *ACM Computing Surveys*, 55(5), 90:1–30. https://doi.org/10.1145/3527155
4. Matsubara, Y., Yang, R., Levorato, M., & Mandt, S. (2023). SC2 benchmark: Supervised compression for split computing. *Transactions on Machine Learning Research*. https://doi.org/10.48550/arXiv.2203.08875
5. He, K., Zhang, X., Ren, S., & Sun, J. (2016). Deep residual learning for image recognition. *Proceedings of IEEE CVPR*, 770–778.
6. PyTorch and torchvision documentation (ResNet-50 pretrained weights, CUDA event timing). https://pytorch.org/docs/
7. Microsoft. New-NetQosPolicy (NetQos) documentation. https://learn.microsoft.com/powershell/module/netqos/new-netqospolicy
