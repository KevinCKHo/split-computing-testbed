#!/usr/bin/env bash
# Apply or clear an emulated uplink on the edge client's egress interface.
#   sudo scripts/netem.sh apply <iface> <rate_mbit> <one_way_delay_ms> [loss_pct] [jitter_ms]
#   sudo scripts/netem.sh clear <iface>
#   scripts/netem.sh show  <iface>
# Rate limiting uses an HTB class with netem as its child, so queueing happens at the
# shaped rate and delay/loss are applied on top. Only egress (edge -> server) is shaped.
# The server runs Windows (no tc), so all emulated delay lives here: for one request and
# one response, putting the full added RTT on the uplink gives the same end-to-end latency
# as splitting it across both directions. Pass delay = target RTT - measured base RTT.
set -euo pipefail
cmd=${1:?apply|clear|show}; iface=${2:?interface}

case "$cmd" in
  apply)
    rate=${3:?rate_mbit}; delay=${4:?delay_ms}; loss=${5:-0}; jitter=${6:-0}
    tc qdisc del dev "$iface" root 2>/dev/null || true
    tc qdisc add dev "$iface" root handle 1: htb default 10
    tc class add dev "$iface" parent 1: classid 1:10 htb rate "${rate}mbit" ceil "${rate}mbit"
    netem_args="delay ${delay}ms"
    [[ "$jitter" != 0 ]] && netem_args+=" ${jitter}ms distribution normal"
    [[ "$loss" != 0 ]] && netem_args+=" loss ${loss}%"
    # limit sized so the netem queue never drops at the shaped rate
    tc qdisc add dev "$iface" parent 1:10 handle 10: netem $netem_args limit 10000
    tc -s qdisc show dev "$iface"
    ;;
  clear) tc qdisc del dev "$iface" root 2>/dev/null || true; echo "cleared $iface" ;;
  show)  tc -s qdisc show dev "$iface"; tc -s class show dev "$iface" ;;
  *) echo "unknown command $cmd" >&2; exit 1 ;;
esac
