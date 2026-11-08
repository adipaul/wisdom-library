import json
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401  (puts bin/lib on sys.path)
import transcript


def write(path, data):
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class MergeTest(unittest.TestCase):
    def test_offsets_shift_later_chunks_and_record_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b, out = f"{tmp}/a.json", f"{tmp}/b.json", f"{tmp}/out.json"
            write(a, {"model": "voxtral", "text": "one", "segments": [{"start": 1, "end": 2, "text": "one"}]})
            write(b, {"text": "two", "segments": [{"start": 0.5, "end": 3, "text": "two"}]})
            transcript.merge(out, "mistral", [f"{a}:0", f"{b}:1800.25"])
            merged = json.load(open(out))
        self.assertEqual(merged["provider"], "mistral")
        self.assertEqual(merged["model"], "voxtral")
        second = merged["segments"][1]
        self.assertAlmostEqual(second["start"], 1800.75)
        self.assertAlmostEqual(second["end"], 1803.25)
        self.assertEqual(second["chunk"], 2)
        self.assertEqual(merged["text"], "one\n\ntwo")


class RenderTest(unittest.TestCase):
    def render(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            src, txt, srt = f"{tmp}/in.json", f"{tmp}/out.txt", f"{tmp}/out.srt"
            write(src, data)
            transcript.render(src, txt, srt)
            return Path(txt).read_text(), Path(srt).read_text()

    def test_speaker_ids_become_readable_and_turns_merge(self):
        txt, srt = self.render({"segments": [
            {"start": 0, "end": 2, "text": "Hello", "speaker_id": "speaker_1"},
            {"start": 2, "end": 4, "text": "again.", "speaker_id": "speaker_1"},
            {"start": 75, "end": 80, "text": "Hi.", "speaker_name": "Speaker 2"},
        ]})
        self.assertEqual(txt.splitlines(), ["[00:00] Speaker 1: Hello again.", "[01:15] Speaker 2: Hi."])
        self.assertIn("00:01:15,000 --> 00:01:20,000\nSpeaker 2: Hi.", srt)

    def test_without_speakers_paragraphs_break_on_pause_and_minute(self):
        segs = [{"start": t, "end": t + 4, "text": f"s{t}"} for t in (0, 4, 8)]   # continuous
        segs.append({"start": 20, "end": 24, "text": "after-pause"})              # 8 s pause
        segs += [{"start": t, "end": t + 4, "text": f"s{t}"} for t in range(24, 92, 4)]
        lines = self.render({"segments": segs})[0].splitlines()
        self.assertTrue(lines[0].startswith("[00:00] s0 s4 s8"))
        self.assertTrue(lines[1].startswith("[00:20] after-pause"))
        self.assertTrue(lines[2].startswith("[01:20] "), lines)  # 60 s after 00:20

    def test_chunk_boundary_is_marked(self):
        txt, _ = self.render({"chunks": [{"index": 1}, {"index": 2}], "segments": [
            {"start": 0, "end": 1, "text": "a", "speaker_id": "speaker_1", "chunk": 1},
            {"start": 3300, "end": 3301, "text": "b", "speaker_id": "speaker_1", "chunk": 2},
        ]})
        self.assertIn("--- chunk 2 starts at 55:00", txt)
        self.assertIn("[55:00] Speaker 1: b", txt)

    def test_no_segments_falls_back_to_text(self):
        txt, srt = self.render({"text": "Just text."})
        self.assertEqual(txt, "Just text.\n")
        self.assertIn("Just text.", srt)


class WhisperAndProviderTest(unittest.TestCase):
    def test_from_whisper_converts_millisecond_offsets(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out = f"{tmp}/w.json", f"{tmp}/out.json"
            write(src, {"result": {"language": "ro"}, "transcription": [
                {"offsets": {"from": 0, "to": 2500}, "text": " Bună ziua."},
                {"offsets": {"from": 2500, "to": 3000}, "text": "  "},
            ]})
            transcript.from_whisper(src, out, "large-v3-turbo")
            data = json.load(open(out, encoding="utf-8"))
        self.assertEqual(data["provider"], "local")
        self.assertEqual(data["language"], "ro")
        self.assertEqual(data["segments"], [{"start": 0.0, "end": 2.5, "text": "Bună ziua."}])

    def test_provider_of_legacy_transcripts(self):
        self.assertEqual(transcript.provider_of({"provider": "local"}), "local")
        self.assertEqual(transcript.provider_of({"model": "voxtral-small-transcribe-3"}), "mistral")
        self.assertEqual(transcript.provider_of({}), "unknown")


if __name__ == "__main__":
    unittest.main()
