import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]


class InstallTests(unittest.TestCase):
    def install(self, *args):
        return subprocess.run([sys.executable, str(PROJECT / "tools/install.py"), *map(str, args)],
                              capture_output=True, text=True)

    def test_personal_install_and_replace_guard(self):
        with tempfile.TemporaryDirectory() as home:
            result = self.install("--home", home)
            self.assertEqual(result.returncode, 0, result.stderr)
            target = Path(home) / ".copilot/skills/repoecho"
            self.assertTrue((target / "SKILL.md").exists())
            self.assertTrue((target / "references/java.md").exists())
            helper = target / "scripts/repoecho.py"
            result = subprocess.run([sys.executable, str(helper), "--root", home, "scan"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("files", json.loads(result.stdout))
            self.assertNotEqual(self.install("--home", home).returncode, 0)
            self.assertEqual(self.install("--home", home, "--replace").returncode, 0)

    def test_project_install(self):
        with tempfile.TemporaryDirectory() as root:
            result = self.install("--project", root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(root) / ".github/skills/repoecho/scripts/repoecho.py").is_file())


if __name__ == "__main__":
    unittest.main()
