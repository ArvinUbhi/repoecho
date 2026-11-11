#!/usr/bin/env python3
"""Dependency-free, synthetic repository benchmarks and paired release reports."""
import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HELPER = ROOT / '.github/skills/repoecho/scripts/repoecho.py'
SCHEMA = 1
PROFILES = {'smoke': [(100, 5)], 'team': [(1000, 20), (5000, 100)],
            'large': [(1000, 20), (5000, 100), (20000, 200)]}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def summary(values):
    return {'samples': len(values), 'median_ms': statistics.median(values),
            'p95_ms': sorted(values)[math.ceil(len(values) * .95) - 1],
            'min_ms': min(values), 'max_ms': max(values)}


def clean_env():
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               PYTHONDONTWRITEBYTECODE='1')
    return env


def fixture(helper, files, notes, runs, plain=False):
    """All mutations stay in a disposable fixture. Report no source or cache contents."""
    helper = Path(helper).resolve()
    spec = importlib.util.spec_from_file_location('benchmark_engine', helper)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    env = clean_env()
    raw = {}
    checks = []
    with tempfile.TemporaryDirectory(prefix='repoecho-suite-') as directory:
        root = Path(directory) / 'repository'; root.mkdir()
        paths = []
        for i in range(files):
            extension = ['java', 'py', 'ts', 'xml'][i % 4]
            name = f'module{i % 20:02d}/source{i:06d}.{extension}'
            p = root / name; p.parent.mkdir(exist_ok=True)
            p.write_text(f'// Synthetic {extension} source {i}\n' + '// Representative fixture text.\n' * 100, encoding='utf-8')
            paths.append(name)
        source_bytes = sum((root / p).stat().st_size for p in paths)

        def git(*args):
            return subprocess.run(['git', '-C', str(root), *args], env=env,
                                  capture_output=True, check=True, timeout=120)

        if not plain:
            git('init', '-b', 'main'); git('config', 'user.name', 'Benchmark')
            git('config', 'user.email', 'benchmark@example.invalid')
            git('config', 'core.hooksPath', str(root / '.git/disabled-hooks'))
            git('add', '.'); git('commit', '-m', 'Synthetic fixture')

        def cli(*args, location=root):
            start = time.perf_counter_ns()
            result = subprocess.run([sys.executable, str(helper), '--root', str(location), *args],
                                    env=env, capture_output=True, text=True, check=True, timeout=120)
            return json.loads(result.stdout), (time.perf_counter_ns() - start) / 1e6, len(result.stdout.encode())

        def measure(name, args, validate, count=runs, location=root):
            values = []; outputs = []
            for _ in range(count):
                data, elapsed, size = cli(*args, location=location)
                validate(data)
                values.append(elapsed); outputs.append(size)
            raw[name] = {'latency_ms': values, 'response_bytes': outputs}
            checks.append(name)
            return data

        def hit(data):
            require(len(data.get('hits', [])) == 1, 'Expected exactly one verified hit')
            require(data['hits'][0]['freshness'] == 'content_verified', 'Unverified hit')

        def miss(data):
            require(not data.get('hits'), 'Unexpected cached knowledge')

        def stale(data):
            miss(data); require(data.get('stale'), 'Changed evidence was not rejected')

        def bypass(data):
            require(data.get('state') == 'bypassed', 'Disabled mode read cache')

        measure('cold_scan', ['scan'], lambda d: None, count=1)
        evidence = paths[:3]
        # Setup uses the engine API, while measured retrieval uses a new CLI process.
        started = time.perf_counter()
        memory = engine.Memory(root)
        try:
            memory.scan()
            for i in range(notes):
                captured = [paths[(i * 3 + j) % files] for j in range(3)]
                receipt = memory.capture(captured, [], 24000)['receipt']
                memory.remember({'id': f'note-{i}', 'title': f'Workflow {i}',
                                 'summary': 'Synthetic source-linked workflow summary.',
                                 'tags': [f'topic{i:06d}']}, receipt)
        finally:
            memory.close()
        learning_ms = (time.perf_counter() - started) * 1000
        query = ['query', 'topic000000']
        cli(*query)  # Explicit unmeasured warm-up; OS page cache is not flushed.
        initial = measure('warm_hit', query, hit)
        revision = initial['hits'][0]['revision']
        compact = measure('compact_hit', [*query, '--compact'], hit)
        require(compact['hits'][0]['id'] == initial['hits'][0]['id'], 'Compact query changed result')
        # Four independent CLI readers simulate overlapping local agent requests.
        with ThreadPoolExecutor(max_workers=4) as pool:
            timings = []
            sizes = []
            for _ in range(runs):
                batch = list(pool.map(lambda _: cli(*query), range(4)))
                for data, elapsed, size in batch:
                    hit(data); timings.append(elapsed); sizes.append(size)
            raw['concurrent_readers_4'] = {'latency_ms': timings, 'response_bytes': sizes}
            checks.append('concurrent_readers_4')
        measure('query_miss', ['query', 'absentuniquequery'], miss)
        measure('budget_omission', [*query, '--max-chars', '1'],
                lambda d: (miss(d), require(d.get('budget_omitted', 0) > 0, 'Budget not enforced')))
        measure('warm_scan', ['scan'], lambda d: None)
        measure('full_scan', ['scan', '--full'], lambda d: None)
        before = cli('storage')[0]
        for mode in ['mode', 'cache'] + ([] if plain else ['branch']):
            cli(mode, 'off'); measure(mode + '_off', query, bypass)
            cli(mode, 'inherit' if mode == 'branch' else 'on')
        other = Path(directory) / 'other'; other.mkdir()
        (other / 'different.java').write_text('Other repository', encoding='utf-8')
        measure('repository_isolation', query, miss, location=other)
        # Unrelated edits must not reject the note.
        untouched = root / paths[-1]; saved = untouched.read_bytes()
        untouched.write_bytes(saved + b'// unrelated\n')
        measure('unrelated_edit', query, hit)
        untouched.write_bytes(saved)
        target = root / paths[0]; original = target.read_bytes()
        target.write_bytes(original + b'// changed\n')
        measure('dirty_evidence', query, stale)
        if not plain:
            git('add', '--', paths[0]); measure('staged_evidence', query, stale)
            git('reset', '--', paths[0])
        target.write_bytes(original)
        renamed = target.with_name('renamed.java'); target.rename(renamed)
        measure('renamed_evidence', query, stale); renamed.rename(target)
        target.unlink(); measure('deleted_evidence', query, stale); target.write_bytes(original)
        measure('restored_evidence', query, hit)
        # Membership-sensitive notes must reject new, untracked matching files.
        memory = engine.Memory(root)
        try:
            receipt = memory.capture([paths[0]], ['module00/**'], 24000)['receipt']
            memory.remember({'id': 'scope', 'title': 'Module membership',
                             'summary': 'Synthetic membership-sensitive summary.', 'tags': ['scopetopic']}, receipt)
        finally:
            memory.close()
        added = root / 'module00/new.java'; added.write_text('// new member\n', encoding='utf-8')
        measure('scope_addition', ['query', 'scopetopic'], stale); added.unlink()
        if not plain:
            git('switch', '-c', 'feature')
            measure('unchanged_branch', query, hit)
            target.write_bytes(original + b'// feature\n'); git('add', '--', paths[0])
            git('commit', '-m', 'Feature evidence')
            measure('changed_branch', query, stale)
            memory = engine.Memory(root)
            try:
                receipt = memory.capture(evidence, [], 24000)['receipt']
                memory.remember({'id': 'note-0', 'title': 'Feature workflow',
                                 'summary': 'Synthetic feature revision.', 'tags': ['topic000000']}, receipt)
            finally:
                memory.close()
            feature = cli(*query)[0]['hits'][0]['revision']
            require(feature != revision, 'Feature revision not saved')
            git('switch', 'main')
            def original_hit(d):
                hit(d); require(d['hits'][0]['revision'] == revision, 'Original branch revision not reused')
            measure('branch_return', query, original_hit)
            git('switch', 'feature')
            measure('feature_return', query, lambda d: (hit(d), require(d['hits'][0]['revision'] == feature, 'Feature revision not reused')))
            git('switch', 'main')
            worktree = Path(directory) / 'worktree'
            git('worktree', 'add', '--detach', str(worktree), 'HEAD')
            measure('worktree_isolation', query, miss, location=worktree)
            git('worktree', 'remove', '--force', str(worktree))
        after = cli('storage')[0]
        expected = notes + 1 + (0 if plain else 1)
        require(after['note_revisions'] == expected, 'Queries or branch returns duplicated stored revisions')
        return {'files': files, 'notes': notes, 'repository': 'plain' if plain else 'git',
                'runs': runs, 'source_bytes': source_bytes, 'learning_setup_ms': learning_ms,
                'storage_before': before, 'storage_after': after,
                'context_estimate': compact.get('context_estimate'),
                'checks_passed': checks, 'raw': raw,
                'metrics': {name: summary(v['latency_ms']) for name, v in raw.items()}}


