#!/usr/bin/env python3
"""
autodream: gate — quality gate evaluation

Takes a list of scored candidate entries and mode thresholds,
applies gates in configured strictness order,
returns qualified/deferred split.

Usage:
    python3 gate.py --candidates candidates.json --config ~/.openclaw/autodream/autodream.json --modes rem,deep,core
    python3 gate.py --candidates candidates.json --config ~/.openclaw/autodream/autodream.json --modes core

Input (candidates.json): array of objects with at minimum:
  {
    "id": "...",
    "importance": 0.82,
    "referenceCount": 5,
    "uniqueSessionCount": 3,
    "marker": null
  }

Supported optional candidate fields:
  - uniqueDayCount / unique_day_count
  - uniqueChannelCount / unique_channel_count
  - marker
  - ref_count
  - unique_sessions

Supported optional mode config fields:
  - minScore
  - minRecallCount
  - minUnique
  - uniqueMode: "day_or_session" | "day" | "session" | "max" | "channel"
  - fastPathMinScore
  - fastPathMinRecallCount
  - fastPathMarkers: ["HIGH", "PIN", "PROCEDURE", ...]
  - enabled

Notes:
- PERMANENT still bypasses all gates.
- Fast path is a softer bypass for high-salience entries.
- Default uniqueMode is "day_or_session":
    prefer uniqueDayCount when available, otherwise fall back to uniqueSessionCount.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Evaluation order.
# Keep this aligned with how you want "higher-tier" promotion to win.
# Current behavior: rem is evaluated first, then deep, then core.
STRICTNESS_ORDER = ['rem', 'deep', 'core']


def load_candidates(path: str) -> list:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.loads(f.read())
    if isinstance(data, list):
        return data
    return data.get('scored', data.get('candidates', []))


def load_config(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.loads(f.read())


def normalize_marker(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, str):
        return value.strip().upper()
    return str(value).strip().upper()


def normalize_marker_list(values: Any) -> set:
    if not values:
        return set()
    if isinstance(values, list):
        return {normalize_marker(v) for v in values if str(v).strip()}
    if isinstance(values, str):
        # Support comma-separated config strings just in case
        return {normalize_marker(v) for v in values.split(',') if v.strip()}
    return {normalize_marker(values)}


def get_entry_id(entry: dict) -> str:
    return str(
        entry.get('id')
        or entry.get('summary')
        or entry.get('title')
        or entry.get('name')
        or json.dumps(entry, sort_keys=True, ensure_ascii=False)
    )


def get_reference_count(entry: dict) -> int:
    return int(entry.get('referenceCount', entry.get('ref_count', 0)) or 0)


def get_unique_counts(entry: dict) -> Tuple[int, int, int]:
    unique_session = int(entry.get('uniqueSessionCount', entry.get('unique_sessions', 0)) or 0)
    unique_day = int(entry.get('uniqueDayCount', entry.get('unique_day_count', 0)) or 0)
    unique_channel = int(entry.get('uniqueChannelCount', entry.get('unique_channel_count', 0)) or 0)
    return unique_session, unique_day, unique_channel


def get_effective_unique(entry: dict, gate: dict) -> Tuple[int, str, Dict[str, int]]:
    unique_session, unique_day, unique_channel = get_unique_counts(entry)
    unique_mode = str(gate.get('uniqueMode', 'day_or_session')).strip().lower()

    if unique_mode == 'day':
        unique = unique_day
        source = 'uniqueDayCount'
    elif unique_mode == 'session':
        unique = unique_session
        source = 'uniqueSessionCount'
    elif unique_mode == 'channel':
        unique = unique_channel
        source = 'uniqueChannelCount'
    elif unique_mode == 'max':
        unique = max(unique_day, unique_session, unique_channel)
        if unique == unique_day:
            source = 'max(uniqueDayCount, uniqueSessionCount, uniqueChannelCount)->uniqueDayCount'
        elif unique == unique_session:
            source = 'max(uniqueDayCount, uniqueSessionCount, uniqueChannelCount)->uniqueSessionCount'
        else:
            source = 'max(uniqueDayCount, uniqueSessionCount, uniqueChannelCount)->uniqueChannelCount'
    else:
        # default: day_or_session
        if unique_day > 0:
            unique = unique_day
            source = 'uniqueDayCount'
        else:
            unique = unique_session
            source = 'uniqueSessionCount'

    raw_counts = {
        'uniqueSessionCount': unique_session,
        'uniqueDayCount': unique_day,
        'uniqueChannelCount': unique_channel,
    }
    return unique, source, raw_counts


def get_gate_values(gate: dict) -> Tuple[float, int, int]:
    min_score = float(gate.get('minScore', 0.0) or 0.0)
    min_recall = int(gate.get('minRecallCount', 0) or 0)
    min_unique = int(gate.get('minUnique', 0) or 0)
    return min_score, min_recall, min_unique


def passes_fast_path(entry: dict, gate: dict) -> Tuple[bool, Dict[str, Any]]:
    marker = normalize_marker(entry.get('marker'))
    importance = float(entry.get('importance', 0.0) or 0.0)
    ref_count = get_reference_count(entry)

    fast_path_score = gate.get('fastPathMinScore', None)
    fast_path_recall = int(gate.get('fastPathMinRecallCount', 0) or 0)
    fast_path_markers = normalize_marker_list(gate.get('fastPathMarkers', []))

    score_recall_pass = False
    if fast_path_score is not None:
        try:
            fast_path_score = float(fast_path_score)
            score_recall_pass = importance >= fast_path_score and ref_count >= fast_path_recall
        except (TypeError, ValueError):
            score_recall_pass = False

    marker_pass = marker in fast_path_markers if marker else False
    passed = score_recall_pass or marker_pass

    detail = {
        'marker': marker or None,
        'importance': importance,
        'referenceCount': ref_count,
        'fastPathMinScore': fast_path_score,
        'fastPathMinRecallCount': fast_path_recall,
        'fastPathMarkers': sorted(fast_path_markers),
        'score_recall_pass': score_recall_pass,
        'marker_pass': marker_pass,
    }
    return passed, detail


def apply_gates(candidates: list, config: dict, due_modes: list) -> dict:
    """Apply quality gates in strictness order. Returns qualified/deferred."""
    modes_conf = config.get('modes', {})

    # Filter to due modes, preserving configured evaluation order
    ordered_modes = [m for m in STRICTNESS_ORDER if m in due_modes]

    qualified = []
    qualified_ids = set()
    breakdown = {m: [] for m in ordered_modes}

    for mode in ordered_modes:
        gate = modes_conf.get(mode, {})
        if not gate.get('enabled', True):
            continue

        min_score, min_recall, min_unique = get_gate_values(gate)

        for entry in candidates:
            entry_id = get_entry_id(entry)
            if entry_id in qualified_ids:
                continue  # already promoted by earlier-evaluated mode

            marker = normalize_marker(entry.get('marker'))
            importance = float(entry.get('importance', 0.0) or 0.0)
            ref_count = get_reference_count(entry)
            unique, unique_source, raw_unique = get_effective_unique(entry, gate)

            # Hard bypass: PERMANENT
            if marker == 'PERMANENT':
                qualified.append({
                    **entry,
                    'promotedBy': mode,
                    'gate_bypass': 'PERMANENT',
                    'gate_detail': {
                        'score': f'{importance:.3f}',
                        'recall': str(ref_count),
                        'unique': f'{unique} via {unique_source}',
                        'raw_unique': raw_unique,
                    },
                })
                qualified_ids.add(entry_id)
                breakdown[mode].append(entry_id)
                continue

            # Soft bypass: fast path
            fast_path_passed, fast_path_detail = passes_fast_path(entry, gate)
            if fast_path_passed:
                qualified.append({
                    **entry,
                    'promotedBy': mode,
                    'gate_bypass': 'FAST_PATH',
                    'gate_detail': {
                        'score': f'{importance:.3f}',
                        'recall': str(ref_count),
                        'unique': f'{unique} via {unique_source}',
                        'raw_unique': raw_unique,
                        'fast_path': fast_path_detail,
                    },
                })
                qualified_ids.add(entry_id)
                breakdown[mode].append(entry_id)
                continue

            # Regular AND gate
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
                        'unique': f'{unique} >= {min_unique} via {unique_source}',
                        'raw_unique': raw_unique,
                    },
                })
                qualified_ids.add(entry_id)
                breakdown[mode].append(entry_id)

    # Deferred = candidates not in qualified
    deferred = []
    for entry in candidates:
        entry_id = get_entry_id(entry)
        if entry_id in qualified_ids:
            continue

        importance = float(entry.get('importance', 0.0) or 0.0)
        ref_count = get_reference_count(entry)
        marker = normalize_marker(entry.get('marker'))

        fail_reasons = {}
        for mode in ordered_modes:
            gate = modes_conf.get(mode, {})
            if not gate.get('enabled', True):
                fail_reasons[mode] = ['mode disabled']
                continue

            min_score, min_recall, min_unique = get_gate_values(gate)
            unique, unique_source, raw_unique = get_effective_unique(entry, gate)
            mode_reasons = []

            # Show fast-path status for debugging
            fast_path_passed, fast_path_detail = passes_fast_path(entry, gate)

            if importance < min_score:
                mode_reasons.append(f'score {importance:.3f} < {min_score}')
            if ref_count < min_recall:
                mode_reasons.append(f'recall {ref_count} < {min_recall}')
            if unique < min_unique:
                mode_reasons.append(f'unique {unique} < {min_unique} via {unique_source}')

            if marker == 'PERMANENT':
                mode_reasons.append('PERMANENT would bypass, but entry was not promoted due to earlier processing issue')
            elif fast_path_detail.get('fastPathMinScore') is not None or fast_path_detail.get('fastPathMarkers'):
                if not fast_path_passed:
                    fp_notes = []
                    if fast_path_detail.get('fastPathMinScore') is not None:
                        fp_notes.append(
                            f'fastPath(score/recall) failed: '
                            f'{importance:.3f} / {ref_count} '
                            f'vs {fast_path_detail["fastPathMinScore"]} / {fast_path_detail["fastPathMinRecallCount"]}'
                        )
                    if fast_path_detail.get('fastPathMarkers'):
                        fp_notes.append(
                            f'fastPath(marker) failed: {marker or "none"} not in {fast_path_detail["fastPathMarkers"]}'
                        )
                    mode_reasons.extend(fp_notes)

            fail_reasons[mode] = {
                'reasons': mode_reasons,
                'raw_unique': raw_unique,
                'unique_used': {
                    'value': unique,
                    'source': unique_source,
                },
            }

        deferred.append({
            **entry,
            'fail_reasons': fail_reasons,
        })

    return {
        'ok': True,
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
    parser.add_argument(
        '--candidates',
        required=True,
        help='Path to candidates JSON file (array of scored entries)'
    )
    parser.add_argument(
        '--config',
        required=True,
        help='Path to autodream.json'
    )
    parser.add_argument(
        '--modes',
        required=True,
        help='Comma-separated due modes (e.g., rem,deep,core)'
    )
    args = parser.parse_args()

    candidates = load_candidates(args.candidates)
    config = load_config(args.config)
    due_modes = [m.strip() for m in args.modes.split(',') if m.strip()]

    result = apply_gates(candidates, config, due_modes)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
