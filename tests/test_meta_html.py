import json
import tempfile
import unittest
from pathlib import Path

from helpers import BIN, run


class MetaTest(unittest.TestCase):
    def test_ytdlp_fields_and_sidecar_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            info, side, out = Path(tmp, "i.json"), Path(tmp, "s.json"), Path(tmp, "o.json")
            info.write_text(json.dumps({
                "title": "Episode", "uploader": "Channel", "upload_date": "20240131",
                "webpage_url": "https://example.com/v", "duration": 61,
                "chapters": [{"start_time": 5.7, "title": "Intro"}], "description": ""}))
            side.write_text(json.dumps({"title": "My title", "speaker": "Ana"}))
            r = run("python3", BIN / "lib/meta.py", out, "--ytdlp", info, "--sidecar", side,
                    "source_type=video", "empty=")
            self.assertEqual(r.returncode, 0, r.stderr)
            meta = json.loads(out.read_text())
        self.assertEqual(meta["published"], "2024-01-31")
        self.assertEqual(meta["channel"], "Channel")
        self.assertEqual(meta["chapters"], [{"start": 5, "title": "Intro"}])
        self.assertEqual(meta["title"], "My title")      # sidecar wins
        self.assertEqual(meta["speaker"], "Ana")
        self.assertNotIn("description", meta)            # empty values dropped
        self.assertNotIn("empty", meta)


class Html2TextTest(unittest.TestCase):
    def convert(self, html_bytes, content_type=""):
        with tempfile.TemporaryDirectory() as tmp:
            src, out = Path(tmp, "p.html"), Path(tmp, "o.txt")
            src.write_bytes(html_bytes)
            r = run("python3", BIN / "lib/html2text.py", "https://x.test/a", src, out, content_type)
            self.assertEqual(r.returncode, 0, r.stderr)
            return r.stdout.strip(), out.read_text(encoding="utf-8")

    def test_prefers_article_and_drops_navigation(self):
        body = "Real content sentence. " * 40
        html = (f"<html><head><title>T</title></head><body><nav>Menu Home</nav>"
                f"<article><h1>Headline</h1><p>{body}</p></article>"
                f"<footer>Copyright</footer><script>var x=1</script></body></html>")
        title, text = self.convert(html.encode())
        self.assertEqual(title, "T")
        self.assertIn("# Headline", text)
        self.assertIn("Real content sentence.", text)
        for junk in ("Menu Home", "Copyright", "var x"):
            self.assertNotIn(junk, text)

    def test_decodes_declared_charset(self):
        html = "<html><body><p>Știință și decizii</p></body></html>".encode("iso-8859-16")
        _, text = self.convert(html, "text/html; charset=iso-8859-16")
        self.assertIn("Știință și decizii", text)


if __name__ == "__main__":
    unittest.main()
