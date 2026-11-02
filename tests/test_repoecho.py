"""Behavioral tests: source changes must never yield stale knowledge."""
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

PROJECT = Path(__file__).resolve().parents[1]
HELPER = Path(os.environ.get("REPOECHO_HELPER", PROJECT / ".github/skills/repoecho/scripts/repoecho.py"))
spec = importlib.util.spec_from_file_location("repoecho", HELPER)
repoecho = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repoecho)


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.memory = None
        self.write("pom.xml", "<project><properties><maven.compiler.release>8</maven.compiler.release></properties></project>")
        self.write("src/main/java/example/ProcessManager.java", "package example;\npublic class ProcessManager { public void stop() {} }\n")
        self.source = "src/main/java/example/ProcessManager.java"

    def tearDown(self):
        if self.memory:
            self.memory.close()
        self.temp.cleanup()

    def write(self, path, content):
        dest = self.root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            dest.write_bytes(content)
        else:
            dest.write_text(content, encoding="utf-8")

    def open(self):
        if self.memory:
            self.memory.close()
        self.memory = repoecho.Memory(self.root)
        return self.memory

    def note(self, note_id="process", summary="ProcessManager owns process lifecycle and shutdown."):
        return {"id": note_id, "title": "Process lifecycle", "summary": summary,
                "facts": [self.source + ":2 declares stop()."], "tags": ["java", "shutdown"]}

    def learn(self, scopes=(), files=None, note_id="process"):
        m = self.memory or self.open()
        capture = m.capture(files or [self.source, "pom.xml"], scopes, 24000)
        m.remember(self.note(note_id), capture["receipt"])
        return m

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def git_init(self):
        if not shutil.which("git"):
            self.skipTest("Git unavailable")
        self.git("init", "-b", "main")
        self.git("config", "user.name", "RepoEcho Test")
        self.git("config", "user.email", "repoecho@example.invalid")

    def test_cold_then_warm_scan(self):
        m = self.open()
        cold, warm = m.scan(), m.scan()
        self.assertEqual(cold["hashed"], 2)
        self.assertEqual(warm["hashed"], 0)
        self.assertEqual(warm["stat_reused"], 2)
        self.assertEqual(m.scan(True)["hashed"], 2)

    def test_persists_across_sessions(self):
        self.learn()
        result = self.open().query("shutdown")
        self.assertEqual(result["hits"][0]["id"], "process")
        self.assertIn("verified_at", result["hits"][0])
        self.assertEqual(result["hits"][0]["freshness"], "content_verified")
        self.assertEqual(result["source_files_verified"], 2)

    def test_changed_source_withholds_body(self):
        m = self.learn()
        self.write(self.source, "public class Changed {}")
        result = m.query("shutdown")
        self.assertEqual(result["hits"], [])
        self.assertNotIn("ProcessManager owns", json.dumps(result))
        self.assertIn("source_changed", result["stale"][0]["reason"])

    def test_same_size_and_restored_mtime(self):
        m = self.learn()
        path = self.root / self.source
        old_stat = path.stat()
        self.write(self.source, path.read_text().replace("stop", "halt"))
        os.utime(path, ns=(old_stat.st_atime_ns, old_stat.st_mtime_ns))
        self.assertEqual(m.query("shutdown")["hits"], [])

    def test_windows_stat_and_fstat_ctime_differ_for_unchanged_file(self):
        m = self.open()
        real_fstat = os.fstat
        def descriptor_stat(fd):
            value = real_fstat(fd)
            return SimpleNamespace(st_size=value.st_size, st_mtime_ns=value.st_mtime_ns,
                                   st_ctime_ns=value.st_ctime_ns + 1_000_000,
                                   st_ino=value.st_ino, st_dev=value.st_dev, st_mode=value.st_mode)
        with mock.patch.object(repoecho.os, "fstat", side_effect=descriptor_stat):
            self.learn()
            result = m.query("shutdown")
        self.assertEqual(len(result["hits"]), 1)
        self.assertEqual(result["scan"]["hashed"], 0)

    def test_descriptor_timestamp_change_during_read_still_rejected(self):
        m = self.open()
        real_fstat = os.fstat
        count = 0
        def changing_stat(fd):
            nonlocal count
            count += 1
            value = real_fstat(fd)
            return SimpleNamespace(st_size=value.st_size, st_mtime_ns=value.st_mtime_ns,
                                   st_ctime_ns=value.st_ctime_ns + count,
                                   st_ino=value.st_ino, st_dev=value.st_dev, st_mode=value.st_mode)
        with mock.patch.object(repoecho.os, "fstat", side_effect=changing_stat):
            with self.assertRaisesRegex(repoecho.CacheError, "changed during read"):
                m.read_source(self.source)

    def test_strict_query_rehashes_even_if_manifest_signature_lies(self):
        m = self.learn()
        old = m.db.execute("SELECT hash FROM files WHERE path=?", (self.source,)).fetchone()[0]
        self.write(self.source, "different content")
        sig = repoecho.packed(repoecho.signature((self.root / self.source).stat()))
        with m.db:
            m.db.execute("UPDATE files SET hash=?, sig=? WHERE path=?", (old, sig, self.source))
        result = m.query("shutdown")
        self.assertEqual(result["scan"]["hashed"], 0)
        self.assertEqual(result["hits"], [])

    def test_delete_and_rename_invalidate(self):
        m = self.learn()
        (self.root / self.source).rename(self.root / "Renamed.java")
        self.assertEqual(m.query("process")["hits"], [])

    def test_scope_addition_invalidates(self):
        m = self.learn(scopes=["src/main/java/example/**"])
        self.write("src/main/java/example/NewManager.java", "class NewManager {}")
        result = m.query("process")
        self.assertEqual(result["hits"], [])
        self.assertTrue(result["stale"][0]["reason"].startswith("scope_changed"))

    def test_empty_scope_detects_first_member(self):
        m = self.learn(scopes=["plugins/**"])
        self.write("plugins/New.java", "class New {}")
        self.assertEqual(m.query("process")["hits"], [])

    def test_scope_change_of_uncaptured_file_invalidates(self):
        self.write("src/main/java/example/Other.java", "class Other {}")
        m = self.learn(scopes=["src/main/java/example/**"])
        self.write("src/main/java/example/Other.java", "class Other { int x; }")
        self.assertEqual(m.query("process")["hits"], [])

    def test_new_maven_module_invalidates_build_scope(self):
        m = self.learn(scopes=["**/pom.xml"])
        self.write("new-module/pom.xml", "<project/>")
        self.assertEqual(m.query("process")["hits"], [])

    def test_unrelated_change_preserves_note(self):
        m = self.learn(scopes=["src/main/java/example/**"])
        self.write("docs/unrelated.md", "Unrelated documentation")
        self.assertEqual(len(m.query("process")["hits"]), 1)

    def test_parent_pom_change_invalidates_module_note(self):
        m = self.learn()
        self.write("pom.xml", "<project><version>2</version></project>")
        self.assertEqual(m.query("process")["hits"], [])

    def test_capture_save_race_rejected(self):
        m = self.open()
        captured = m.capture([self.source], [], 24000)
        self.write(self.source, "changed after capture")
        with self.assertRaisesRegex(repoecho.CacheError, "Evidence changed"):
            m.remember(self.note(), captured["receipt"])
        self.assertEqual(m.query("process")["hits"], [])

    def test_scope_capture_save_race_rejected(self):
        m = self.open()
        captured = m.capture([self.source], ["**/pom.xml"], 24000)
        self.write("new/pom.xml", "<project/>")
        with self.assertRaisesRegex(repoecho.CacheError, "scope_changed"):
            m.remember(self.note(), captured["receipt"])

    def test_receipt_single_use_and_update_by_id(self):
        m = self.open()
        captured = m.capture([self.source], [], 24000)
        m.remember(self.note(), captured["receipt"])
        with self.assertRaisesRegex(repoecho.CacheError, "consumed"):
            m.remember(self.note(), captured["receipt"])
        captured = m.capture([self.source], [], 24000)
        m.remember(self.note(summary="Replacement shutdown note"), captured["receipt"])
        result = m.query("shutdown")
        self.assertEqual(len(result["hits"]), 1)
        self.assertEqual(result["hits"][0]["summary"], "Replacement shutdown note")

    def test_receipt_expiry(self):
        m = self.open()
        captured = m.capture([self.source], [], 24000)
        with m.db:
            m.db.execute("UPDATE receipts SET created=0")
        with self.assertRaisesRegex(repoecho.CacheError, "24 hours"):
            m.remember(self.note(), captured["receipt"])

    def test_note_expiry(self):
        m = self.learn()
        row = m.db.execute("SELECT payload FROM notes").fetchone()[0]
        note = json.loads(row)
        note["evidence"]["expires_epoch"] = 1
        with m.db:
            m.db.execute("UPDATE notes SET payload=?", (json.dumps(note),))
        result = m.query("process")
        self.assertEqual(result["hits"], [])
        self.assertEqual(result["stale"][0]["reason"], "review_expired")

    def test_configuration_change_invalidates(self):
        self.learn()
        self.write(".repoecho.json", '{"note_ttl_days": 14}')
        result = self.open().query("process")
        self.assertEqual(result["hits"], [])
        self.assertEqual(result["stale"][0]["reason"], "skill_or_configuration_changed")

    def test_policy_change_invalidates(self):
        m = self.learn()
        m.policy = "updated-policy"
        self.assertEqual(m.query("process")["hits"], [])

    def test_periodic_full_verification(self):
        m = self.open()
        m.scan()
        with m.db:
            m.set_meta("full_verified", "0")
        self.assertTrue(m.scan()["full"])

    def test_query_and_capture_budgets(self):
        m = self.learn()
        result = m.query("process", max_chars=1)
        self.assertEqual(result["hits"], [])
        self.assertEqual(result["budget_omitted"], 1)
        with self.assertRaisesRegex(repoecho.CacheError, "exceeds"):
            m.capture([self.source], [], 1)

    def test_invalid_note_does_not_consume_receipt(self):
        m = self.open()
        receipt = m.capture([self.source], [], 24000)["receipt"]
        note = self.note()
        note["evidence"] = "forged"
        with self.assertRaises(repoecho.CacheError):
            m.remember(note, receipt)
        m.remember(self.note(), receipt)
        self.assertEqual(len(m.query("")["hits"]), 1)

    def test_generated_secrets_binary_and_size_exclusions(self):
        for path in ("target/Gen.java", "build/Gen.java", "node_modules/a.js", ".env", "keys/key.pem", "credentials.json"):
            self.write(path, "must not index")
        self.write("opaque.dat", b"abc\x00xyz")
        self.write("legacy.txt", b"\xff\xfeabc")
        self.write("large.txt", "a" * 1_048_577)
        m = self.open()
        m.scan()
        self.assertEqual(set(m.manifest), {self.source, "pom.xml"})

    def test_extra_ignore_patterns(self):
        self.write(".repoechoignore", "# comment\n**/generated/**\nprivate/\n")
        self.write("mod/generated/a.java", "class X {}")
        self.write("private/a.txt", "private")
        m = self.open()
        m.scan()
        self.assertNotIn("mod/generated/a.java", m.manifest)
        self.assertNotIn("private/a.txt", m.manifest)

    def test_glob_zero_segments_and_boundaries(self):
        match = repoecho.pattern_matches
        self.assertTrue(match("pom.xml", "**/pom.xml"))
        self.assertTrue(match("a/b/pom.xml", "**/pom.xml"))
        self.assertTrue(match("src/Foo.java", "src/**/*.java"))
        self.assertFalse(match("src/deep/Foo.java", "src/*.java"))
        self.assertFalse(match("src2/Foo.java", "src/**"))

    def test_path_traversal_and_symlink_rejection(self):
        m = self.open()
        with self.assertRaises(repoecho.CacheError):
            m.safe_path("../outside")
        try:
            (self.root / "linked.java").symlink_to(self.root / self.source)
        except OSError:
            self.skipTest("Symlink permission unavailable")
        m.scan()
        self.assertNotIn("linked.java", m.manifest)
        with self.assertRaises(repoecho.CacheError):
            m.capture(["linked.java"], [], 24000)

    def test_cache_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as other:
            try:
                (self.root / ".repoecho").symlink_to(other, target_is_directory=True)
            except OSError:
                self.skipTest("Symlink permission unavailable")
            with self.assertRaisesRegex(repoecho.CacheError, "real local"):
                repoecho.Memory(self.root)

    def test_copied_cache_rejected(self):
        self.learn()
        self.memory.close()
        self.memory = None
        with tempfile.TemporaryDirectory() as other:
            shutil.copytree(self.root / ".repoecho", Path(other) / ".repoecho")
            with self.assertRaisesRegex(repoecho.CacheError, "another checkout"):
                repoecho.Memory(other)

    def test_fts_and_fallback_identifier_search(self):
        m = self.learn()
        for backend in (m.fts, False):
            m.fts = backend
            self.assertEqual(len(m.query("process manager")["hits"]), 1)
            self.assertEqual(len(m.query('" OR * shutdown :')["hits"]), 1)

    def test_forget_removes_search_result(self):
        m = self.learn()
        self.assertTrue(m.forget("process")["existed"])
        self.assertFalse(m.forget("process")["existed"])
        self.assertEqual(m.query("shutdown")["hits"], [])

    def test_multiple_languages_and_unicode_paths(self):
        for path in ("web/package.json", "api/pyproject.toml", "worker/Cargo.toml", "svc/go.mod", "lib/build.gradle.kts", "資料/guide.md"):
            self.write(path, "valid UTF-8 résumé")
        result = self.open().plan()
        self.assertIn("worker/Cargo.toml", result["build_files"])
        self.assertIn("lib/build.gradle.kts", result["build_files"])
        self.assertIn("資料/guide.md", self.memory.manifest)

    def test_status_does_not_pretend_verified(self):
        m = self.learn()
        result = m.plan()
        self.assertEqual(result["notes"][0]["state"], "candidate_needs_query_verification")
        self.assertNotIn("ProcessManager owns", json.dumps(result))

    def test_git_ignore_untracked_staged_and_dirty_content(self):
        self.git_init()
        self.write(".gitignore", "ignored.txt\n")
        self.write("ignored.txt", "ignored")
        self.git("add", "pom.xml", self.source, ".gitignore")
        self.git("commit", "-m", "fixture")
        m = self.learn()
        self.assertNotIn("ignored.txt", m.manifest)
        self.write(self.source, "dirty content")
        self.git("add", self.source)
        self.assertEqual(m.query("process")["hits"], [])
        self.assertNotIn(".repoecho", self.git("status", "--porcelain", "--untracked-files=all"))

    def test_branch_change_and_revert(self):
        self.git_init()
        self.git("add", ".")
        self.git("commit", "-m", "fixture")
        m = self.learn()
        self.git("checkout", "-b", "other")
        self.write(self.source, "branch variant")
        self.git("add", ".")
        self.git("commit", "-m", "variant")
        self.assertEqual(m.query("shutdown")["hits"], [])
        self.git("checkout", "main")
        self.assertEqual(len(m.query("shutdown")["hits"]), 1)

    def test_git_subdirectory_is_bounded(self):
        self.git_init()
        self.write("module/src/Foo.java", "class Foo {}")
        self.git("add", ".")
        m = repoecho.Memory(self.root / "module")
        try:
            m.scan()
            self.assertEqual(set(m.manifest), {"src/Foo.java"})
        finally:
            m.close()

    def test_concurrent_processes_and_json_cli(self):
        self.learn()
        self.memory.close()
        self.memory = None
        command = [sys.executable, str(HELPER), "--root", str(self.root), "query", "shutdown"]
        def run(_):
            return subprocess.run(command, capture_output=True, text=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for result in pool.map(run, range(8)):
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["hits"][0]["id"], "process")

    def test_corrupt_cache_fails_closed(self):
        cache = self.root / ".repoecho"
        cache.mkdir()
        (cache / "cache.sqlite3").write_bytes(b"not a database")
        result = subprocess.run([sys.executable, str(HELPER), "--root", str(self.root), "query", "anything"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("error", json.loads(result.stderr))

    def test_invalid_configuration(self):
        for value in ('{"unknown": 1}', '{"note_ttl_days": 0}', '{"exclude": "src"}', '{"full_verify_hours": NaN}'):
            self.write(".repoecho.json", value)
            with self.assertRaises(repoecho.CacheError):
                repoecho.Memory(self.root)

    def test_no_source_blobs_in_database(self):
        m = self.learn()
        dump = "\n".join(m.db.iterdump())
        self.assertNotIn("public class ProcessManager {", dump)


if __name__ == "__main__":
    unittest.main()
