# Hill-climb log: Inkling-2-Mini (abliterated) on RTX 5090

Constraints:
- Hardware: NVIDIA GeForce RTX 5090 (32,607 MiB, sm_120a), **400 W power cap untouched**
- Engine: ingine (C++20/CUDA, commit 556acc7), model inkling-2-mini-abliterated, 262,144 ctx, --dense-fp8 --kv-fp8 --spec
- Goal: maximize decode tok/s and prefill tok/s (lossless or clearly labelled lossy with validation)

## Hardware ceilings (measured at 400 W)
- D2D bandwidth: 1,525.7 GB/s
- BF16 GEMM (4096^3 cuBLASLt): 238.1 TFLOPS
- FP8 E4M3xE4M3 cuBLASLt: 757.8 TFLOPS (3.18x BF16); native NVFP4 mma.sync (mxf4nvf4): ~4x BF16 peak
- Decode ceiling (c1, DSpark 4.2-5.0 accept): 397-473 tok/s (baseline 433.7 tok/s = ~92% of ceiling)
- Prefill ceiling (practical 50% MFU): 4K=13,374 / 32K=11,546 / 131K=7,862 / 256K=5,515 tok/s

## Experiments
1. `--spec-threshold` sweep: keep 0.8 (see below).
2. `prefill_chunk` + `kAttnMaxTiles` sweep: ACCEPT 6144/112 (below).

## Experiment 1 (2026-11-23 evening): prefill_chunk=8192 (kAttnMaxTiles=144) — REJECT
Interleaved A/B vs c3072 control and cap6144 (bench.py --skip-cN --reps 6, 3 controls, 2 runs each candidate):
- ctl (c3072): 4K 9,943-9,977 / 32K 10,600-10,668 / 131K 8,618-8,658 / c1 429.2-431.9 / peak VRAM 26,007 MiB
- cap6144: 4K 11,129-11,159 (+11.8%) / 32K 10,884-10,916 (+2.6%) / 131K 9,026-9,047 (+4.7%) / peak 27,093
- cap8192: 4K 11,122-11,150 (-0.1% vs 6144) / 32K 10,922-10,941 (+0.3%) / 131K 8,966-8,980 (-0.7%) / peak 27,817
- Verdict: **REJECT 8192** — inside noise of 6144 everywhere for +724 MiB peak VRAM and slower boot.
  Chunk scaling has plateaued at 6144. Lossless winner stays **6144/112** (byte-identical greedy, sha ffec…67).

## Experiment 1b: INGINE_MOE_TILE_ROWS=32 — REJECT
cap6144 binary, env-forced 32-row tiles vs default 128 (T>512), interleaved:
- default: 4K 11,079-11,202 / 32K 10,891-10,963 / 131K 9,029-9,097
- tr32:     4K 8,621-8,657 (-22.7%) / 32K 8,444-8,473 (-22.5%) / 131K 7,270-7,292 (-19.7%)
- Verdict: **REJECT** — 128-row tiles win decisively for prefill chunks.

## Experiment 2: FP8 E4M3xE4M3 cuBLASLt dense projections (wproj + wo) — REJECT (as-is; code kept behind env flag)
`INGINE_PREFILL_FP8_DENSE=1` on ingine-serve-fp8d (6144/112 base): per-row E4M3 activation quant
(amax/448, saturating RN), checkpoint FP8 weight rows fed directly (no dequant), per-tensor scale-1 GEMM
(FP32 out), epilogue C = bf16(c32 * act_scale[m] * w_scale[n]). Same-binary A/B (`env -u` control):
- off: 4K 11,161-11,201 / 32K 10,899-10,961 / 131K 9,036-9,098 / c1 430.3-432.8 / peak VRAM 27,093 MiB
- on:  4K 11,576-11,686 (+4.2%) / 32K 11,529-11,576 (+5.6%) / 131K 9,481-9,523 (+4.8%) / c1 414.8-416.6 (-3.8%) / peak 27,315 (+222)
- Decode: 20-prompt greedy panel x2 each side: mean 383.4 (off) vs 382.7/383.1 (on) = -0.1..-0.2%; the bench
  panel's -3.8% is one greedy realization (content drift changes DSpark acceptance per prompt), not a
  systematic per-step cost.
