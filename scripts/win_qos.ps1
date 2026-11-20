<#
OS-level uplink rate limit on Windows (built-in policy-based QoS, no extra install).
Run in an elevated PowerShell on the EDGE laptop. Throttles outbound TCP to the server port,
so real TCP behaviour (cwnd, socket-buffer queueing) shows up, unlike the app-level shaper.
Windows has no built-in delay or loss emulation: combine this with the client's --delay-ms
(run_matrix.py --shaper qos does that), or use clumsy for loss and jitter.

  .\scripts\win_qos.ps1 -RateMbit 10          # apply
  .\scripts\win_qos.ps1 -Clear                # remove
  Get-NetQosPolicy -Name splitbench           # inspect
Verify the rate with iperf3 before measuring: some drivers or Windows editions ignore throttling.
#>
param([double]$RateMbit = 0, [int]$Port = 50051, [switch]$Clear)
$ErrorActionPreference = "Stop"
Get-NetQosPolicy -Name splitbench -ErrorAction SilentlyContinue | Remove-NetQosPolicy -Confirm:$false
if ($Clear) { Write-Host "cleared splitbench QoS policy"; exit 0 }
if ($RateMbit -le 0) { throw "give -RateMbit > 0 or -Clear" }
$bps = [uint64]($RateMbit * 1e6)
New-NetQosPolicy -Name splitbench -IPProtocolMatchCondition TCP -IPDstPortMatchCondition $Port `
    -ThrottleRateActionBitsPerSecond $bps -PolicyStore ActiveStore | Out-Null
Get-NetQosPolicy -Name splitbench -PolicyStore ActiveStore
