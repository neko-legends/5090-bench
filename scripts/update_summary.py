import json

p = 'results/inkblot-2-mini-20261127/summary.json'
d = json.load(open(p))
d['status'] = 'promoted-2026-11-27 combined arm live'
d['cutover'] = {
    'date': '2026-11-27',
    'arm': 'combined',
    'method': 'weights directory plus ablation overlay swapped in the serving config; same binary, same flags, same model id (no client change)',
    'rollback': 'verified snapshot of the pre-cutover serving config; restore file then restart',
    'verified_after_cutover': {
        'thinking_on_by_default': True,
        'thinking_evidence': 'reasoning present with no reasoning_effort field sent; 53 completion tok, 121 reasoning chars, correct answer',
        'reasoning_replay_multiturn': True,
        'vision_live': {'cases': 8, 'correct': 8, 'backend': 'ripper-5090', 'fallback_calls': 0},
        'worker_smoke': 'synthetic CSV to JSON task completed; artifact re-run by the operator',
        'benign_controls': '5/5 substantive, 0 refusal patterns',
        'power_cap_w': 400,
        'lossless_path_active': True,
    },
    'limits': {
        'note': 'one shared context pool: input plus thinking plus answer',
        'engine_context': 262144,
        'generation_reserve_tokens': 8,
        'max_input_tokens_at_min_output': 262135,
        'max_output_tokens_at_51k_input': 211146,
        'engine_clamps_oversized_max_tokens': 'yes, never rejects',
        'cli_default_max_tokens': 65536,
        'max_tokens_is_a_ceiling_not_a_cap': 'the CLI sends a ceiling and the engine clamps to remaining room; no artificial per-request cap was added',
    },
    'larger_budget_result': {
        'fixture': 'same ~50,990-token synthesis prompt',
        'budgets_tested': [16000, 32768, 65536],
        'fact_proxy_hits_each': [21, 21, 21],
        'finish_each': ['length', 'length', 'length'],
        'wall_s_each': [31.0, 49.8, 100.9],
        'outputs_are_strict_prefixes': True,
        'useful_content_ends_at_chars': 1955,
        'conclusion': 'recall saturates at 21/25; extra budget is consumed by a ticket-number repetition loop, so the per-request synthesis budget stays 16000',
    },
}
d['pending_followups'] = [
    '400,000-token context qualification on the 5090 and on the pinned Radeon (256K is the current 5090 window, 131K on the Radeon)',
    'Adversarial refusal comparison (benign controls only so far)',
    '4-pass loop depth (3 passes evaluated only)',
]
json.dump(d, open(p, 'w'), indent=2)
open(p, 'a').write('\n')
print(d['status'], len(d['arms']), list(d['cutover']['limits'])[:3])
