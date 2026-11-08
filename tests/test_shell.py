"""Shell scripts: name sanitizing, argument handling, help output (no network, no API)."""
import unittest

from helpers import BIN, run


def sanitize(name):
    r = run("bash", "-c", 'source "$1"; sanitize "$2"', "_", BIN / "_common.sh", name)
    assert r.returncode == 0, r.stderr
    return r.stdout


class SanitizeTest(unittest.TestCase):
    def test_short_names_are_cleaned_but_kept(self):
        self.assertEqual(sanitize("grandma story (2026).m4a"), "grandma_story_2026_.m4a")

    def test_long_names_stay_unique_and_short(self):
        base = "Cum Luăm Decizii Mai Bune Când Totul E Incert ｜ Interviu Lung Cu Un Invitat ｜ Podcast [ID] - Part "
        one, two = sanitize(base + "1"), sanitize(base + "2")
        self.assertNotEqual(one, two)                 # the old cut-at-80 made these identical
        self.assertLessEqual(max(len(one), len(two)), 80)
        self.assertIn("Part_1", one)                  # the distinguishing end is kept

    def test_same_input_same_name(self):
        self.assertEqual(sanitize("x" * 200), sanitize("x" * 200))


class ArgumentsTest(unittest.TestCase):
    def test_second_input_is_rejected(self):
        for script in ("transcribe", "extract"):
            r = run(BIN / script, "a.m4a", "—", "speaker:", "x")
            self.assertEqual(r.returncode, 1, script)
            self.assertIn("only one input allowed", r.stderr)

    def test_unknown_option_is_rejected(self):
        r = run(BIN / "extract", "--bogus", "a.pdf")
        self.assertEqual(r.returncode, 1)
        self.assertIn("unknown option: --bogus", r.stderr)

    def test_help_prints_the_whole_header(self):
        for script, last_line in (("transcribe", "WHISPER_MODEL_PATH"), ("extract", "OCR_LANG")):
            r = run(BIN / script, "--help")
            self.assertEqual(r.returncode, 0, script)
            self.assertTrue(r.stdout.startswith(script + " —"), r.stdout[:40])
            self.assertIn(last_line, r.stdout)
            self.assertNotIn("_common.sh", r.stdout)    # stops before the code starts


if __name__ == "__main__":
    unittest.main()
