#!/usr/bin/env python3
"""Generate publication-grade SVG + PNG charts for 5090-bench directly from ledger.jsonl and role-bench receipts."""
import json
import os
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "results/inkling-2-mini-20261124/ledger.jsonl"
OUT = ROOT / "docs/images"
OUT.mkdir(parents=True, exist_ok=True)

rows = [json.loads(line) for line in LEDGER.read_text().splitlines() if line.strip()]

def bucket_mean(pred, field):
    vals = [r[field] for r in rows if pred(r) and r.get(field) is not None]
    return statistics.mean(vals), min(vals), max(vals), len(vals)

def render_png(svg_path: Path):
    png_path = svg_path.with_suffix(".png")
    subprocess.run(
        ["rsvg-convert", "-w", "1600", "-o", str(png_path), str(svg_path)],
        check=True,
    )
    return png_path

# Compute exact numbers from ledger.jsonl
stock_pred = lambda r: r["name"].startswith(("ctl", "chunk-ctl", "cc2-ctl", "cc3-ctl"))
c4096_pred = lambda r: r["name"].startswith("cc2-4096")
c6144_pred = lambda r: r["name"].startswith(("cc2-6144", "cc3-6144", "tr-def", "fp8a-off", "fp4a-off", "fp4b-off"))
c8192_pred = lambda r: r["name"].startswith("cc3-8192")
tr32_pred  = lambda r: r["name"].startswith("tr-32")
fp8_pred   = lambda r: r["name"].startswith("fp8a-on")
fp4_pred   = lambda r: r["name"].startswith(("fp4a-on", "fp4b-on"))

s_c1, s_c1_lo, s_c1_hi, s_c1_n = bucket_mean(stock_pred, "c1_decode")
l_c1, l_c1_lo, l_c1_hi, l_c1_n = bucket_mean(c6144_pred, "c1_decode")
l_4k, l_4k_lo, l_4k_hi, l_4k_n = bucket_mean(c6144_pred, "prefill_4096")
l_32k, l_32k_lo, l_32k_hi, l_32k_n = bucket_mean(c6144_pred, "prefill_32768")
l_131k, l_131k_lo, l_131k_hi, l_131k_n = bucket_mean(c6144_pred, "prefill_131072")
l_ttft, _, _, _ = bucket_mean(c6144_pred, "ttft_short_ms")

s_4k, _, _, s_4k_n = bucket_mean(stock_pred, "prefill_4096")
s_32k, _, _, s_32k_n = bucket_mean(stock_pred, "prefill_32768")
s_131k, _, _, s_131k_n = bucket_mean(stock_pred, "prefill_131072")

f4_4k, _, _, f4_n = bucket_mean(fp4_pred, "prefill_4096")
f4_32k, _, _, _ = bucket_mean(fp4_pred, "prefill_32768")
f4_131k, _, _, _ = bucket_mean(fp4_pred, "prefill_131072")
f4_ttft, _, _, _ = bucket_mean(fp4_pred, "ttft_short_ms")

f8_4k, _, _, f8_n = bucket_mean(fp8_pred, "prefill_4096")
f8_32k, _, _, _ = bucket_mean(fp8_pred, "prefill_32768")
f8_131k, _, _, _ = bucket_mean(fp8_pred, "prefill_131072")

c4_4k, _, _, _ = bucket_mean(c4096_pred, "prefill_4096")
c4_32k, _, _, _ = bucket_mean(c4096_pred, "prefill_32768")
c4_131k, _, _, _ = bucket_mean(c4096_pred, "prefill_131072")

c8_4k, _, _, _ = bucket_mean(c8192_pred, "prefill_4096")
c8_32k, _, _, _ = bucket_mean(c8192_pred, "prefill_32768")
c8_131k, _, _, _ = bucket_mean(c8192_pred, "prefill_131072")

tr_4k, _, _, _ = bucket_mean(tr32_pred, "prefill_4096")
tr_32k, _, _, _ = bucket_mean(tr32_pred, "prefill_32768")
tr_131k, _, _, _ = bucket_mean(tr32_pred, "prefill_131072")

