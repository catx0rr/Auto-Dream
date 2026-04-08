#!/usr/bin/env python3
"""
autodream: gate — quality gate evaluation

Takes a list of scored candidate entries and mode thresholds,
applies gates in strictest-first order (rem → deep → core),
returns qualified/deferred split.

Usage:
    python3 gate.py --candidates candidates.json --config ~/.openclaw/autodream/autodream.json --modes rem,deep,core
    python3 gate.py --candidates candidates.json --config ~/.openclaw/autodream/autodream.json --modes core

Input (candidates.json): array of objects with at minimum:
  { "id": "...", "importance": 0.82, "referenceCount": 5, "uniqueSessionCount": 3, "marker": null }

Typically produced by the LLM after extraction, or from score.py output.
"""

import argparse
import json
import sys
from pathlib import Path

# Strictness order — higher minScore = stricter
STRICTNESS_ORDER = ['rem', 'deep', 'core']


def load_candidates(path: str) -> list:
    with open(path, 'r') as f:
        data = json.loads(f.read())
    return data if isinstance(data, list) else data.get('scored', data.get('candidates', []))


def load_config(path: str) -> dict:
    with open(path, 'r') as f:
        return json.loads(f.read())


def apply_gates(candidates: list, config: dict, due_modes: list) -> dict:
    """Apply quality gates in strictness order. Returns qualified/deferred."""
    modes_conf = config.get('modes', {})

    # Filter to due modes, sort by strictness
    ordered_modes = [m for m in STRICTNESS_ORDER if m in due_modes]

    qualified = []
    qualified_ids = set()
    breakdown = {m: [] for m in ordered_modes}

    for mode in ordered_modes:
        gate = modes_conf.get(mode, {})
        min_score = gate.get('minScore', 0.0)
        min_recall = gate.get('minRecallCount', 0)
        min_unique = gate.get('minUnique', 0)

        for entry in candidates:
            entry_id = entry.get('id', entry.get('summary', ''))
            if entry_id in qualified_ids:
                continue  # already promoted by stricter mode

            marker = entry.get('marker')
            importance = entry.get('importance', 0.0)
            ref_count = entry.get('referenceCount', entry.get('ref_count', 0))
            unique = entry.get('uniqueSessionCount', entry.get('unique_sessions', 0))

            # PERMANENT bypasses gates
            if marker == 'PERMANENT':
                qualified.append({
                    **entry,
                    'promotedBy': mode,
                    'gate_bypass': 'PERMANENT',
                })
                qualified_ids.add(entry_id)
                breakdown[mode].append(entry_id)
                continue

            # Apply gate
            passes_score = importance >= min_score
            passes_recall = ref_count >= min_recall
            passes_unique = unique >= min_unique

            if passes_score and passes_recall and passes_unique:
                qualified.append({
                    **entry,
                    'promotedBy': mode,
                    'gate_detail': {
                        'score': f'{importance:.3f} >= {min_score}',
                        'recall': f'{ref_count} >= {min_recall}',
                        'unique': f'{unique} >= {min_unique}',
                    },
                })
                qualified_ids.add(entry_id)
                breakdown[mode].append(entry_id)

    # Deferred = candidates not in qualified
    deferred = []
    for entry in candidates:
        entry_id = entry.get('id', entry.get('summary', ''))
        if entry_id not in qualified_ids:
            # Show why it failed each mode
            fail_reasons = {}
            for mode in ordered_modes:
                gate = modes_conf.get(mode, {})
                reasons = []
                importance = entry.get('importance', 0.0)
                ref_count = entry.get('referenceCount', entry.get('ref_count', 0))
                unique = entry.get('uniqueSessionCount', entry.get('unique_sessions', 0))

                if importance < gate.get('minScore', 0):
                    reasons.append(f'score {importance:.3f} < {gate["minScore"]}')
                if ref_count < gate.get('minRecallCount', 0):
                    reasons.append(f'recall {ref_count} < {gate["minRecallCount"]}')
                if unique < gate.get('minUnique', 0):
                    reasons.append(f'unique {unique} < {gate["minUnique"]}')
                fail_reasons[mode] = reasons

            deferred.append({
                **entry,
                'fail_reasons': fail_reasons,
            })

    return {
        'modes_evaluated': ordered_modes,
        'total_candidates': len(candidates),
        'qualified_count': len(qualified),
        'deferred_count': len(deferred),
        'breakdown': {m: len(ids) for m, ids in breakdown.items()},
        'qualified': qualified,
        'deferred': deferred,
    }


def main():
    parser = argparse.ArgumentParser(description='AutoDream: Quality Gate Evaluation')
    parser.add_argument('--candidates', required=True,
                        help='Path to candidates JSON file (array of scored entries)')
    parser.add_argument('--config', required=True,
                        help='Path to autodream.json')
    parser.add_argument('--modes', required=True,
                        help='Comma-separated due modes (e.g., rem,deep,core)')
    args = parser.parse_args()

    candidates = load_candidates(args.candidates)
    config = load_config(args.config)
    due_modes = [m.strip() for m in args.modes.split(',')]

    result = apply_gates(candidates, config, due_modes)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return 0


if __name__ == '__main__':
    sys.exit(main())
