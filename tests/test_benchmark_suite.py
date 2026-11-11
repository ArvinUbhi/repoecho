import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('benchmark_suite', ROOT / 'tools/benchmark_suite.py')
SUITE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(SUITE)


class BenchmarkTests(unittest.TestCase):
    def test_nearest_rank_and_median(self):
        values = list(range(1, 21))
        self.assertEqual(SUITE.summary(values)['p95_ms'], 19)
        self.assertEqual(SUITE.summary(values)['median_ms'], 10.5)

    def test_regression_requires_relative_and_absolute_thresholds(self):
        def result(label, values):
            return dict(files=100, notes=5, repository='git', trial=1, label=label,
                        metrics={k: {'median_ms': v} for k, v in values.items()})
        rows = SUITE.comparisons([result('baseline', {'small': 1, 'large': 100, 'faster': 100}),
                                 result('candidate', {'small': 3, 'large': 140, 'faster': 80})], 25, 10)
        self.assertEqual([r['regression'] for r in rows], [False, True, False])
        self.assertEqual(rows[2]['change_percent'], -20)

    def test_no_baseline_means_no_comparison(self):
        self.assertEqual(SUITE.comparisons([], 25, 10), [])

    def test_fixture_correctness_and_reports(self):
        # Small fixture still covers all branch/evidence/control transitions.
        with tempfile.TemporaryDirectory() as temp:
            script = ROOT / 'tools/benchmark_suite.py'
            result = subprocess.run([sys.executable, str(script), '--runs', '1', '--trials', '1',
                                     '--output', temp], capture_output=True, text=True, timeout=180)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((Path(temp) / 'report.json').read_text())
            self.assertTrue(report['complete'])
            git, plain = report['results']
            self.assertIn('worktree_isolation', git['checks_passed'])
            self.assertIn('scope_addition', plain['checks_passed'])
            self.assertEqual(git['storage_after']['note_revisions'], 7)
            self.assertEqual(plain['storage_after']['note_revisions'], 6)
            self.assertEqual(len(git['raw']['warm_hit']['latency_ms']), 1)
            self.assertTrue((Path(temp) / 'samples.csv').is_file())
            self.assertIn('No baseline supplied', (Path(temp) / 'report.md').read_text())

    def test_partial_report_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            report = {'created_at': 'test', 'environment': {'system': 'test', 'python': 'test'},
                      'results': [], 'comparisons': [], 'complete': False}
            SUITE.write_reports(report, Path(temp))
            self.assertIn('PARTIAL', (Path(temp) / 'report.md').read_text())
            self.assertFalse(json.loads((Path(temp) / 'report.json').read_text())['complete'])

    def test_failure_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as temp:
            # Force a fixture exception after metadata is loaded.
            from unittest.mock import patch
            with patch.object(SUITE, 'fixture', side_effect=RuntimeError('Deliberate validation failure')):
                with self.assertRaises(RuntimeError):
                    SUITE.main(['--runs', '1', '--trials', '1', '--output', temp])
            failure = json.loads((Path(temp) / 'failure.json').read_text())
            self.assertEqual(failure['completed_fixtures'], 0)
            self.assertFalse((Path(temp) / 'report.md').exists())

if __name__ == '__main__':
    unittest.main()
