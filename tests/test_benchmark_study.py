import importlib.util
from pathlib import Path
import unittest
SPEC = importlib.util.spec_from_file_location('study', Path(__file__).resolve().parents[1] / 'tools/benchmark_study.py')
STUDY = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(STUDY)


def row(mode, tokens, correct='yes', task='task'):
    return dict(task_id=task, trial='1', model='model', mode=mode, input_tokens=str(tokens),
                output_tokens='100', duration_ms='500', correct=correct)


class StudyTests(unittest.TestCase):
    def test_measured_savings_and_cold_break_even(self):
        data = STUDY.analyse([row('off', 1000), row('warm', 500), row('cold', 2000)])
        self.assertEqual(data['tokens_saved_on_quality_pass_pairs'], 500)
        self.assertEqual(data['pairs'][0]['repeat_uses_to_recover_cold_extra'], 2)

    def test_bad_answers_do_not_count_as_savings(self):
        data = STUDY.analyse([row('off', 1000), row('warm', 100, 'no')])
        self.assertEqual(data['quality_pass_pairs'], 0)
        self.assertIsNone(data['token_reduction_percent'])

    def test_negative_savings_are_preserved(self):
        data = STUDY.analyse([row('off', 100), row('warm', 1000)])
        self.assertLess(data['tokens_saved_on_quality_pass_pairs'], 0)

    def test_invalid_and_unpaired_data_rejected(self):
        for rows in [[row('off', 1)], [row('off', 1), row('warm', 'nan')],
                     [row('off', 1), row('warm', 1), row('warm', 2)],
                     [row('off', 1), row('warm', 1.5)]]:
            with self.assertRaises(ValueError):
                STUDY.analyse(rows)