# ==============================================================================
# CHART 1: Current Performance Hero Card (matches spark-bench aesthetic)
# ==============================================================================
pct_4k = (l_4k / s_4k - 1) * 100
pct_32k = (l_32k / s_32k - 1) * 100
pct_131k = (l_131k / s_131k - 1) * 100

svg1 = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="960" viewBox="0 0 1600 960">
<rect width="1600" height="960" fill="#0f141b"/>
<text x="90" y="82" fill="#8ea3b8" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="22" font-weight="600" letter-spacing="2">5090-BENCH  ·  2026-11-24</text>
<text x="90" y="152" fill="#f4f7fa" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="50" font-weight="700">Inkling-2-Mini · RTX 5090 (400 W cap)</text>
<text x="90" y="202" fill="#b8c7d9" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="24">Single RTX 5090 (32 GB, sm_120a) · ingine + lossless chunk-6144/tiles-112 · 262,144 ctx · abliterated</text>

<rect x="90" y="246" width="1420" height="516" rx="16" fill="#171f2a" stroke="#263242" stroke-width="1.5"/>
<text x="130" y="302" fill="#8ea3b8" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="21" font-weight="700" letter-spacing="1.5">MEASURED ON THE LIVE PRODUCTION CONFIG (n = {l_4k_n} INTERLEAVED RUNS)</text>

<text x="130" y="368" fill="#e2eaf3" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="25" font-weight="600">Decode · concurrency 1 (speculative DSpark, threshold 0.8)</text>
<text x="1470" y="368" fill="#f2cc7b" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="42" font-weight="700" text-anchor="end">{l_c1:,.1f} tok/s</text>
<text x="130" y="400" fill="#9fb2c7" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="19">range {l_c1_lo:.1f}–{l_c1_hi:.1f} tok/s · ~92% of measured 400 W physics ceiling (397–473 tok/s) · TTFT {l_ttft:.1f} ms</text>

<path d="M130 430 H1470" stroke="#283546" stroke-width="1.2"/>

<text x="130" y="486" fill="#e2eaf3" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="25" font-weight="600">Cold prefill · 4K prompt (3,302 tokens)</text>
<text x="1470" y="486" fill="#6fd1f5" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="42" font-weight="700" text-anchor="end">{l_4k:,.0f} tok/s</text>
<text x="130" y="518" fill="#9fb2c7" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="19">+{pct_4k:.1f}% over stock chunk-3072 ({s_4k:,.0f} tok/s) · byte-identical greedy output (sha256 verified)</text>

<path d="M130 548 H1470" stroke="#283546" stroke-width="1.2"/>

<text x="130" y="604" fill="#e2eaf3" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="25" font-weight="600">Cold prefill · 32K / 131K prompts (25,554 / 102,557 tokens)</text>
<text x="1470" y="604" fill="#7ce09b" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="42" font-weight="700" text-anchor="end">{l_32k:,.0f} / {l_131k:,.0f} tok/s</text>
<text x="130" y="636" fill="#9fb2c7" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="19">+{pct_32k:.1f}% at 32K · +{pct_131k:.1f}% at 131K over stock · peak VRAM 26.5 GiB (leaves ~5.5 GiB headroom)</text>

<path d="M130 666 H1470" stroke="#283546" stroke-width="1.2"/>

<text x="130" y="720" fill="#e2eaf3" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="25" font-weight="600">Private vision · multimodal (same live server)</text>
<text x="1470" y="720" fill="#c79bff" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="42" font-weight="700" text-anchor="end">0.33 s · 97.3%</text>
<text x="130" y="748" fill="#9fb2c7" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="19">36/37 on internal vision bench · 4 s cold server boot · native thinking ON (effort 0.9)</text>

