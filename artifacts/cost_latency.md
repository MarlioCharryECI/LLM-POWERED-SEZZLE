# Latency & cost characteristics

Machine: RTX 3050 6GB VRAM / 13.7GB RAM. Model: qwen2.5:7b (Q4_K_M), local Ollama.
Cases timed: 10 (after warm-up).

## Per-request wall-clock (seconds)
- p50 total: 14.8s
- p95 total: 20.1s
- mean total: 14.5s

## Per-stage (ms)
- router  p50 3626  p95 3780
- answer  p50 11128  p95 16394
- calls/case: 1 (policy/escalate) or 2 (tool/both)

## Reading against the production budget (100k/day, $50/day, p95<=3s)
- Local p95 is well above 3s: a 7B on a 6GB laptop is NOT the production
  answer. The DESIGN meets the budget; the local model is the $0 dev stand-in.
- Structure that makes the budget reachable on a hosted small model:
  * ~2k-token policy prefix is CACHEABLE -> most input tokens are cache reads.
  * routing gates the 2nd call: ~half of traffic (policy/escalate) is 1 call.
  * all date/money math is deterministic (no extra model calls).
- Order-of-magnitude paid estimate (hosted small model, e.g. Haiku-class):
  ~3.5k in + ~0.3k out per call, ~1.5 calls/q avg, 100k q/day
  ~= 525M in + 45M out tokens/day; with a cached prefix the effective input
  cost is far lower. At cents-per-Mtok that lands in the ~$50/day ballpark,
  and p95<=3s is achievable with a hosted model + prompt caching + the
  single-extra-call ceiling. Trade to pull cost down further: smaller model
  for routing, or fold router+answer into one call for policy/escalate.