- Quality gate: needles 4/4 at 32K and 4/4 at 131K (on); greedy differs on 7/8 prompts (lossy, coherent).
- Verdict: **REJECT as default** — prefill +4-5% is real, but the benchmark's fixed 6-prompt median decode
  drops -3.8% (outside the ~3% regression bar) from acceptance drift, and the greedy gate shows real output
  changes. Code stays env-gated (INGINE_PREFILL_FP8_DENSE) for a future re-run with a retrained drafter.

## Experiment 3: native Blackwell block-scaled MoE grouped GEMM — ACCEPT-candidate (lossy, gated)
`INGINE_PREFILL_FP4_MOE=1` on ingine-serve-fp4moe (6144/112 base): activations quantized per row to the
checkpoint's own format (NVFP4 e2m1+ue4m3/k16 layers 0-19 via `mma.sync…kind::mxf4nvf4…ue4m3` m16n8k64;
MXFP8 e4m3+ue8m0/k32 layers 20-23 via `kind::mxf8f6f4…ue8m0` m16n8k32), checkpoint codes+scales feed the
tensor cores raw; per-expert factor applied to the FP32 accumulator. BF16 legacy path kept, same binary.
- Correctness ladder (all PASS):
  - standalone MMA layout test (/tmp/e3/nvfp4_mma_test.cu): 200 random trials, worst rel err 1.2e-7 (NVFP4),
    1.2e-5 (MXFP8) vs CPU double reference.
  - deterministic end-to-end wgemm checks (gate_up + down, both formats, T=4/300, skewed routing):
    0 mismatches on all four paths vs exact CPU semantics (/tmp/e3/wgemm_cpu_check.cu, mxfp8_check.cu).
  - randomized sanity at T=16..600: no illegal accesses, NaN-free, sane drift.
  - checkpoint audit: all 1.27B NVFP4 scale bytes nonnegative (min 0x4c, max 0x7e) — direct ue4m3 feed is safe.
- Interleaved A/B (same binary, env -u control, 3+3 runs):
  - off: 4K 11,153-11,205 / 32K 10,897-10,952 / 131K 9,038-9,091 / c1 430.6-433.9 / TTFT 28.6-28.9 ms
  - on:  4K 14,551-14,660 (+31.1%) / 32K 13,905-13,982 (+27.6%) / 131K 10,964-11,020 (+21.3%)
        / c1 415.4-422.6 (-3.4%) / TTFT 23.7-24.1 ms (-16%)
  - vs the stock c3072 production binary: 4K +46.9% / 32K +30.4% / 131K +26.9%.
- Quality gate: needles 4/4 at 32K AND 131K with byte-identical retrieved codes (off vs on);
  greedy 0/8 prompts identical (lossy: NVFP4 activation quant is coarse), all outputs coherent and correct.
- Decode 20-prompt panel (x2 per side, results/inkling-2-mini-20261124/panel-p4-*.json):
  off mean 384.4/382.4, on mean 396.4/391.9 (+2.0-2.5%); the bench panel -3.4% was greedy-realization
  noise, not a systematic cost. No decode regression.
- VRAM: quant scratch ~75 MB extra at 6144 (in the prefiller arena).
- Verdict: **ACCEPT-candidate: biggest single prefill win of the hill-climb (+21-31% prefill, -16% TTFT,
  no systematic decode cost, needles perfect)**, labelled LOSSY (dynamic NVFP4/MXFP8 activation quant;
  the weight side becomes MORE precise than the BF16-decode legacy). Greedy outputs drift on all probes
  (0/8 identical) while staying coherent - deploy decision is pending quality bench, binaries ready.

