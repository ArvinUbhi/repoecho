import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT / ".github/skills/repoecho/scripts"
CLI = SCRIPTS / "repoecho_cli.py"
spec = importlib.util.spec_from_file_location("repoecho_setup", SCRIPTS / "setup_repoecho.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class FriendlyTests(unittest.TestCase):
    def test_doctor_reports_multiple_installations_without_creating_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            engine = root / ".github/skills/repoecho/scripts/repoecho.py"
            engine.parent.mkdir(parents=True)
            engine.write_text('VERSION = "0.0.1"\n')
            result = self.call(root, "--json", "doctor")
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertTrue(any(x["version"] == "0.0.1" for x in data["installations"]))
            self.assertTrue(any("Multiple" in x for x in data["warnings"]))
            self.assertFalse((root / ".repoecho").exists())

    def test_storage_and_prune_commands_do_not_scan_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            for command in ("storage", "prune"):
                result = self.call(temp, command)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("scan", json.loads(result.stdout))

    def call(self, cwd, *args, uv=False):
        prefix = [shutil.which("uv"), "run", "--offline", "--no-project", "--no-config", "--python", sys.executable, "--script"] if uv else [sys.executable]
        return subprocess.run([*prefix, str(CLI), *map(str, args)], cwd=cwd, capture_output=True, text=True)

    def test_root_discovery_modes_and_no_database(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-b", "main", temp], check=True, capture_output=True)
            sub = root / "src/main/java"
            sub.mkdir(parents=True)
            result = self.call(sub, "off")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("BYPASSED", result.stdout)
            self.assertIn(str(root.resolve()), result.stdout)
            self.assertFalse((sub / ".repoecho").exists())
            self.assertFalse((root / ".repoecho/cache.sqlite3").exists())
            self.call(sub, "cache", "off")
            result = self.call(sub, "--json", "on")
            self.assertFalse(json.loads(result.stdout)["controls"]["effective_enabled"])
            self.call(sub, "cache", "on")
            self.call(sub, "branch", "only")
            subprocess.run(["git", "symbolic-ref", "HEAD", "refs/heads/feature"], cwd=root, check=True)
            result = self.call(sub, "--json", "status")
            self.assertEqual(json.loads(result.stdout)["controls"]["bypass_reasons"], ["branch_off"])

    def test_explicit_subtree_and_plain_roots(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "one").mkdir()
            (root / "two").mkdir()
            self.call(root / "one", "off")
            result = self.call(root / "two", "--json", "status")
            self.assertTrue(json.loads(result.stdout)["controls"]["effective_enabled"])
            result = self.call(root, "--root", root / "one", "--json", "status")
            self.assertFalse(json.loads(result.stdout)["controls"]["effective_enabled"])

    def test_help_errors_doctor_and_passthrough(self):
        with tempfile.TemporaryDirectory() as temp:
            for args in [("--help",), ("cache", "--help"), ("benchmark", "--help"), ("setup", "--help")]:
                result = self.call(temp, *args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout)
            self.assertNotEqual(self.call(temp, "off", "garbage").returncode, 0)
            result = self.call(temp, "--json", "doctor")
            self.assertEqual(json.loads(result.stdout)["repository"], str(Path(temp).resolve()))
            self.assertFalse((Path(temp) / ".repoecho").exists())
            result = self.call(temp, "query", "argument with spaces; $(not executed)")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["hits"], [])

    @unittest.skipUnless(shutil.which("uv"), "uv integration requires uv")
    def test_uv_ignores_incompatible_project_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pyproject.toml").write_text('[project]\nname="incompatible"\nversion="0"\nrequires-python="<3"\ndependencies=["not-a-real-package-1234"]\n')
            (root / ".python-version").write_text("2.7")
            result = self.call(root, "status", uv=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / ".venv").exists())
            self.assertFalse((root / "uv.lock").exists())

    def test_alias_collision_idempotence_and_quoting(self):
        dest = Path("/path with spaces/user's skill")
        expansion = setup.alias_expansion(dest)
        with patch.object(setup.shutil, "which", return_value="available"), patch.object(setup.subprocess, "run") as run:
            run.return_value.stdout = "repoecho: !" + expansion + "\n"
            self.assertIsNone(setup.prepare_alias(dest))
            run.return_value.stdout = "repoecho: !echo other\n"
            with self.assertRaises(RuntimeError):
                setup.prepare_alias(dest)
            command, body = setup.prepare_alias(dest, replace=True)
            self.assertIn("--clobber", command)
            self.assertEqual(body, expansion)
            run.return_value.stdout = "other: issue list\n"
            command, _ = setup.prepare_alias(dest)
            self.assertNotIn("--clobber", command)

    def test_alias_failure_rolls_back_installed_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / ".copilot/skills/repoecho"
            dest.mkdir(parents=True)
            (dest / "SKILL.md").write_text("previous skill")
            with patch.object(setup, "prepare_alias", return_value=(["gh"], "body")), patch.object(setup, "register_alias", side_effect=subprocess.CalledProcessError(1, "gh")):
                with self.assertRaises(SystemExit):
                    setup.main(["--home", temp, "--replace", "--gh"])
            self.assertEqual((dest / "SKILL.md").read_text(), "previous skill")
            self.assertFalse((dest / "scripts").exists())

    def test_benchmark_ignores_exported_git_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            env = dict(os.environ, GIT_DIR=str(Path(temp) / "must-not-exist"),
                       GIT_WORK_TREE=temp, GIT_INDEX_FILE=str(Path(temp) / "must-not-exist-index"))
            result = subprocess.run([sys.executable, str(CLI), "benchmark", "--files", "4", "--notes", "2", "--runs", "1"],
                                    cwd=temp, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["branch_return"]["original_revision_reused"])
            self.assertEqual(list(Path(temp).iterdir()), [])

    @unittest.skipUnless(shutil.which("gh") and shutil.which("uv") and shutil.which("sh"), "requires real gh, uv, sh")
    def test_real_gh_alias_installed_copy_and_arguments(self):
        with tempfile.TemporaryDirectory(prefix="repoecho user's home ") as temp:
            root = Path(temp)
            home = root / "personal"
            repo = root / "repository with spaces"
            repo.mkdir()
            env = dict(os.environ, GH_CONFIG_DIR=str(root / "gh-config"), GH_PROMPT_DISABLED="1", UV_OFFLINE="1")
            # No token or authentication is needed for aliases/local commands.
            env.pop("GH_TOKEN", None)
            env.pop("GITHUB_TOKEN", None)
            def run(*args):
                return subprocess.run(list(map(str, args)), cwd=repo, env=env, capture_output=True, text=True)
            result = run(sys.executable, PROJECT / "tools/install.py", "--home", home, "--gh")
            self.assertEqual(result.returncode, 0, result.stderr)
            result = run("gh", "repoecho", "off")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("BYPASSED", result.stdout)
            result = run("gh", "repoecho", "--json", "status")
            self.assertFalse(json.loads(result.stdout)["controls"]["effective_enabled"])
            run("gh", "repoecho", "on")
            result = run("gh", "repoecho", "query", "spaces ' and ; $(literal)")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["hits"], [])
            result = run(sys.executable, PROJECT / "tools/install.py", "--home", home, "--gh", "--replace")
            self.assertEqual(result.returncode, 0, result.stderr)
            result = run("gh", "repoecho", "benchmark", "--files", "4", "--notes", "2", "--runs", "1")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["branch_return"]["original_revision_reused"])


if __name__ == "__main__":
    unittest.main()
