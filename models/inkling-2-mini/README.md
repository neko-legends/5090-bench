# Inkling-2-Mini (abliterated) on RTX 5090 — Production Recipe

**Status:** 🟢 **live** since 2026-11-24
**Engine:** [`satellitedown/inkling-2-mini-abliterated-ingine`](https://github.com/satellitedown/inkling-2-mini-abliterated-ingine) (commit `556acc7` + lossless patch `0001`)
**Hardware:** Single NVIDIA GeForce RTX 5090 (32 GB, `sm_120a`), **400 W power cap**

## Headline numbers (400 W cap, 262,144 context)

| Metric | Stock (`chunk=3072`) | **Shipped (`chunk=6144` / `tiles=112`)** | Delta |
|---|---:|---:|---:|
| **Decode c1 (speculative)** | 430.9 tok/s (n=14) | **431.3 tok/s** (n=15) | +0.1% (unchanged, ~92% of ceiling) |
| **Short TTFT** | 28.9 ms | **28.9 ms** | unchanged |
| **Cold prefill @ 4K (3,302 tok)** | 9,955 tok/s | **11,154 tok/s** | **+12.0%** |
| **Cold prefill @ 32K (25,554 tok)** | 10,645 tok/s | **10,911 tok/s** | **+2.5%** |
| **Cold prefill @ 131K (102,557 tok)** | 8,648 tok/s | **9,049 tok/s** | **+4.6%** |
| **Greedy output equivalence** | baseline | **byte-identical** (`sha256=fcec56817bbcbc67`) | **lossless** |
| **VRAM resident** | 25,151 MiB | **26,237 MiB** | +1,086 MiB (~5.5 GiB free) |
| **Private vision (37-item bench)** | 97.3% (36/37) @ 0.33 s | **97.3% (36/37) @ 0.33 s** | unchanged |

## How to build & run the shipped config

```bash
git clone https://github.com/satellitedown/inkling-2-mini-abliterated-ingine.git
cd inkling-2-mini-abliterated-ingine
git checkout 556acc7

# Apply ONLY the lossless win (do NOT enable FP4 MoE in production)
git apply /path/to/5090-bench/models/inkling-2-mini/patches/0001-prefill-accept-prefill_chunk-6144-kAttnMaxTiles-112-.patch

# Build for Blackwell sm_120a
cmake -S native -B native/build-install -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CUDA_ARCHITECTURES=120a
cmake --build native/build-install --target ingine-serve -j "$(nproc)"
```

Serve with the flags in [`configs/serving-profile.json`](configs/serving-profile.json) and [`configs/ingine.env.example`](configs/ingine.env.example):

```bash
ingine-serve --engine \
  --model-dir models/Inkling-2-Mini \
  --ablation models/Inkling-2-Mini/inkling-2-mini-abliterated.safetensors \
  --model-id inkling-2-mini-abliterated \
  --host 127.0.0.1 --port 8003 \
  --max-ctx 262144 \
  --dense-fp8 --kv-fp8 --spec --spec-threshold 0.8
```

## What we tested and rejected (and why)

All 59 interleaved runs are logged in [`results/inkling-2-mini-20261124/ledger.jsonl`](../../results/inkling-2-mini-20261124/ledger.jsonl) and narrated in [`JOURNAL.md`](JOURNAL.md):

1. **Native Blackwell FP4/MXFP8 MoE prefill (`patches/0002` + `0003`, `INGINE_PREFILL_FP4_MOE=1`) — REJECTED ON QUALITY.**
   - Speed was dramatic: **14,593 / 13,918 / 10,974 tok/s** at 4K / 32K / 131K (**+46.6% / +30.7% / +26.9%** over stock), TTFT 28.9 → 23.9 ms, and it passed 4/4 needle-in-a-haystack checks at 131K.
   - **Why it stays OFF:** On our real multi-role agent benchmark (2 runs/cell, temp 0), **Builder dropped 66.7% → 33.3%** and **Reviewer dropped 100% → 66.7%** — four extra cells looped to the 65,536-token cap and returned empty content. Passing needle-in-a-haystack was not enough; real agentic work caught the regression.
2. **FP8 dense prefill (`INGINE_PREFILL_FP8_DENSE=1`) — REJECTED AS DEFAULT.** +4–5% prefill, −3.8% c1 bench decode drift, lossy greedy output.
3. **`prefill_chunk=8192 / kAttnMaxTiles=144` — REJECTED.** Within noise of 6144 (−0.1% at 4K, −0.7% at 131K) for +724 MiB extra VRAM.
4. **`--spec-threshold` sweep (`0.0`, `0.5`, `0.9`) — REJECTED.** Default `0.8` won every interleaved A/B (`0.5` = −8.7%, `0.0` = −28.5%, `0.9` = −1.4%).
5. **`INGINE_MOE_TILE_ROWS=32` — REJECTED.** −20% to −23% prefill across all prompt sizes.
6. **Multi-GPU 5090 + 3090 P2P — RULED OUT.** `ingine` is single-GPU Blackwell-only (`sm_120a`), the 3090 is Ampere (`sm_86`), and splitting a 20 GB model across mismatched cards is slower than running on the 5090 alone.