def comparisons(results, percent, floor):
    rows = []
    groups = {}
    for result in results:
        key = (result['files'], result['notes'], result['repository'], result['trial'])
        groups.setdefault(key, {})[result['label']] = result
    for key, pair in sorted(groups.items()):
        if 'baseline' not in pair or 'candidate' not in pair:
            continue
        for name, new in pair['candidate']['metrics'].items():
            old = pair['baseline']['metrics'][name]['median_ms']
            value = new['median_ms']; delta = value - old
            change = 100 * delta / old if old else None
            rows.append({'files': key[0], 'notes': key[1], 'repository': key[2], 'trial': key[3],
                         'scenario': name, 'baseline_ms': old, 'candidate_ms': value,
                         'change_percent': change,
                         'regression': change is not None and change > percent and delta > floor})
    return rows


def write_reports(report, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    with (output / 'samples.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['label', 'trial', 'files', 'notes', 'repository', 'scenario', 'sample', 'latency_ms', 'response_bytes'])
        for r in report['results']:
            for scenario, values in r['raw'].items():
                for i, (ms, size) in enumerate(zip(values['latency_ms'], values['response_bytes'])):
                    writer.writerow([r['label'], r['trial'], r['files'], r['notes'], r['repository'], scenario, i + 1, ms, size])
    lines = ['# RepoEcho benchmark report', '', f"Generated: {report['created_at']}", '',
             f"Environment: {report['environment']['system']} / Python {report['environment']['python']}", '',
             'Synthetic helper timings include Python process startup and Git. No LLM calls, actual token savings, AIC or thinking-time measurements. Cold scan means an empty RepoEcho cache, not cold OS disk caches.', '',
             '## Measured scenarios', '', '| Build | Trial | Files | Repo | Scenario | N | Median ms | p95 ms |',
             '|---|---:|---:|---|---|---:|---:|---:|']
    for r in report['results']:
        for name, metric in r['metrics'].items():
            lines.append(f"| {r['label']} | {r['trial']} | {r['files']} | {r['repository']} | {name} | {metric['samples']} | {metric['median_ms']:.2f} | {metric['p95_ms']:.2f} |")
    lines += ['', '## Storage and context', '', '| Build | Trial | Files | Repo | DB allocated bytes | Revisions | Compact response bytes |', '|---|---:|---:|---|---:|---:|---:|']
    for r in report['results']:
        lines.append(f"| {r['label']} | {r['trial']} | {r['files']} | {r['repository']} | {r['storage_after']['database_allocated_bytes']} | {r['storage_after']['note_revisions']} | {int(statistics.median(r['raw']['compact_hit']['response_bytes']))} |")
    lines += ['', '## Baseline comparison', '', 'Positive changes are slower. Flags require both percentage and absolute thresholds; confirm on a controlled machine before treating timing as a release blocker.', '', '| Files | Repo | Trial | Scenario | Baseline ms | Candidate ms | Change % | Flag |', '|---:|---|---:|---|---:|---:|---:|---|']
    for r in report['comparisons']:
        change = 'n/a' if r['change_percent'] is None else f"{r['change_percent']:+.1f}"
        lines.append(f"| {r['files']} | {r['repository']} | {r['trial']} | {r['scenario']} | {r['baseline_ms']:.2f} | {r['candidate_ms']:.2f} | {change} | {'REVIEW' if r['regression'] else ''} |")
    if not report['comparisons']:
        lines += ['', 'No baseline supplied; no release speedup claim is made.']
    lines += ['', 'Raw samples, engine SHA-256 identities, thresholds and detailed storage/context estimates are in report.json and samples.csv. p95 uses nearest rank; small samples do not establish an SLA. Correctness failures abort the suite and produce failure.json.', '']
    markdown = '\n'.join(lines)
    (output / 'report.md').write_text(markdown, encoding='utf-8')
    body = []; in_table = False
    for line in lines:
        if line.startswith('|'):
            if set(line.replace('|', '').replace(':', '').replace('-', '').strip()) == set():
                continue
            if not in_table:
                body.append('<div class="table"><table>'); in_table = True
            cells = line.strip('|').split('|')
            body.append('<tr>' + ''.join('<td>' + html.escape(cell.strip()) + '</td>' for cell in cells) + '</tr>')
        else:
            if in_table:
                body.append('</table></div>'); in_table = False
            if line.startswith('# '):
                body.append('<h1>' + html.escape(line[2:]) + '</h1>')
            elif line.startswith('## '):
                body.append('<h2>' + html.escape(line[3:]) + '</h2>')
            elif line:
                body.append('<p>' + html.escape(line) + '</p>')
    if in_table:
        body.append('</table></div>')
    (output / 'report.html').write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>RepoEcho benchmarks</title><style>body{font:15px system-ui;margin:2rem auto;padding:0 1rem;max-width:1200px;color:#172635}h1,h2{color:#155b73}.table{overflow:auto}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}td{padding:.5rem;border-bottom:1px solid #d5e0e5;white-space:nowrap}tr:first-child{font-weight:bold;background:#eaf4f7}tr:nth-child(even){background:#f5f8fa}p{line-height:1.6}</style>' + ''.join(body), encoding='utf-8')



def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=PROFILES, default='smoke')
    parser.add_argument('--runs', type=int, default=5)
    parser.add_argument('--trials', type=int, default=2)
    parser.add_argument('--helper', type=Path, default=DEFAULT_HELPER)
    parser.add_argument('--baseline-helper', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'benchmark-results')
    parser.add_argument('--regression-percent', type=float, default=25)
    parser.add_argument('--regression-ms', type=float, default=10)
    parser.add_argument('--fail-on-regression', action='store_true')
    args = parser.parse_args(argv)
    if args.runs < 1 or args.trials < 1 or args.regression_percent < 0 or args.regression_ms < 0:
        parser.error('runs/trials must be positive and thresholds nonnegative')
    # Isolate imported engine API calls as well as child processes.
    environment = clean_env()
    os.environ.clear(); os.environ.update(environment)
    engines = {'candidate': args.helper.resolve()}
    if args.baseline_helper:
        engines['baseline'] = args.baseline_helper.resolve()
    report = {'schema': SCHEMA, 'created_at': datetime.now(timezone.utc).isoformat(),
              'environment': {'system': platform.system(), 'machine': platform.machine(),
                              'python': platform.python_version(), 'cpu_count': os.cpu_count(),
                              'git': subprocess.check_output(['git', '--version'], text=True).strip()},
              'profile': args.profile, 'thresholds': {'percent': args.regression_percent, 'ms': args.regression_ms},
              'engines': {k: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for k, p in engines.items()},
              'results': []}
    args.output.mkdir(parents=True, exist_ok=True)
    for name in ['report.json', 'report.md', 'report.html', 'samples.csv', 'failure.json']:
        (args.output / name).unlink(missing_ok=True)
    try:
        for trial in range(1, args.trials + 1):
            labels = list(engines) if trial % 2 else list(reversed(engines))
            for files, notes in PROFILES[args.profile]:
                for plain in [False, True]:
                    for label in labels:
                        print(f'{label}: trial={trial} files={files} notes={notes} plain={plain}', flush=True)
                        result = fixture(engines[label], files, notes, args.runs, plain)
                        result.update(label=label, trial=trial)
                        report['results'].append(result)
        report['comparisons'] = comparisons(report['results'], args.regression_percent, args.regression_ms)
        write_reports(report, args.output)
    except Exception as error:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / 'failure.json').write_text(json.dumps({'error_type': type(error).__name__, 'message': str(error), 'completed_fixtures': len(report['results'])}, indent=2), encoding='utf-8')
        raise
    return 1 if args.fail_on_regression and any(r['regression'] for r in report['comparisons']) else 0


if __name__ == '__main__':
    sys.exit(main())
