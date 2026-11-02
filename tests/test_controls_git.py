"""End-to-end mode controls, branch transitions and repository isolation."""
import concurrent.futures
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from test_repoecho import HELPER, repoecho


class ControlAndGitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        (self.root / "Main.java").write_text("class Main { int value = 1; }", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, *args, root=None, success=True):
        result = subprocess.run([sys.executable, str(HELPER), "--root", str(root or self.root), *args],
                                capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        return json.loads(result.stderr)

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def init_git(self):
        if not shutil.which("git"):
            self.skipTest("Git unavailable")
        self.git("init", "-b", "main")
        self.git("config", "user.name", "RepoEcho Test")
        self.git("config", "user.email", "repoecho@example.invalid")
        self.git("add", ".")
        self.git("commit", "-m", "initial")

    def learn(self, summary="Main version one", root=None):
        m = repoecho.Memory(root or self.root)
        try:
            receipt = m.capture(["Main.java"], [], 24000)["receipt"]
            return m.remember({"id": "main", "title": "Main implementation", "summary": summary}, receipt)
        finally:
            m.close()

    def test_default_on_and_status_does_not_create_database(self):
        result = self.cli("mode")
        self.assertTrue(result["controls"]["effective_enabled"])
        self.assertFalse((self.root / ".repoecho").exists())

    def test_mode_off_bypasses_every_data_command(self):
        self.cli("mode", "off")
        commands = [("query", "Main"), ("scan", "--full"), ("plan",), ("status",),
                    ("capture", "--file", "Main.java"),
                    ("remember", "--note", "missing.json", "--receipt", "missing"), ("forget", "main")]
        for command in commands:
            result = self.cli(*command)
            self.assertEqual(result["state"], "bypassed")
            self.assertEqual(result["hits"], [])
        self.assertFalse((self.root / ".repoecho/cache.sqlite3").exists())

    def test_cache_off_preserves_existing_database(self):
        self.learn()
        db = self.root / ".repoecho/cache.sqlite3"
        before = db.read_bytes()
        self.cli("cache", "off")
        result = self.cli("query", "Main")
        self.assertEqual(result["controls"]["skill"], "on")
        self.assertEqual(result["controls"]["bypass_reasons"], ["cache_off"])
        self.assertEqual(db.read_bytes(), before)
        self.cli("cache", "on")
        self.assertEqual(len(self.cli("query", "Main")["hits"]), 1)

    def test_independent_control_precedence(self):
        self.cli("mode", "off")
        self.cli("cache", "off")
        result = self.cli("mode", "on")
        self.assertFalse(result["controls"]["effective_enabled"])
        self.assertEqual(result["controls"]["bypass_reasons"], ["cache_off"])

    def test_changes_while_disabled_are_checked_on_resume(self):
        self.learn()
        self.cli("cache", "off")
        (self.root / "Main.java").write_text("class Main { int value = 2; }", encoding="utf-8")
        self.cli("cache", "on")
        result = self.cli("query", "Main")
        self.assertEqual(result["hits"], [])
        self.assertEqual(len(result["stale"]), 1)

    def test_branch_override_follows_branch_switches(self):
        self.init_git()
        self.cli("branch", "off")
        self.assertFalse(self.cli("mode")["controls"]["effective_enabled"])
        self.git("checkout", "-b", "feature/cache")
        self.assertTrue(self.cli("mode")["controls"]["effective_enabled"])
        self.git("checkout", "main")
        self.assertFalse(self.cli("mode")["controls"]["effective_enabled"])
        self.assertTrue(self.cli("branch", "inherit")["controls"]["effective_enabled"])

    def test_only_current_branch_and_all_reset(self):
        self.init_git()
        result = self.cli("branch", "only")
        self.assertEqual(result["controls"]["branch_default"], "off")
        self.git("checkout", "-b", "other")
        self.assertEqual(self.cli("query", "Main")["state"], "bypassed")
        result = self.cli("branch", "all")
        self.assertTrue(result["controls"]["effective_enabled"])
        self.assertEqual(result["controls"]["branch_overrides"], {})

    def test_detached_head_uses_default_and_rejects_named_override(self):
        self.init_git()
        self.cli("branch", "only")
        self.git("checkout", "--detach")
        result = self.cli("mode")
        self.assertEqual(result["controls"]["branch_kind"], "detached")
        self.assertFalse(result["controls"]["effective_enabled"])
        self.assertIn("named Git branch", self.cli("branch", "on", success=False)["error"])

    def test_plain_directory_controls_work_without_branch(self):
        self.assertIn("named Git branch", self.cli("branch", "off", success=False)["error"])
        self.assertFalse(self.cli("cache", "off")["controls"]["effective_enabled"])

    def test_malformed_controls_fail_closed(self):
        self.cli("mode", "off")
        (self.root / ".repoecho/control.json").write_text('{"skill_enabled": "true"}', encoding="utf-8")
        self.assertIn("Invalid RepoEcho controls", self.cli("query", "Main", success=False)["error"])
        self.assertFalse((self.root / ".repoecho/cache.sqlite3").exists())

    def test_disabled_mode_does_not_open_corrupt_database(self):
        self.cli("cache", "off")
        (self.root / ".repoecho/cache.sqlite3").write_bytes(b"corrupt")
        self.assertEqual(self.cli("query", "Main")["state"], "bypassed")

    def test_concurrent_control_writers_preserve_both_changes(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self.cli, "mode", "off"), pool.submit(self.cli, "cache", "off")]
            for future in futures:
                future.result()
        self.assertEqual(self.cli("mode")["controls"]["bypass_reasons"], ["skill_off", "cache_off"])

    def test_git_status_staged_unstaged_and_untracked(self):
        self.init_git()
        self.cli("scan")
        (self.root / "Main.java").write_text("class Main { int value = 2; }", encoding="utf-8")
        self.git("add", "Main.java")
        (self.root / "Main.java").write_text("class Main { int value = 3; }", encoding="utf-8")
        (self.root / "New.java").write_text("class New {}", encoding="utf-8")
        result = self.cli("scan")["git"]
        self.assertIn("Main.java", result["staged"])
        self.assertIn("Main.java", result["unstaged"])
        self.assertIn("New.java", result["untracked"])
        self.assertTrue(result["dirty"])
        self.assertFalse(any(".repoecho" in x["path"] for x in result["status"]))

    def test_git_warm_scan_reuses_unchanged_untracked_files(self):
        self.init_git()
        (self.root / "New.java").write_text("class New {}", encoding="utf-8")
        self.cli("scan")
        self.assertEqual(self.cli("scan")["hashed"], 0)

    def test_git_diff_and_branch_note_versions_reused_on_return(self):
        self.init_git()
        first = self.learn("Main version one")
        self.git("checkout", "-b", "feature")
        (self.root / "Main.java").write_text("class Main { int value = 2; }", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-m", "version two")
        result = self.cli("query", "Main")
        self.assertEqual(result["hits"], [])
        self.assertTrue(result["scan"]["git"]["branch_changed"])
        self.assertEqual(result["scan"]["git"]["between_heads"], ["Main.java"])
        second = self.learn("Main version two")
        self.assertNotEqual(first["revision"], second["revision"])
        self.git("checkout", "main")
        result = self.cli("query", "Main")
        self.assertEqual(result["hits"][0]["summary"], "Main version one")
        self.assertEqual(result["stale"], [])
        self.git("checkout", "feature")
        self.assertEqual(self.cli("query", "Main")["hits"][0]["summary"], "Main version two")
        self.assertEqual(self.cli("forget", "main")["versions_removed"], 2)

    def test_missing_git_history_forces_full_hash_scan(self):
        self.init_git()
        self.learn()
        m = repoecho.Memory(self.root)
        try:
            with m.db:
                m.set_meta("git_snapshot", json.dumps({"head": "0" * 40, "branch": "gone"}))
        finally:
            m.close()
        result = self.cli("scan")
        self.assertFalse(result["git"]["history_complete"])
        self.assertTrue(result["full"])

    def test_two_repositories_have_independent_notes_and_modes(self):
        self.learn("First repository implementation")
        with tempfile.TemporaryDirectory() as other:
            second = Path(other)
            (second / "Main.java").write_text("class Main { int value = 9; }", encoding="utf-8")
            self.assertEqual(self.cli("query", "Main", root=second)["hits"], [])
            self.learn("Second repository implementation", root=second)
            self.cli("mode", "off")
            result = self.cli("query", "Main", root=second)
            self.assertEqual(result["hits"][0]["summary"], "Second repository implementation")
            self.assertTrue(result["controls"]["effective_enabled"])

    def test_separate_worktree_has_separate_cache(self):
        self.init_git()
        self.learn()
        with tempfile.TemporaryDirectory() as parent:
            worktree = Path(parent) / "checkout"
            self.git("worktree", "add", "-b", "linked", str(worktree))
            result = self.cli("query", "Main", root=worktree)
            self.assertEqual(result["hits"], [])
            self.assertEqual(result["controls"]["current_branch"], "linked")
            self.assertNotEqual(result["scan"]["repository_id"], self.cli("scan")["repository_id"])
            self.git("worktree", "remove", "--force", str(worktree))

    def test_note_history_is_bounded_and_keeps_latest(self):
        (self.root / ".repoecho.json").write_text('{"max_note_versions": 2}', encoding="utf-8")
        for version in range(3):
            (self.root / "Main.java").write_text("class Main { int value = %d; }" % version, encoding="utf-8")
            self.learn("Main version %d" % version)
        self.assertEqual(self.cli("query", "Main")["hits"][0]["summary"], "Main version 2")
        self.assertEqual(self.cli("forget", "main")["versions_removed"], 2)

    def test_benchmark_exercises_warm_and_disabled_modes(self):
        benchmark = Path(__file__).resolve().parents[1] / "tools/benchmark.py"
        result = subprocess.run([sys.executable, str(benchmark), "--files", "12", "--notes", "3", "--runs", "2"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["warm_manifest_files_rehashed"], 0)
        self.assertEqual(data["warm_evidence_files_verified"], 3)
        self.assertEqual(data["stale_versions_rejected"], 1)
        self.assertGreater(data["mode_off_cli"]["median_ms"], 0)


if __name__ == "__main__":
    unittest.main()