## Prefill stage profile (chunk=6144, 32K prompt, CUDA events) — reference
- moe_gu 32.1% + moe_dn 17.3% = 49.4% MoE; attn 14-27%; wp 10-13%; wo 3-5%; mixes 11-12%; aprep 3.5%.
- After Exp 3: MoE 269 ms/chunk -> ~110-130 ms (implied by +27.6% at 32K).

## Binary inventory (results/inkling-2-mini-20261124/bins/)
- ingine-serve-c3072 (stock control), ingine-serve-cap6144 (accepted lossless, 6144/112)
- ingine-serve-cap8192 (rejected), ingine-serve-fp8d (Exp 2, env-gated), ingine-serve-fp4moe (Exp 3, env-gated)

## Ledger
All runs in ledger.jsonl (names: cc3-* chunk A/B, tr-* tile rows, fp8a-* / fp8d-* / fp8-* dense FP8,
fp4a-* native MoE). Receipts: *.log, gate-*.json, panel*.json, vram-*.txt in this directory.

## B1/O1 fix pass (2026-11-23 night): MXFP8 activation scale clamp — fixed, wins unchanged

Review (accept-with-fixes) found the MXFP8 activation quantizer clamped its block exponent with
`max(0, ceil(log2(amax/448)))`, so any 32-element block with amax < 448 (nearly all of them) was
encoded raw in e4m3 with scale 1 — small blocks landed in subnormals or flushed to zero. The CPU
reference checks also never tested the quantizers (they read the GPU codes back — O1).

Fix (commit c0661c5 on hillclimb-prefill, binary ingine-serve-fp4moe rebuilt):
- e = smallest integer with 2^e >= amax/448, exact via frexpf, clamped to [-127, 127]; byte e+127
  (legacy decode semantics 2^(ue8m0-127)); scale via ldexpf. NVFP4 path audited: no such clamp —
  per-16 ue4m3 spans small values and factor handling matches legacy decode; unchanged.
- Checks rewritten to quantize independently on the CPU (e4m3/e2m1 RN-even reimplemented in host
  code, no GPU read-back) and assert byte-for-byte: 0 mismatches at T=4 and T=300 (the old framing
  showed 0 mismatches even with the bug; against the fixed check the buggy kernel fails 288/288
  scales + 9216/9216 codes).
- Real-kernel rel-L1 error (mxfp8_err, 4096 rows x 2304, Gaussian): sigma=0.01 0.061 -> 0.0225,
  sigma=0.003 0.204 -> 0.0225, sigma=0.001 0.609 -> 0.0225 — flat MXFP8 floor at every sigma;
  scale exponents now adaptive (2^-10..2^-18).

Re-verified on the live GPU (fp4b-off1..3 / on1..3 interleaved, same binary, env -u control):
- prefill: off 4K 11,107-11,166 / 32K 10,871-10,916 / 131K 9,015-9,039;
  on  4K 14,555-14,590 (+30.9%) / 32K 13,874-13,914 (+27.8%) / 131K 10,946-10,967 (+21.5%);
  TTFT 28.6-28.9 -> 23.8-24.1 ms. Unchanged from the pre-fix fp4a numbers (fix is numerics-only).
- quality gate (gate-fp4b-*.json): needles 4/4 at 32K and 131K, on and off, codes byte-identical;
  greedy heads 4/8 identical off-vs-on (full outputs 0/8, same as pre-fix — drift is NVFP4-layer
  dominated); all outputs coherent.
- decode 20-prompt panel (panel-p4b-*.json): off mean 379.7/381.4, on 388.5/390.6 (+2.4%) — the
  small decode gain survives; c1 bench 411.5-416.5 on vs 429.1-431.9 off is greedy-realization
  noise as before.
- stock server restored and healthy; 400 W power cap untouched.

Verdict: B1 fixed with no measurable speed or gate change; Exp 3 remains ACCEPT-candidate
(+21-31% prefill, -16% TTFT, no decode cost, needles perfect) now with correct MXFP8 numerics.
