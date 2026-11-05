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

    def test_focused_query_skips_unrelated_files_but_preserves_manifest(self):
        self.write("other/Large.java", "class Large {}")
        m = self.learn()
        original = m.read_source
        def guarded(path):
            self.assertNotEqual(path, "other/Large.java")
            return original(path)
        self.write("other/Large.java", "class Changed {}")
        with mock.patch.object(m, "read_source", side_effect=guarded):
            result = m.query("shutdown")
        self.assertEqual(len(result["hits"]), 1)
        self.assertEqual(result["scan"]["scope"], "candidate_evidence")
        self.assertEqual(result["scan"]["paths_considered"], 2)
        self.assertIsNotNone(m.db.execute("SELECT path FROM files WHERE path='other/Large.java'").fetchone())
        self.assertGreater(m.scan()["changed"], 0)

    def test_focused_scope_checks_new_members_after_unrelated_query(self):
        self.learn(scopes=["src/**"])
        self.write("src/Added.java", "class Added {}")
        self.assertEqual(self.memory.query("no_such_topic")["hits"], [])
        result = self.memory.query("shutdown")
        self.assertEqual(result["hits"], [])
        self.assertIn("scope_changed", result["stale"][0]["reason"])

    def test_capture_hints_do_not_forge_read_evidence(self):
        captured = self.open().capture([self.source], [], 24000)
        self.assertEqual(captured["coverage_hints"]["uncaptured_ancestor_build_files"], ["pom.xml"])
        self.assertNotIn("pom.xml", captured["evidence"]["sources"])
        self.assertEqual([item["path"] for item in captured["files"]], [self.source])

    def test_note_limit_preserves_existing_history_and_receipt(self):
        self.write(".repoecho.json", '{"max_note_revisions": 1}')
        m = self.learn()
        captured = m.capture([self.source], [], 24000)
        with self.assertRaisesRegex(repoecho.CacheError, "limit reached"):
            m.remember(self.note("another"), captured["receipt"])
        self.assertEqual(m.storage()["note_revisions"], 1)
        self.assertIsNotNone(m.db.execute("SELECT id FROM receipts WHERE id=?", (captured["receipt"],)).fetchone())
        self.assertEqual(m.query("shutdown")["hits"][0]["id"], "process")

    def test_note_limit_reclaims_expired_history_before_rejecting_save(self):
        self.write(".repoecho.json", '{"max_note_revisions": 1}')
        m = self.learn()
        row = m.db.execute("SELECT id,payload FROM notes").fetchone()
        payload = json.loads(row["payload"])
        payload["evidence"]["expires_epoch"] = 1
        with m.db:
            m.db.execute("UPDATE notes SET payload=? WHERE id=?", (repoecho.packed(payload), row["id"]))
        receipt = m.capture([self.source], [], 24000)["receipt"]
        m.remember(self.note("new"), receipt)
        self.assertEqual(m.storage()["note_revisions"], 1)
        self.assertEqual(m.query("shutdown")["hits"][0]["id"], "new")

    def test_receipt_limit_bounds_abandoned_learning(self):
        self.write(".repoecho.json", '{"max_receipts": 1}')
        m = self.open()
        first = m.capture([self.source], [], 24000)
        with self.assertRaisesRegex(repoecho.CacheError, "receipt limit"):
            m.capture([self.source], [], 24000)
        m.remember(self.note(), first["receipt"])
        self.assertIn("receipt", m.capture([self.source], [], 24000))

    def test_sqlite_budget_rolls_back_without_losing_notes(self):
        self.write(".repoecho.json", '{"max_cache_mb": 1}')
        m = self.learn()
        m.db.execute("CREATE TABLE quota_probe (value BLOB)")
        with self.assertRaises(sqlite3.OperationalError):
            with m.db:
                m.db.execute("INSERT INTO quota_probe VALUES (?)", (b"x" * (2 * 1024 * 1024),))
        self.assertLessEqual(m.storage()["database_allocated_bytes"], 1024 * 1024)
        self.assertEqual(m.db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertEqual(len(m.query("shutdown")["hits"]), 1)

    def test_prune_removes_only_expired_history_and_compacts(self):
        m = self.learn()
        self.learn(note_id="expired")
        row = m.db.execute("SELECT id,payload FROM notes WHERE id LIKE 'expired@%'").fetchone()
        payload = json.loads(row["payload"])
        payload["evidence"]["expires_epoch"] = 1
        with m.db:
            m.db.execute("UPDATE notes SET payload=? WHERE id=?", (repoecho.packed(payload), row["id"]))
        result = m.prune(compact=True)
        self.assertTrue(result["compacted"])
        self.assertEqual(result["expired_note_revisions_removed"], 1)
        self.assertEqual(result["storage"]["note_revisions"], 1)
        self.assertEqual(m.query("shutdown")["hits"][0]["id"], "process")

    def test_daily_prune_cleans_expired_notes_without_renewing_valid_notes(self):
        m = self.learn()
        expiry = m.query("shutdown")["hits"][0]["evidence"]["expires_epoch"]
        self.learn(note_id="expired")
        row = m.db.execute("SELECT id,payload FROM notes WHERE id LIKE 'expired@%'").fetchone()
        payload = json.loads(row["payload"])
        payload["evidence"]["expires_epoch"] = 1
        with m.db:
            m.db.execute("UPDATE notes SET payload=? WHERE id=?", (repoecho.packed(payload), row["id"]))
            m.set_meta("last_prune", 0)
        result = m.query("shutdown")
        self.assertEqual(m.storage()["note_revisions"], 1)
        self.assertEqual(result["hits"][0]["evidence"]["expires_epoch"], expiry)

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

    def make_legacy_notes(self):
        """Reproduce schema-1 storage before compatibility was explicit."""
        m = self.memory
        rows = m.db.execute("SELECT * FROM notes").fetchall()
        with m.db:
            for row in rows:
                note = json.loads(row["payload"])
                note["evidence"].pop("compatibility", None)
                note["evidence"]["policy"] = repoecho.digest("old release and skill files")
                note["revision"] = repoecho.digest({k: note["evidence"][k] for k in ("policy", "sources", "scopes")})
                storage_id = note["id"] + "@" + note["revision"]
                m.db.execute("DELETE FROM notes WHERE id=?", (row["id"],))
                m.db.execute("INSERT INTO notes VALUES (?,?,?,?)",
                             (storage_id, repoecho.packed(note), row["search"], row["generated_at"]))
                if m.fts:
                    m.db.execute("DELETE FROM search_notes WHERE id=?", (row["id"],))
                    m.db.execute("INSERT INTO search_notes VALUES (?,?)", (storage_id, row["search"]))
        return [json.loads(r[0]) for r in m.db.execute("SELECT payload FROM notes")]

    def test_release_code_and_docs_changes_preserve_cache_and_receipts(self):
        m = self.learn()
        before = m.query("shutdown")["hits"][0]
        receipt = m.capture([self.source], [], 24000)["receipt"]
        with tempfile.TemporaryDirectory() as updated:
            skill = Path(updated)
            (skill / "scripts").mkdir()
            (skill / "references").mkdir()
            script = skill / "scripts/repoecho.py"
            script.write_text("# Updated helper implementation\n")
            (skill / "SKILL.md").write_text("Updated instructions")
            (skill / "references/cache-contract.md").write_text("Updated documentation")
            with mock.patch.object(repoecho, "VERSION", "9.9.9"), mock.patch.object(repoecho, "__file__", str(script)):
                m = self.open()
                after = m.query("shutdown")["hits"][0]
                self.assertEqual(after["revision"], before["revision"])
                self.assertEqual(after["evidence"], before["evidence"])
                self.assertEqual(m.scan()["hashed"], 0)
                m.remember(self.note("second"), receipt)

    def test_legacy_upgrade_preserves_dates_and_deduplicates(self):
        self.learn(scopes=["src/**"])
        old = self.make_legacy_notes()[0]
        m = self.open()
        self.assertEqual(m.plan()["notes"][0]["state"], "candidate_needs_query_verification")
        hit = m.query("shutdown")["hits"][0]
        self.assertEqual(hit["evidence"]["compatibility"], repoecho.CACHE_COMPATIBILITY)
        self.assertEqual(hit["generated_at"], old["generated_at"])
        for key in ("captured_at", "expires_epoch", "expires_at", "origin", "sources", "scopes"):
            self.assertEqual(hit["evidence"][key], old["evidence"][key])
        self.assertEqual(m.db.execute("SELECT COUNT(*) FROM notes").fetchone()[0], 1)
        self.learn(scopes=["src/**"])
        self.assertEqual(m.db.execute("SELECT COUNT(*) FROM notes").fetchone()[0], 1)
        self.assertEqual(len(self.open().query("shutdown")["hits"]), 1)

    def test_legacy_duplicate_merges_branch_origins(self):
        m = self.learn()
        legacy = self.make_legacy_notes()[0]
        legacy["evidence"]["origin"]["branch"] = "main"
        with m.db:
            m.db.execute("UPDATE notes SET payload=?", (repoecho.packed(legacy),))
        capture = m.capture([self.source, "pom.xml"], [], 24000)
        capture["evidence"]["origin"]["branch"] = "feature"
        with m.db:
            m.db.execute("UPDATE receipts SET payload=? WHERE id=?",
                         (repoecho.packed(capture["evidence"]), capture["receipt"]))
        m.remember(self.note(), capture["receipt"])
        m.scan()
        self.assertIsNone(m.validity(legacy["evidence"], allow_legacy=True))
        m.adopt_compatible_note(legacy)
        rows = m.db.execute("SELECT payload FROM notes").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads(rows[0][0])["evidence"]["origin"]["branches"], ["feature", "main"])
        self.assertEqual(len(m.query("shutdown")["hits"]), 1)

    def test_legacy_changed_scope_is_withheld_until_restored(self):
        self.learn(scopes=["src/**"])
        self.make_legacy_notes()
        self.write("src/Added.java", "class Added {}")
        m = self.open()
        self.assertEqual(m.query("shutdown")["hits"], [])
        stored = json.loads(m.db.execute("SELECT payload FROM notes").fetchone()[0])
        self.assertNotIn("compatibility", stored["evidence"])
        (self.root / "src/Added.java").unlink()
        self.assertEqual(len(m.query("shutdown")["hits"]), 1)

    def test_legacy_excluded_source_is_withheld(self):
        self.learn()
        self.make_legacy_notes()
        self.write(".repoecho.json", json.dumps({"exclude": [self.source]}))
        result = self.open().query("shutdown")
        self.assertEqual(result["hits"], [])
        self.assertIn("source_changed_or_removed", result["stale"][0]["reason"])

    def test_legacy_expiry_is_not_renewed(self):
        m = self.learn()
        self.make_legacy_notes()
        row = json.loads(m.db.execute("SELECT payload FROM notes").fetchone()[0])
        row["evidence"]["expires_epoch"] = 1
        with m.db:
            m.db.execute("UPDATE notes SET payload=?", (repoecho.packed(row),))
        result = self.open().query("shutdown")
        self.assertEqual(result["hits"], [])
        self.assertEqual(result["stale"][0]["reason"], "review_expired")

    def test_incompatible_contract_rejects_notes_and_receipts(self):
        m = self.learn()
        receipt = m.capture([self.source], [], 24000)["receipt"]
        with mock.patch.object(repoecho, "CACHE_COMPATIBILITY", 2):
            m = self.open()
            result = m.query("shutdown")
            self.assertEqual(result["hits"], [])
            self.assertEqual(result["stale"][0]["reason"], "cache_compatibility_changed")
            with self.assertRaisesRegex(repoecho.CacheError, "cache_compatibility_changed"):
                m.remember(self.note(), receipt)
            self.make_legacy_notes()
            self.assertEqual(m.query("shutdown")["hits"], [])

    def test_legacy_receipt_requires_recapture(self):
        m = self.open()
        captured = m.capture([self.source], [], 24000)
        evidence = captured["evidence"]
        evidence.pop("compatibility")
        with m.db:
            m.db.execute("UPDATE receipts SET payload=?", (repoecho.packed(evidence),))
        with self.assertRaisesRegex(repoecho.CacheError, "recapture"):
            m.remember(self.note(), captured["receipt"])

    def test_operational_configuration_preserves_notes_and_receipts(self):
        m = self.learn()
        before = m.query("process")["hits"][0]
        captured = m.capture([self.source], [], 24000)
        self.write(".repoecho.json", json.dumps({"note_ttl_days": 14, "full_verify_hours": 2, "max_note_versions": 3}))
        m = self.open()
        after = m.query("process")["hits"][0]
        self.assertEqual(after["revision"], before["revision"])
        self.assertEqual(after["evidence"]["expires_epoch"], before["evidence"]["expires_epoch"])
        m.remember(self.note("second"), captured["receipt"])

    def test_exclusions_only_withhold_affected_evidence(self):
        self.learn()
        self.write(".repoecho.json", json.dumps({"exclude": ["unrelated/**"]}))
        self.assertEqual(len(self.open().query("process")["hits"]), 1)
        self.write(".repoecho.json", json.dumps({"exclude": [self.source]}))
        self.assertEqual(self.open().query("process")["hits"], [])
        self.write(".repoecho.json", "{}")
        self.assertEqual(len(self.open().query("process")["hits"]), 1)

    def test_133_policy_is_upgraded_with_dates_intact(self):
        m = self.learn()
        row = json.loads(m.db.execute("SELECT payload FROM notes").fetchone()[0])
        row["evidence"]["policy"] = repoecho.digest({"compatibility": 1, "config": m.config, "exclude": m.excludes})
        with m.db:
            m.db.execute("UPDATE notes SET payload=?", (repoecho.packed(row),))
        hit = self.open().query("process")["hits"][0]
        self.assertEqual(hit["evidence"]["expires_epoch"], row["evidence"]["expires_epoch"])
        self.assertEqual(hit["evidence"]["policy"], self.memory.policy)

    def test_git_environment_cannot_redirect_repo_discovery(self):
        self.git_init()
        self.git("add", ".")
        self.git("commit", "-m", "fixture")
        self.write(".gitignore", "private.txt\n")
        self.write("private.txt", "ignored data")
        with mock.patch.dict(os.environ, {"GIT_DIR": str(self.root / "wrong.git"),
                                         "GIT_WORK_TREE": str(self.root / "wrong"),
                                         "GIT_INDEX_FILE": str(self.root / "wrong-index")}):
            m = self.open()
            self.assertEqual(m.scan()["git"]["branch"], "main")
            self.assertNotIn("private.txt", m.manifest)
            self.assertEqual(repoecho.Controls(self.root).report()["current_branch"], "main")

    def test_missing_git_does_not_bypass_gitignore(self):
        self.git_init()
        self.write(".gitignore", "private.txt\n")
        self.write("private.txt", "ignored data")
        with mock.patch.object(repoecho.shutil, "which", return_value=None):
            with self.assertRaisesRegex(repoecho.CacheError, "Git is required"):
                self.open().scan()
            with self.assertRaisesRegex(repoecho.CacheError, "Git is required"):
                repoecho.Controls(self.root)

    def test_plain_directory_works_without_git(self):
        with mock.patch.object(repoecho.shutil, "which", return_value=None):
            self.assertEqual(self.open().scan()["files"], 2)

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

    def test_natural_language_aliases_both_backends_and_freshness(self):
        m = self.open()
        capture = m.capture([self.source], [], 24000)
        note = self.note()
        note["aliases"] = ["terminate a running job", "end worker execution"]
        m.remember(note, capture["receipt"])
        m = self.open()  # Persisted aliases survive a new session.
        for backend in (m.fts, False):
            m.fts = backend
            for query in ("terminate job", "worker execution"):
                hits = m.query(query)["hits"]
                self.assertEqual([n["id"] for n in hits], ["process"])
                self.assertEqual(hits[0]["freshness"], "content_verified")
            self.assertEqual(m.query("invoice settlement")["hits"], [])
        self.write(self.source, "changed evidence")
        self.assertEqual(m.query("terminate job")["hits"], [])

    def test_alias_validation_and_update_same_revision(self):
        m = self.learn()
        capture = m.capture([self.source, "pom.xml"], [], 24000)
        note = self.note()
        note["aliases"] = "not a list"
        with self.assertRaisesRegex(repoecho.CacheError, "aliases must"):
            m.remember(note, capture["receipt"])
        note["aliases"] = ["halt worker"]
        m.remember(note, capture["receipt"])
        self.assertEqual(len(m.query("halt worker")["hits"]), 1)
        self.assertEqual(m.db.execute("SELECT COUNT(*) FROM notes").fetchone()[0], 1)

    def test_compact_preserves_knowledge_and_rejects_stale_evidence(self):
        m = self.learn()
        full = m.query("shutdown")
        compact = m.query("shutdown", compact=True)
        for key in ("id", "title", "summary", "facts", "inferences", "caveats", "freshness"):
            self.assertEqual(compact["hits"][0][key], full["hits"][0][key])
        self.assertEqual(compact["hits"][0]["sources"], list(full["hits"][0]["evidence"]["sources"]))
        self.assertNotIn("evidence", compact["hits"][0])
        self.assertLess(len(repoecho.packed(compact)), len(repoecho.packed(full)))
        self.assertEqual(m.query("shutdown", max_chars=1, compact=True)["hits"], [])
        self.write(self.source, "changed")
        result = m.query("shutdown", compact=True)
        self.assertEqual(result["hits"], [])
        self.assertTrue(result["stale"])

    def test_context_estimate_uses_verified_sources_and_compact_payload(self):
        source_text = "class ProcessManager {\n" + ("    void run() {}\n" * 500) + "}\n"
        self.write(self.source, source_text)
        m = self.open()
        receipt = m.capture([self.source], [], 24000)["receipt"]
        m.remember({"id": "workflow", "title": "Process run", "summary": "Runs work."}, receipt)
        response = m.query("process run", compact=True)
        estimate = response["context_estimate"]
        self.assertEqual(estimate["source_chars"], len((self.root / self.source).read_bytes().decode("utf-8")))
        self.assertEqual(estimate["verified_source_files"], 1)
        self.assertGreater(estimate["estimated_tokens_avoided"], 0)
        self.assertEqual(estimate["returned_note_chars"], response["content_chars"])
        self.write(self.source, "changed")
        stale = m.query("process run", compact=True)
        self.assertEqual(stale["hits"], [])
        self.assertEqual(stale["context_estimate"]["estimated_tokens_avoided"], 0)

    def test_context_estimate_deduplicates_shared_source_files(self):
        self.write(self.source, "class ProcessManager {}\n" * 300)
        m = self.open()
        for note_id in ("process-first", "process-second"):
            receipt = m.capture([self.source], [], 24000)["receipt"]
            m.remember({"id": note_id, "title": "Process manager", "summary": "Process evidence."}, receipt)
        result = m.query("process", limit=2, compact=True)
        self.assertEqual(len(result["hits"]), 2)
        self.assertEqual(result["context_estimate"]["verified_source_files"], 1)
        self.assertEqual(result["context_estimate"]["source_chars"], len((self.root / self.source).read_bytes().decode("utf-8")))

    def test_intent_and_component_ranking_with_branch_changes(self):
        self.write("src/HostController.java", "class HostController { void stopHost() {} }")
        m = self.open()
        cases = [
            ("host-stop", "Stop host service", "host shutdown", ["stop a host", "halt host service"], "src/HostController.java"),
            ("process-stop", "Stop running process", "process shutdown", ["stop a running job", "terminate process"], self.source),
        ]
        for note_id, title, summary, aliases, path in cases:
            receipt = m.capture([path], [], 24000)["receipt"]
            m.remember({"id": note_id, "title": title, "summary": summary,
                        "aliases": aliases, "facts": [path + ":1 handles stopping."]}, receipt)
        for backend in (m.fts, False):
            m.fts = backend
            self.assertEqual(m.query("What happens when I stop a running job?", limit=1)["hits"][0]["id"], "process-stop")
            self.assertEqual(m.query("How do I halt the host service?", limit=1)["hits"][0]["id"], "host-stop")
            self.assertEqual(m.query("invoice settlement", limit=1)["hits"], [])
        self.write(self.source, "changed process")
        result = m.query("stop a running job", limit=1)
        self.assertEqual(result["hits"], [])
        self.assertIn("process-stop", [x["id"] for x in result["stale"]])

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

    def test_same_file_two_branch_versions_selected_on_each_switch(self):
        self.git_init()
        self.git("add", ".")
        self.git("commit", "-m", "main source")
        m = self.open()
        main_receipt = m.capture([self.source], [], 24000)["receipt"]
        m.remember({"id": "workflow-stop", "title": "Stop process", "summary": "Main stops immediately.",
                    "aliases": ["stop running job"]}, main_receipt)
        main_rev = m.query("stop running job", limit=1, compact=True)["hits"][0]["summary"]
        self.git("switch", "-c", "feature")
        self.write(self.source, "package example; class ProcessManager { void stop() { /* drain */ } }\n")
        self.git("add", self.source)
        self.git("commit", "-m", "feature source")
        self.assertEqual(m.query("stop running job")["hits"], [])
        feature_receipt = m.capture([self.source], [], 24000)["receipt"]
        m.remember({"id": "workflow-stop", "title": "Stop process", "summary": "Feature drains first.",
                    "aliases": ["stop running job"]}, feature_receipt)
        self.assertEqual(m.query("stop running job", limit=1, compact=True)["hits"][0]["summary"], "Feature drains first.")
        self.git("switch", "main")
        main_result = m.query("stop running job", limit=1, compact=True)
        self.assertEqual(main_result["hits"][0]["summary"], main_rev)
        self.assertEqual(main_result["stale"], [])
        self.git("switch", "feature")
        self.assertEqual(m.query("stop running job", limit=1, compact=True)["hits"][0]["summary"], "Feature drains first.")
        self.assertEqual(m.db.execute("SELECT COUNT(*) FROM notes WHERE id LIKE 'workflow-stop@%'").fetchone()[0], 2)

    def test_legacy_branch_versions_survive_upgrade(self):
        self.git_init()
        self.git("add", ".")
        self.git("commit", "-m", "main")
        self.learn()
        self.git("switch", "-c", "feature")
        self.write(self.source, "class ProcessManager { void stop() { /* drain */ } }")
        self.git("add", self.source)
        self.git("commit", "-m", "feature")
        self.learn()
        self.make_legacy_notes()
        m = self.open()
        feature = m.query("shutdown")["hits"][0]["revision"]
        self.git("switch", "main")
        main = m.query("shutdown")["hits"][0]["revision"]
        self.assertNotEqual(main, feature)
        self.git("switch", "feature")
        self.assertEqual(m.query("shutdown")["hits"][0]["revision"], feature)
        self.assertEqual(m.db.execute("SELECT COUNT(*) FROM notes").fetchone()[0], 2)

    def test_many_branches_retain_their_same_file_revisions(self):
        self.git_init()
        self.git("add", ".")
        self.git("commit", "-m", "main")
        m = self.open()
        def save(label):
            receipt = m.capture([self.source], [], 24000)["receipt"]
            m.remember({"id": "workflow-stop", "title": "Stop process",
                        "summary": label, "aliases": ["stop running job"]}, receipt)
        save("main")
        self.git("switch", "-c", "shared-evidence")
        save("main")
        self.assertEqual(m.db.execute("SELECT COUNT(*) FROM notes WHERE id LIKE 'workflow-stop@%'").fetchone()[0], 1)
        for i in range(10):
            self.git("switch", "main")
            self.git("switch", "-c", f"feature-{i}")
            self.write(self.source, f"class Example {{ int branch = {i}; }}")
            self.git("add", self.source)
            self.git("commit", "-m", f"branch {i}")
            save(f"feature-{i}")
        self.git("switch", "main")
        self.assertEqual(m.query("stop running job", limit=1)["hits"][0]["summary"], "main")
        self.git("switch", "feature-0")
        self.assertEqual(m.query("stop running job", limit=1)["hits"][0]["summary"], "feature-0")
        self.git("switch", "shared-evidence")
        self.assertEqual(m.query("stop running job", limit=1)["hits"][0]["summary"], "main")
        self.assertEqual(m.db.execute("SELECT COUNT(*) FROM notes WHERE id LIKE 'workflow-stop@%'").fetchone()[0], 11)

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
