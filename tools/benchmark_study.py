#!/usr/bin/env python3
"""Summarize paired real-agent measurements; never infer actual tokens from text size."""
import argparse
import csv
import json
import math
from pathlib import Path
import statistics

FIELDS = ['task_id', 'trial', 'model', 'mode', 'input_tokens', 'output_tokens', 'duration_ms', 'correct']


def analyse(rows):
    groups = {}
    for row in rows:
        if row['mode'] not in ('off', 'warm', 'cold'):
            raise ValueError('mode must be off, warm or cold')
        if row['correct'] not in ('yes', 'no'):
            raise ValueError('correct must be yes or no')
        key = (row['task_id'], row['trial'], row['model'])
        if not all(key):
            raise ValueError('Task, trial and model must be specified')
        values = {}
        for metric in ['input_tokens', 'output_tokens', 'duration_ms']:
            value = float(row[metric])
            if not math.isfinite(value) or value < 0 or ('tokens' in metric and not value.is_integer()):
                raise ValueError('Measurements must be finite, nonnegative; tokens must be integers')
            values[metric] = value
        values['correct'] = row['correct'] == 'yes'
        group = groups.setdefault(key, {})
        if row['mode'] in group:
            raise ValueError('Duplicate task/trial/model/mode measurement')
        group[row['mode']] = values
    pairs = []
    for key, group in groups.items():
        if 'off' not in group or 'warm' not in group:
            raise ValueError('Every task/trial/model needs off and warm measurements')
        off, warm = group['off'], group['warm']
        off_tokens = off['input_tokens'] + off['output_tokens']
        warm_tokens = warm['input_tokens'] + warm['output_tokens']
        pair = {'task_id': key[0], 'trial': key[1], 'model': key[2],
                'quality_pass': off['correct'] and warm['correct'],
                'off_tokens': off_tokens, 'warm_tokens': warm_tokens,
                'tokens_saved': off_tokens - warm_tokens,
                'duration_ms_saved': off['duration_ms'] - warm['duration_ms']}
        if 'cold' in group:
            cold = group['cold']
            premium = cold['input_tokens'] + cold['output_tokens'] - off_tokens
            pair['cold_quality_pass'] = cold['correct']
            pair['cold_extra_tokens'] = premium
            pair['repeat_uses_to_recover_cold_extra'] = (max(0, math.ceil(premium / pair['tokens_saved']))
                                                       if pair['tokens_saved'] > 0 and cold['correct'] and pair['quality_pass'] else None)
        pairs.append(pair)
    accepted = [p for p in pairs if p['quality_pass']]
    total_off = sum(p['off_tokens'] for p in accepted)
    saved = sum(p['tokens_saved'] for p in accepted)
    return {'schema': 1, 'pairs': pairs, 'total_pairs': len(pairs), 'quality_pass_pairs': len(accepted),
            'tokens_saved_on_quality_pass_pairs': saved,
            'token_reduction_percent': 100 * saved / total_off if total_off else None,
            'median_duration_ms_saved': statistics.median(p['duration_ms_saved'] for p in accepted) if accepted else None,
            'scope': 'User-supplied measured session totals. Not independently instrumented or causally attributed. Failed-quality pairs are excluded from savings and remain listed.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--output', type=Path, default=Path('benchmark-results/study.json'))
    args = parser.parse_args()
    with args.csv.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            parser.error('Missing required columns: ' + ', '.join(FIELDS))
        result = analyse(list(reader))
    if not result['pairs']:
        parser.error('No measurements supplied')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"{result['quality_pass_pairs']}/{result['total_pairs']} pairs passed quality; recorded token reduction: {result['token_reduction_percent']}%")


if __name__ == '__main__':
    main()