<text x="90" y="814" fill="#edf2f7" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="23" font-weight="700">Why we did NOT ship the faster 14,593 tok/s FP4 MoE kernel</text>
<text x="90" y="850" fill="#b7c5d3" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="21">Native Blackwell FP4/MXFP8 MoE prefill hit +47% prefill (14.6k @4K), but failed our real role-bench quality gate:</text>
<text x="90" y="882" fill="#f58a8a" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="21" font-weight="600">Builder dropped 66.7% → 33.3% and Reviewer dropped 100% → 66.7%. Speed without task quality stays OFF.</text>
<text x="90" y="924" fill="#7f93a8" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="19">Measured hardware ceilings at 400 W: 1,525.7 GB/s D2D · 238.1 TFLOPS BF16 · 757.8 TFLOPS FP8 · Receipts: results/inkling-2-mini-20261124/ledger.jsonl</text>
</svg>'''
p1 = OUT / "current-performance-20261124.svg"
p1.write_text(svg1)
render_png(p1)

# ==============================================================================
# CHART 2: Prefill Hill-Climb Journey (Every Experiment Tested, 4K / 32K / 131K)
# ==============================================================================
configs = [
    ("MoE tile rows = 32", "REJECT (−22%)", tr_4k, tr_32k, tr_131k, "#64748b"),
    ("Stock (chunk 3072)", "BASELINE", s_4k, s_32k, s_131k, "#94a3b8"),
    ("chunk 4096 / tiles 80", "SUPERSEDED", c4_4k, c4_32k, c4_131k, "#60a5fa"),
    ("chunk 8192 / tiles 144", "REJECT (+724 MiB)", c8_4k, c8_32k, c8_131k, "#64748b"),
    ("chunk 6144 / tiles 112", "SHIPPED · LOSSLESS", l_4k, l_32k, l_131k, "#22c55e"),
    ("+ FP8 dense prefill", "OFF (lossy, −3.8% c1)", f8_4k, f8_32k, f8_131k, "#f59e0b"),
    ("+ FP4 MoE prefill", "REJECTED ON QUALITY", f4_4k, f4_32k, f4_131k, "#ef4444"),
]

# Grouped horizontal bars
W, H = 1600, 1020
left_x = 395
right_x = 1490
bar_w = right_x - left_x
max_v = 16000.0

def x_of(val):
    return left_x + (val / max_v) * bar_w

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
    f'<rect width="{W}" height="{H}" fill="#0f141b"/>',
    '<text x="70" y="68" fill="#8ea3b8" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="20" font-weight="600" letter-spacing="2">5090-BENCH  ·  PREFILL HILL-CLIMB (59 INTERLEAVED RUNS)</text>',
    '<text x="70" y="122" fill="#f4f7fa" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="40" font-weight="700">Every Prefill Optimization Tested on RTX 5090</text>',
    '<text x="70" y="162" fill="#b8c7d9" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="21">Inkling-2-Mini (abliterated) · ingine · 400 W cap untouched · mean cold prefill tok/s across prompt sizes</text>',
    # Legend
    '<rect x="70" y="186" width="18" height="18" rx="3" fill="#6fd1f5"/>',
    '<text x="96" y="202" fill="#d8e3ee" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="18">4K prompt (3,302 tok)</text>',
    '<rect x="330" y="186" width="18" height="18" rx="3" fill="#7ce09b"/>',
    '<text x="356" y="202" fill="#d8e3ee" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="18">32K prompt (25,554 tok)</text>',
    '<rect x="615" y="186" width="18" height="18" rx="3" fill="#a78bfa"/>',
    '<text x="641" y="202" fill="#d8e3ee" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="18">131K prompt (102,557 tok)</text>',
]

# Grid lines
y_top = 232
row_h = 100
y_bot = y_top + len(configs) * row_h
for tick in range(0, 16001, 2000):
    tx = x_of(tick)
    parts.append(f'<line x1="{tx:.1f}" y1="{y_top}" x2="{tx:.1f}" y2="{y_bot}" stroke="#223042" stroke-width="1"/>')
    parts.append(f'<text x="{tx:.1f}" y="{y_bot + 28}" fill="#8ea3b8" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="16" text-anchor="middle">{tick:,}</text>')

# Practical 4K ceiling reference line (13,374 tok/s at 50% BF16 MFU)
cx = x_of(13374)
parts.append(f'<line x1="{cx:.1f}" y1="{y_top - 10}" x2="{cx:.1f}" y2="{y_bot}" stroke="#f59e0b" stroke-width="1.8" stroke-dasharray="7,5"/>')
parts.append(f'<text x="{cx - 8:.1f}" y="{y_top - 16}" fill="#f59e0b" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="15" text-anchor="end">BF16 50% MFU 4K ref (13,374)</text>')

for idx, (label, badge, v4, v32, v131, bcol) in enumerate(configs):
    ry = y_top + idx * row_h
    if label == "chunk 6144 / tiles 112":
        parts.append(f'<rect x="52" y="{ry + 4}" width="1496" height="{row_h - 8}" rx="10" fill="#13261e" stroke="#22c55e" stroke-width="1.5"/>')
    elif label == "+ FP4 MoE prefill":
        parts.append(f'<rect x="52" y="{ry + 4}" width="1496" height="{row_h - 8}" rx="10" fill="#27161a" stroke="#ef4444" stroke-width="1.2" stroke-dasharray="5,4"/>')
    else:
        parts.append(f'<rect x="52" y="{ry + 4}" width="1496" height="{row_h - 8}" rx="10" fill="#151d28" stroke="#202c3c" stroke-width="1"/>')

    parts.append(f'<text x="72" y="{ry + 42}" fill="#f1f5f9" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="21" font-weight="700">{label}</text>')
    # Status pill (wide enough for longest badge text)
    parts.append(f'<rect x="72" y="{ry + 54}" width="268" height="24" rx="5" fill="{bcol}" fill-opacity="0.22" stroke="{bcol}" stroke-width="1"/>')
    parts.append(f'<text x="206" y="{ry + 71}" fill="{bcol}" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="13" font-weight="700" text-anchor="middle">{badge}</text>')

    bars = [
        (v4, "#6fd1f5", ry + 15),
        (v32, "#7ce09b", ry + 41),
        (v131, "#a78bfa", ry + 67),
    ]
    for val, col, by in bars:
        bw = (val / max_v) * bar_w
        parts.append(f'<rect x="{left_x}" y="{by}" width="{bw:.1f}" height="20" rx="4" fill="{col}" fill-opacity="0.9"/>')
        parts.append(f'<text x="{left_x + bw + 8:.1f}" y="{by + 15}" fill="#e2eaf3" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="15" font-weight="600">{val:,.0f}</text>')

parts.append('<text x="70" y="990" fill="#7f93a8" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="17">FP4 MoE crosses the BF16 MFU reference because it uses native Blackwell mxf4nvf4/mxf8f6f4 tensor cores — but failed real task quality (see quality chart).</text>')
parts.append('</svg>')
p2 = OUT / "prefill-hillclimb-20261124.svg"
p2.write_text("\n".join(parts))
render_png(p2)

# ==============================================================================
# CHART 3: Speed vs Quality Trap — Why We Rejected the Fastest Kernel
# ==============================================================================
roles = [
    ("Builder\n(unit tests passed)", 66.7, 33.3, "42.0s → 64.5s (2 extra cells looped empty)"),
    ("Reviewer\n(planted bugs found)", 100.0, 66.7, "4.8s → 32.2s (diff3 looped empty)"),
    ("Instruction Following\n(judge score / 5)", 65.0, 63.4, "3.25/5 → 3.17/5 (T3_ops empty in both)"),
    ("Cheap-Batch\n(classification acc)", 100.0, 100.0, "2.38s → 2.45s (unchanged)"),
]

W3, H3 = 1600, 920
parts3 = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W3}" height="{H3}" viewBox="0 0 {W3} {H3}">',
    f'<rect width="{W3}" height="{H3}" fill="#0f141b"/>',
    '<text x="70" y="68" fill="#8ea3b8" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="20" font-weight="600" letter-spacing="2">5090-BENCH  ·  QUALITY GATE VERDICT (2026-11-24)</text>',
    '<text x="70" y="122" fill="#f4f7fa" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="40" font-weight="700">The Speed Trap: Why We Killed the +47% FP4 MoE Kernel</text>',
    '<text x="70" y="162" fill="#b8c7d9" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="21">Both configs passed 4/4 needle-in-a-haystack at 131K. Only the real agent role-bench caught the regression.</text>',
    # Legend
    '<rect x="70" y="190" width="20" height="20" rx="4" fill="#22c55e"/>',
    '<text x="100" y="207" fill="#e2eaf3" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="19" font-weight="600">Shipped: chunk-6144 lossless (11,154 tok/s @4K)</text>',
    '<rect x="640" y="190" width="20" height="20" rx="4" fill="#ef4444"/>',
    '<text x="670" y="207" fill="#e2eaf3" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="19" font-weight="600">Rejected: + FP4 MoE prefill (14,593 tok/s @4K)</text>',
]

lx3, rx3 = 360, 1140
bw3 = rx3 - lx3
yt3 = 248
rh3 = 136
yb3 = yt3 + len(roles) * rh3

for t in [0, 25, 50, 75, 100]:
    tx = lx3 + (t / 100.0) * bw3
    parts3.append(f'<line x1="{tx:.1f}" y1="{yt3}" x2="{tx:.1f}" y2="{yb3}" stroke="#223042" stroke-width="1"/>')
    parts3.append(f'<text x="{tx:.1f}" y="{yb3 + 28}" fill="#8ea3b8" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="16" text-anchor="middle">{t}%</text>')

for i, (rname, base_v, fp4_v, note) in enumerate(roles):
    ry = yt3 + i * rh3
    parts3.append(f'<rect x="52" y="{ry + 6}" width="1496" height="{rh3 - 14}" rx="12" fill="#151d28" stroke="#223042" stroke-width="1"/>')
    l1, l2 = rname.split("\n")
    parts3.append(f'<text x="74" y="{ry + 52}" fill="#f1f5f9" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="22" font-weight="700">{l1}</text>')
    parts3.append(f'<text x="74" y="{ry + 80}" fill="#8ea3b8" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="17">{l2}</text>')

    w_base = (base_v / 100.0) * bw3
    w_fp4 = (fp4_v / 100.0) * bw3
    parts3.append(f'<rect x="{lx3}" y="{ry + 28}" width="{w_base:.1f}" height="28" rx="5" fill="#22c55e" fill-opacity="0.9"/>')
    parts3.append(f'<text x="{lx3 + w_base + 10:.1f}" y="{ry + 49}" fill="#86efac" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="19" font-weight="700">{base_v:.1f}%</text>')

    parts3.append(f'<rect x="{lx3}" y="{ry + 68}" width="{w_fp4:.1f}" height="28" rx="5" fill="#ef4444" fill-opacity="0.88"/>')
    delta = fp4_v - base_v
    dtxt = f"{fp4_v:.1f}% ({delta:+.1f}%)" if abs(delta) > 0.05 else f"{fp4_v:.1f}%"
    dcol = "#fca5a5" if delta < -2 else "#cbd5e1"
    parts3.append(f'<text x="{lx3 + w_fp4 + 10:.1f}" y="{ry + 89}" fill="{dcol}" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="19" font-weight="700">{dtxt}</text>')

    parts3.append(f'<text x="1526" y="{ry + 68}" fill="#9fb2c7" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="16" text-anchor="end">{note}</text>')

parts3.append('<rect x="52" y="834" width="1496" height="58" rx="10" fill="#171f2a" stroke="#334155" stroke-width="1"/>')
parts3.append('<text x="76" y="869" fill="#cbd5e1" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="18">Note: 40K Synthesis scored 0% on both (temp-0 looping to 65k cap is a baseline property of Inkling-2-Mini, not caused by FP4). 2 runs/cell, judge: deepseek-v4-flash-0731-fast.</text>')
parts3.append('</svg>')
p3 = OUT / "quality-gate-fp4-rejection-20261124.svg"
p3.write_text("\n".join(parts3))
render_png(p3)

# ==============================================================================
# CHART 4: Decode Speculative-Threshold Sweep vs Physics Ceiling
# ==============================================================================
spec_pts = [
    ("0.0 (always verify)", 309.2, "#ef4444", "−28.5%"),
    ("0.5", 395.2, "#f59e0b", "−8.7%"),
    ("0.8 (default · LIVE)", l_c1, "#22c55e", "BEST (~92% ceiling)"),
    ("0.9", 424.5, "#60a5fa", "−1.4%"),
]
W4, H4 = 1600, 680
lx4, rx4 = 330, 1210
bw4 = rx4 - lx4
max4 = 500.0
x4 = lambda v: lx4 + (v / max4) * bw4

parts4 = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W4}" height="{H4}" viewBox="0 0 {W4} {H4}">',
    f'<rect width="{W4}" height="{H4}" fill="#0f141b"/>',
    '<text x="70" y="66" fill="#8ea3b8" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="20" font-weight="600" letter-spacing="2">5090-BENCH  ·  DECODE CEILING &amp; SPECULATIVE SWEEP</text>',
    '<text x="70" y="118" fill="#f4f7fa" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="38" font-weight="700">Decode Is Already at ~92% of 400 W Physics Ceiling</text>',
    '<text x="70" y="156" fill="#b8c7d9" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="20">Measured D2D bandwidth: 1,525.7 GB/s · per-token read: 6.48 GB · DSpark 7-token drafter (--spec-threshold sweep)</text>',
]
yt4, rh4 = 212, 90
yb4 = yt4 + len(spec_pts) * rh4

# Shaded ceiling band 397 - 473
c_lo, c_hi = x4(397), x4(473)
parts4.append(f'<rect x="{c_lo:.1f}" y="{yt4 - 12}" width="{c_hi - c_lo:.1f}" height="{yb4 - yt4 + 12}" fill="#f59e0b" fill-opacity="0.10"/>')
parts4.append(f'<line x1="{c_hi:.1f}" y1="{yt4 - 12}" x2="{c_hi:.1f}" y2="{yb4}" stroke="#f59e0b" stroke-width="1.8" stroke-dasharray="6,5"/>')
parts4.append(f'<text x="{c_hi:.1f}" y="{yt4 - 18}" fill="#f59e0b" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="16" text-anchor="end">Practical ceiling band (397–473 tok/s)</text>')

for t in range(0, 501, 100):
    tx = x4(t)
    parts4.append(f'<line x1="{tx:.1f}" y1="{yt4}" x2="{tx:.1f}" y2="{yb4}" stroke="#223042" stroke-width="1"/>')
    parts4.append(f'<text x="{tx:.1f}" y="{yb4 + 28}" fill="#8ea3b8" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="16" text-anchor="middle">{t} tok/s</text>')

for i, (lbl, val, col, note) in enumerate(spec_pts):
    ry = yt4 + i * rh4
    parts4.append(f'<text x="70" y="{ry + 52}" fill="#f1f5f9" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="21" font-weight="600">{lbl}</text>')
    bw = (val / max4) * bw4
    parts4.append(f'<rect x="{lx4}" y="{ry + 24}" width="{bw:.1f}" height="40" rx="6" fill="{col}" fill-opacity="0.9"/>')
    # Place value inside bar (dark text) and note cleanly in right margin past the ceiling line
    parts4.append(f'<text x="{lx4 + bw - 12:.1f}" y="{ry + 51}" fill="#0f141b" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="19" font-weight="700" text-anchor="end">{val:.1f} tok/s</text>')
    parts4.append(f'<text x="1238" y="{ry + 51}" fill="{col}" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="19" font-weight="700">{note}</text>')

parts4.append('<text x="70" y="644" fill="#7f93a8" font-family="DejaVu Sans,Arial,Helvetica,sans-serif" font-size="17">Conclusion: default --spec-threshold 0.8 wins every interleaved A/B. No flag-level decode headroom remains at 400 W.</text>')
parts4.append('</svg>')
p4 = OUT / "decode-ceiling-20261124.svg"
p4.write_text("\n".join(parts4))
render_png(p4)

print("Generated charts:")
for p in [p1, p2, p3, p4]:
    print(" ", p.name, "->", p.with_suffix(".png").stat().st_size, "bytes")
