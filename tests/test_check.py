import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import BIN, make_library, run


class CheckLibraryTest(unittest.TestCase):
    def check(self, lib):
        return run(BIN / "check", lib)

    def test_valid_library_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib = make_library(Path(tmp), {"decisions--duke.md": "decisions, discussions"})
            r = self.check(lib)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("OK: 1 note(s)", r.stdout)
        self.assertNotIn("Warnings", r.stdout)

    def test_quoted_value_with_colon_is_fine(self):
        # the fixture's sources title is "Author: Example book" — must not break parsing
        with tempfile.TemporaryDirectory() as tmp:
            r = self.check(make_library(Path(tmp), {"decisions--duke.md": "decisions"}))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_errors_fail_the_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib = make_library(Path(tmp), {"Bad_Name.md": "decisions, cooking"})
            (lib / "notes" / "ideas--other.md").write_text("no frontmatter\n")
            r = self.check(lib)
        self.assertEqual(r.returncode, 1)
        for msg in ("name must be <topic>--<name>.md", "unknown usage area 'cooking'",
                    "missing --- frontmatter block", "not listed in notes/index.md"):
            self.assertIn(msg, r.stdout)

    def test_method_and_tagging_warnings_do_not_fail(self):
        notes = {f"decisions--n{i}.md": "decisions" for i in range(3)}
        notes["ideas--wide.md"] = "decisions, discussions, brainstorming"
        with tempfile.TemporaryDirectory() as tmp:
            lib = make_library(Path(tmp), notes, methods={
                "decisions.md": "area: decisions\nupdated: 2026-11-01\nnotes: [decisions--n0.md]"})
            r = self.check(lib)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("hasn't taken 3 note(s) into account", r.stdout)
        self.assertIn("tagged with 3 usage areas", r.stdout)

    def test_area_without_method_warns_at_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib = make_library(Path(tmp), {f"decisions--n{i}.md": "decisions" for i in range(3)})
            r = self.check(lib)
        self.assertIn("decisions: 3 notes but no method yet", r.stdout)

    def test_method_listing_missing_note_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib = make_library(Path(tmp), {"decisions--a.md": "decisions"}, methods={
                "decisions.md": "area: decisions\nnotes: [decisions--a.md, decisions--gone.md]"})
            r = self.check(lib)
        self.assertEqual(r.returncode, 1)
        self.assertIn("lists note 'decisions--gone.md', which does not exist", r.stdout)

    def test_help(self):
        r = run(BIN / "check", "--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage: bin/check", r.stdout)


class CheckSkillsTest(unittest.TestCase):
    """bin/check lints the skills of the repo it lives in, so run a copy in a temp repo."""

    def check_skill(self, frontmatter, link=True):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            shutil.copytree(BIN, repo / "bin")
            skill = repo / ".agents" / "skills" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(f"---\n{frontmatter}\n---\nBody\n")
            if link:
                (repo / ".claude" / "skills").mkdir(parents=True)
                (repo / ".claude" / "skills" / "demo").symlink_to("../../.agents/skills/demo")
            make_library(repo / "library", {})
            return run(repo / "bin" / "check")

    def test_valid_skill_with_folded_description(self):
        r = self.check_skill("name: demo\ndescription: >-\n  Use article: prefix\n  to force.")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("1 skill(s)", r.stdout)

    def test_unquoted_colon_in_description_is_an_error(self):
        r = self.check_skill("name: demo\ndescription: Web article (article: prefix)")
        self.assertEqual(r.returncode, 1)
        self.assertIn("unquoted ': '", r.stdout)

    def test_name_must_match_folder(self):
        r = self.check_skill("name: other\ndescription: Fine.")
        self.assertIn("must match its folder 'demo'", r.stdout)

    def test_missing_claude_link_warns(self):
        r = self.check_skill("name: demo\ndescription: Fine.", link=False)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("Claude Code won't see this skill", r.stdout)


if __name__ == "__main__":
    unittest.main()
