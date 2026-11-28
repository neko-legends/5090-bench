#!/usr/bin/env python3
"""Generate a publication-grade SVG + PNG comparison chart for Inkblot-2-mini vs Incumbent Inkling-2-Mini.

Reads public-safe aggregates directly from results/inkblot-2-mini-20261127/summary.json
and renders docs/images/inkblot-vs-inkling-20261127.{svg,png}.
"""
import json
import subprocess
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "results/inkblot-2-mini-20261127/summary.json"
OUT = ROOT / "docs/images"
OUT.mkdir(parents=True, exist_ok=True)


def render_png(svg_path: Path, width: int = 1600) -> Path:
    png_path = svg_path.with_suffix(".png")
    subprocess.run(
        ["rsvg-convert", "-w", str(width), "-o", str(png_path), str(svg_path)],
        check=True,
    )
    return png_path


def main() -> None:
    payload = json.loads(DATA.read_text())
    arms = {a["id"]: a for a in payload["arms"]}
    inc = arms["incumbent"]
    pln = arms["plain"]
    cmb = arms["combined"]

    FONT = "DejaVu Sans,Arial,Helvetica,sans-serif"
    COLORS = {
        "incumbent": ("#60a5fa", "#93c5fd"),
        "plain": ("#22c55e", "#86efac"),
        "combined": ("#f59e0b", "#fcd34d"),
    }

    W, H = 1600, 1244
    p: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="#0f141b"/>',
        # Header
        f'<text x="64" y="56" fill="#8ea3b8" font-family="{FONT}" font-size="18" font-weight="600" letter-spacing="2">5090-BENCH  ·  CANDIDATE EVALUATION ({escape(payload["date"])})</text>',
        f'<text x="64" y="106" fill="#f4f7fa" font-family="{FONT}" font-size="38" font-weight="700">Inkblot-2-mini (fb0b924) vs. Incumbent Inkling-2-Mini</text>',
        f'<text x="64" y="142" fill="#b8c7d9" font-family="{FONT}" font-size="19">Single RTX 5090 (400 W cap) · same ingine binary (lossless chunk-6144/tiles-112) · 3 passes · controlled 2-boot run</text>',
        # Legend bar
        f'<rect x="64" y="164" width="1472" height="46" rx="10" fill="#151d28" stroke="#223042" stroke-width="1"/>',
        f'<rect x="86" y="178" width="18" height="18" rx="4" fill="{COLORS["incumbent"][0]}"/>',
        f'<text x="112" y="193" fill="#e2eaf3" font-family="{FONT}" font-size="17" font-weight="600">Incumbent: stock Inkling-2-Mini + overlay</text>',
        f'<rect x="556" y="178" width="18" height="18" rx="4" fill="{COLORS["plain"][0]}"/>',
        f'<text x="582" y="193" fill="#e2eaf3" font-family="{FONT}" font-size="17" font-weight="600">Plain: Ex0bit/Inkblot-2-mini (fb0b924)</text>',
        f'<rect x="1028" y="178" width="18" height="18" rx="4" fill="{COLORS["combined"][0]}"/>',
        f'<text x="1054" y="193" fill="#e2eaf3" font-family="{FONT}" font-size="17" font-weight="600">Combined: Inkblot-2-mini + overlay</text>',
    ]

    # =========================================================================
    # SECTION 1: Task Quality & Completion (Code, Synthesis, Hard Math, Vision)
    # =========================================================================
    p.append(
        f'<text x="64" y="246" fill="#8ea3b8" font-family="{FONT}" font-size="16" font-weight="700" letter-spacing="1.5">TASK QUALITY &amp; COMPLETION (% OF ITEMS PASSED / HIT)</text>'
    )

    lx, rx = 370, 1110
    bw = rx - lx
    y_top = 262
    row_h = 128
    tasks = [
        (
            "Tested Code",
            "csv2json suite (19 tests)",
            [
                ("incumbent", inc["code_csv2json"]["passed"], inc["code_csv2json"]["total"], "empty at 16k + 65k retry", True),
                ("plain", pln["code_csv2json"]["passed"], pln["code_csv2json"]["total"], "clean pass", False),
                ("combined", cmb["code_csv2json"]["passed"], cmb["code_csv2json"]["total"], "clean pass", False),
            ],
        ),
        (
            "Long Synthesis",
            "~50,990 in · 16k out cap (25 facts)",
            [
                ("incumbent", inc["synthesis"]["fact_proxy_hits"], inc["synthesis"]["fact_proxy_total"], "empty even at a 65,536 retry", True),
                ("plain", pln["synthesis"]["fact_proxy_hits"], pln["synthesis"]["fact_proxy_total"], f"{pln['synthesis']['output_tokens']:,} out tok", False),
                ("combined", cmb["synthesis"]["fact_proxy_hits"], cmb["synthesis"]["fact_proxy_total"], "▲ truncated at 16,000 ×2 — hit the cap", True),
            ],
        ),
        (
            "Hard Math",
            "40-problem eval (3 passes)",
            [
                ("incumbent", inc["hard_math"]["passed"], inc["hard_math"]["total"], "best on this 40-item set", False),
                ("plain", pln["hard_math"]["passed"], pln["hard_math"]["total"], "−4 vs incumbent", False),
                ("combined", cmb["hard_math"]["passed"], cmb["hard_math"]["total"], "−2 vs incumbent", False),
            ],
        ),
        (
            "Vision Accuracy",
            "37-item bench + 16/16 changed",
            [
                ("incumbent", inc["vision"]["passed"], inc["vision"]["total"], "16/16 changed · same OCR gold", False),
                ("plain", pln["vision"]["passed"], pln["vision"]["total"], "16/16 changed · same OCR gold", False),
                ("combined", cmb["vision"]["passed"], cmb["vision"]["total"], "16/16 changed · same OCR gold", False),
            ],
        ),
    ]

    y_bot = y_top + len(tasks) * row_h

    # X-axis tick labels for 0..100% (gridlines drawn cleanly inside each card)
    for tick in [0, 25, 50, 75, 100]:
        tx = lx + (tick / 100.0) * bw
        p.append(
            f'<text x="{tx:.1f}" y="{y_bot + 20}" fill="#8ea3b8" font-family="{FONT}" font-size="14" text-anchor="middle">{tick}%</text>'
        )

    for idx, (title, subtitle, entries) in enumerate(tasks):
        ry = y_top + idx * row_h
        p.append(
            f'<rect x="64" y="{ry + 6}" width="1472" height="{row_h - 12}" rx="12" fill="#151d28" stroke="#223042" stroke-width="1"/>'
        )
        p.append(
            f'<text x="86" y="{ry + 54}" fill="#f1f5f9" font-family="{FONT}" font-size="21" font-weight="700">{escape(title)}</text>'
        )
        p.append(
            f'<text x="86" y="{ry + 80}" fill="#8ea3b8" font-family="{FONT}" font-size="15">{escape(subtitle)}</text>'
        )

        # Re-draw subtle gridlines inside the card so bars align crisply
        for tick in [0, 25, 50, 75, 100]:
            tx = lx + (tick / 100.0) * bw
            p.append(
                f'<line x1="{tx:.1f}" y1="{ry + 14}" x2="{tx:.1f}" y2="{ry + row_h - 14}" stroke="#1f2c3d" stroke-width="1"/>'
            )

        for j, (arm_id, num, den, note, warn) in enumerate(entries):
            pct = (num / den) * 100.0
            by = ry + 20 + j * 30
            fill_col, txt_col = COLORS[arm_id]
            w_bar = (pct / 100.0) * bw

            if num == 0:
                # Visible empty-bar track + small red cap so 0% reads as an explicit empty failure
                p.append(
                    f'<rect x="{lx}" y="{by}" width="{bw:.1f}" height="22" rx="4" fill="#1c2432" stroke="#334155" stroke-width="1" stroke-dasharray="4,4"/>'
                )
                p.append(f'<rect x="{lx}" y="{by}" width="6" height="22" rx="3" fill="#ef4444"/>')
                p.append(
                    f'<text x="{lx + 16}" y="{by + 16}" fill="#fca5a5" font-family="{FONT}" font-size="15" font-weight="700">{num}/{den} (0.0%) — {escape(note)}</text>'
                )
            else:
                p.append(
                    f'<rect x="{lx}" y="{by}" width="{w_bar:.1f}" height="22" rx="4" fill="{fill_col}" fill-opacity="0.92"/>'
                )
                # Label inside bar on right end if wide enough, else outside
                score_txt = f"{num}/{den} ({pct:.1f}%)"
                p.append(
                    f'<text x="{lx + w_bar - 10:.1f}" y="{by + 16}" fill="#0b1017" font-family="{FONT}" font-size="14" font-weight="700" text-anchor="end">{score_txt}</text>'
                )
                note_col = "#fbbf24" if warn else "#9fb2c7"
                p.append(
                    f'<text x="{rx + 22}" y="{by + 16}" fill="{note_col}" font-family="{FONT}" font-size="15" font-weight="{"600" if warn else "400"}">{escape(note)}</text>'
                )

    # =========================================================================
    # SECTION 2: Bottom Split Cards — Throughput (Left) & Vision Latency (Right)
    # =========================================================================
    card_y = y_bot + 42
    card_h = 312

    # --- Left Card: Decode Throughput (2 boots) ---
    p.append(
        f'<rect x="64" y="{card_y}" width="724" height="{card_h}" rx="12" fill="#151d28" stroke="#223042" stroke-width="1"/>'
    )
    p.append(
        f'<text x="88" y="{card_y + 34}" fill="#8ea3b8" font-family="{FONT}" font-size="15" font-weight="700" letter-spacing="1.4">DECODE THROUGHPUT · c1 tok/s (HIGHER IS FASTER · 2 BOOTS)</text>'
    )

    tlx, trx = 258, 614
    tbw = trx - tlx
    tmax = 460.0
    ty_top = card_y + 54
    trh = 62
    ty_bot = ty_top + 3 * trh

    for tick in [0, 100, 200, 300, 400]:
        tx = tlx + (tick / tmax) * tbw
        p.append(f'<line x1="{tx:.1f}" y1="{ty_top}" x2="{tx:.1f}" y2="{ty_bot}" stroke="#223042" stroke-width="1"/>')
        p.append(
            f'<text x="{tx:.1f}" y="{ty_bot + 20}" fill="#8ea3b8" font-family="{FONT}" font-size="13" text-anchor="middle">{tick}</text>'
        )

    inc_mean = (inc["decode_tok_s"]["boot_1"] + inc["decode_tok_s"]["boot_2"]) / 2.0
    t_rows = [
        ("incumbent", "Incumbent", inc["decode_tok_s"]["boot_1"], inc["decode_tok_s"]["boot_2"]),
        ("plain", "Plain Inkblot", pln["decode_tok_s"]["boot_1"], pln["decode_tok_s"]["boot_2"]),
        ("combined", "Inkblot + overlay", cmb["decode_tok_s"]["boot_1"], cmb["decode_tok_s"]["boot_2"]),
    ]

    for i, (arm_id, lbl, b1, b2) in enumerate(t_rows):
        ry = ty_top + i * trh
        fill_col, txt_col = COLORS[arm_id]
        mean_v = (b1 + b2) / 2.0
        delta_pct = (mean_v / inc_mean - 1.0) * 100.0
        p.append(
            f'<text x="88" y="{ry + 36}" fill="#f1f5f9" font-family="{FONT}" font-size="17" font-weight="600">{escape(lbl)}</text>'
        )
        # Paired Boot 1 (top, solid) and Boot 2 (bottom, slightly lighter) bars
        w1 = (b1 / tmax) * tbw
        w2 = (b2 / tmax) * tbw
        p.append(f'<rect x="{tlx}" y="{ry + 11}" width="{w1:.1f}" height="17" rx="3" fill="{fill_col}" fill-opacity="0.95"/>')
        p.append(f'<rect x="{tlx}" y="{ry + 31}" width="{w2:.1f}" height="17" rx="3" fill="{fill_col}" fill-opacity="0.62"/>')
        # Exact values to the right
        p.append(
            f'<text x="{trx + 14}" y="{ry + 25}" fill="{txt_col}" font-family="{FONT}" font-size="14" font-weight="700">{b1:.1f} / {b2:.1f}</text>'
        )
        if arm_id == "incumbent":
            delta_str = "baseline"
        elif abs(delta_pct) < 0.1:
            delta_str = "≈ baseline"
        else:
            sign = "+" if delta_pct > 0 else "−"
            delta_str = f"{sign}{abs(delta_pct):.1f}% mean"
        d_col = "#9fb2c7" if abs(delta_pct) < 1.0 else "#fbbf24"
        p.append(
            f'<text x="{trx + 14}" y="{ry + 45}" fill="{d_col}" font-family="{FONT}" font-size="13">{delta_str}</text>'
        )

    p.append(
        f'<text x="88" y="{card_y + card_h - 18}" fill="#7f93a8" font-family="{FONT}" font-size="13">Top bar = Boot 1, bottom bar = Boot 2 (same binary). Combined overlay costs ~13.6 tok/s (−3.2%).</text>'
    )

    # --- Right Card: Cold Vision Latency ---
    rcx = 812
    p.append(
        f'<rect x="{rcx}" y="{card_y}" width="724" height="{card_h}" rx="12" fill="#151d28" stroke="#223042" stroke-width="1"/>'
    )
    p.append(
        f'<text x="{rcx + 24}" y="{card_y + 34}" fill="#8ea3b8" font-family="{FONT}" font-size="15" font-weight="700" letter-spacing="1.4">COLD VISION MEDIAN LATENCY · SECONDS (LOWER IS FASTER)</text>'
    )

    vlx, vrx = rcx + 194, rcx + 558
    vbw = vrx - vlx
    vmax = 0.45
    vy_top = card_y + 54
    vrh = 62
    vy_bot = vy_top + 3 * vrh

    for tick in [0.0, 0.1, 0.2, 0.3, 0.4]:
        tx = vlx + (tick / vmax) * vbw
        p.append(f'<line x1="{tx:.1f}" y1="{vy_top}" x2="{tx:.1f}" y2="{vy_bot}" stroke="#223042" stroke-width="1"/>')
        p.append(
            f'<text x="{tx:.1f}" y="{vy_bot + 20}" fill="#8ea3b8" font-family="{FONT}" font-size="13" text-anchor="middle">{tick:.1f}s</text>'
        )

    inc_lat = inc["vision"]["cold_median_s"]
    v_rows = [
        ("incumbent", "Incumbent", inc["vision"]["cold_median_s"]),
        ("plain", "Plain Inkblot", pln["vision"]["cold_median_s"]),
        ("combined", "Inkblot + overlay", cmb["vision"]["cold_median_s"]),
    ]

    for i, (arm_id, lbl, sec) in enumerate(v_rows):
        ry = vy_top + i * vrh
        fill_col, txt_col = COLORS[arm_id]
        w_lat = (sec / vmax) * vbw
        delta_pct = (sec / inc_lat - 1.0) * 100.0
        p.append(
            f'<text x="{rcx + 24}" y="{ry + 36}" fill="#f1f5f9" font-family="{FONT}" font-size="17" font-weight="600">{escape(lbl)}</text>'
        )
        p.append(f'<rect x="{vlx}" y="{ry + 14}" width="{w_lat:.1f}" height="32" rx="5" fill="{fill_col}" fill-opacity="0.92"/>')
        p.append(
            f'<text x="{vrx + 14}" y="{ry + 28}" fill="{txt_col}" font-family="{FONT}" font-size="15" font-weight="700">{sec:.3f} s</text>'
        )
        if arm_id == "incumbent":
            delta_str = "baseline"
        else:
            sign = "+" if delta_pct > 0 else "−"
            delta_str = f"{sign}{abs(delta_pct):.0f}% latency"
        d_col = "#9fb2c7" if arm_id == "incumbent" else "#86efac"
        p.append(
            f'<text x="{vrx + 14}" y="{ry + 46}" fill="{d_col}" font-family="{FONT}" font-size="13">{delta_str}</text>'
        )

    p.append(
        f'<text x="{rcx + 24}" y="{card_y + card_h - 18}" fill="#7f93a8" font-family="{FONT}" font-size="13">All three arms scored 36/37 (same disputed OCR gold) and 16/16 on changed-image checks.</text>'
    )

    # =========================================================================
    # SECTION 3: Footer — Refusal Scope + Pending Status + Receipts
    # =========================================================================
    foot_y = card_y + card_h + 22
    p.append(
        f'<rect x="64" y="{foot_y}" width="1472" height="72" rx="10" fill="#171f2a" stroke="#334155" stroke-width="1"/>'
    )
    p.append(
        f'<text x="86" y="{foot_y + 29}" fill="#cbd5e1" font-family="{FONT}" font-size="16"><tspan font-weight="700" fill="#e2eaf3">Refusal check:</tspan> 0/20 refusal patterns across all 3 arms on 20 benign prompts (no evidence of broad refusal; not an adversarial red-team eval).</text>'
    )
    p.append(
        f'<text x="86" y="{foot_y + 55}" fill="#9fb2c7" font-family="{FONT}" font-size="16"><tspan font-weight="700" fill="#86efac">Now live (combined):</tspan> larger-budget rerun saturated at 21/25 on 16k/32.8k/65.5k, thinking on by default verified, 8/8 live vision with zero fallback.  ·  Data: results/inkblot-2-mini-20261127/summary.json</text>'
    )

    p.append("</svg>")

    svg_path = OUT / "inkblot-vs-inkling-20261127.svg"
    svg_path.write_text("\n".join(p) + "\n")
    png_path = render_png(svg_path)
    print(f"Generated {svg_path.relative_to(ROOT)} and {png_path.relative_to(ROOT)} ({png_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
