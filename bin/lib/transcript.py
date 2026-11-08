#!/usr/bin/env python3
"""Normalize transcription output and render .txt / .srt.

Usage:
  transcript.py merge OUT.json PROVIDER CHUNK1.json:OFFSET_SECONDS [CHUNK2.json:OFFSET ...]
  transcript.py from-whisper WHISPER.json OUT.json MODEL
  transcript.py render IN.json OUT.txt OUT.srt [DURATION_SECONDS]
  transcript.py provider IN.json

Normalized JSON: {provider, model, language, text, segments: [{start, end, text, speaker?, chunk?}]}.
`render` works offline on any saved transcript, so old ones can be re-rendered.
The .txt is what /wisdom-ingest reads, one timestamped line per speaker turn:
  [12:34] Speaker 1: ...
or, without speaker labels (local Whisper), one timestamped paragraph per ~minute.
"""
import json
import re
import sys


def speaker_of(seg):
    for key in ("speaker_name", "speaker_id", "speaker"):
        value = seg.get(key)
        if value not in (None, ""):
            value = str(value).strip()
            # diarize=true returns ids like "speaker_1" → "Speaker 1"
            m = re.fullmatch(r"speaker[_ ]?(\d+)", value, re.I)
            return f"Speaker {m.group(1)}" if m else value
    return ""


def clock(sec, srt=False):
    sec = max(0.0, float(sec))
    h, m, s = int(sec // 3600), int(sec % 3600 // 60), sec % 60
    if srt:
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
    return f"{h}:{m:02d}:{int(s):02d}" if h else f"{m:02d}:{int(s):02d}"


PARAGRAPH_SECONDS = 60  # without speaker labels: start a new paragraph after this long…
PARAGRAPH_PAUSE = 2.0    # …or at a pause longer than this


def provider_of(data):
    if data.get("provider"):
        return data["provider"]
    # transcripts made before providers were recorded all came from Mistral
    return "mistral" if str(data.get("model", "")).startswith("voxtral") else "unknown"


def from_whisper(in_path, out_path, model):
    data = json.load(open(in_path, encoding="utf-8"))
    segments = []
    for item in data.get("transcription") or []:
        text = (item.get("text") or "").strip()
        if not text:
            continue
        offsets = item.get("offsets") or {}
        segments.append({"start": offsets.get("from", 0) / 1000.0,
                         "end": offsets.get("to", 0) / 1000.0, "text": text})
    out = {"provider": "local", "model": f"whisper.cpp {model}",
           "language": (data.get("result") or {}).get("language"),
           "text": " ".join(s["text"] for s in segments), "segments": segments}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


def merge(out_path, provider, parts):
    merged = {"provider": provider, "text": "", "segments": [], "chunks": []}
    texts = []
    for index, part in enumerate(parts, 1):
        path, _, offset = part.rpartition(":")
        offset = float(offset)
        data = json.load(open(path, encoding="utf-8"))
        for key in ("model", "language"):
            if data.get(key) and not merged.get(key):
                merged[key] = data[key]
        for seg in data.get("segments") or []:
            seg = dict(seg)
            seg["start"] = float(seg.get("start", 0)) + offset
            seg["end"] = float(seg.get("end", seg["start"] - offset)) + offset
            seg["chunk"] = index
            merged["segments"].append(seg)
        texts.append((data.get("text") or "").strip())
        merged["chunks"].append({"index": index, "offset": offset})
    merged["text"] = "\n\n".join(t for t in texts if t)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=1)


def render(in_path, txt_path, srt_path, duration=None):
    data = json.load(open(in_path, encoding="utf-8"))
    segments = data.get("segments") or []
    text = (data.get("text") or " ".join(s.get("text", "") for s in segments)).strip()
    multi_chunk = len(data.get("chunks") or []) > 1
    has_speakers = any(speaker_of(s) for s in segments)

    # .txt — speaker turns (or ~1-minute paragraphs) with timestamps;
    # falls back to plain text when there are no segments at all
    lines = []
    turn = None  # (chunk, speaker, start, [texts])
    last_end = 0.0
    for seg in segments:
        chunk, speaker = seg.get("chunk", 1), speaker_of(seg)
        piece = (seg.get("text") or "").strip()
        if not piece:
            continue
        start = float(seg.get("start", 0))
        if has_speakers:
            same = turn and (turn[0], turn[1]) == (chunk, speaker)
        else:
            same = (turn and turn[0] == chunk and start - turn[2] < PARAGRAPH_SECONDS
                    and start - last_end <= PARAGRAPH_PAUSE)
        last_end = float(seg.get("end", start))
        if same:
            turn[3].append(piece)
            continue
        if turn:
            lines.append(format_turn(turn))
        if multi_chunk and (turn is None or turn[0] != chunk) and chunk != 1:
            lines.append(f"\n--- chunk {chunk} starts at {clock(seg.get('start', 0))}; "
                         "speaker numbers restart here and may not match earlier chunks ---\n")
        turn = (chunk, speaker, float(seg.get("start", 0)), [piece])
    if turn:
        lines.append(format_turn(turn))
    body = "\n".join(lines) if lines else text
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(body.strip() + "\n")

    # .srt — one cue per segment, speaker-labelled
    if segments:
        cues = []
        for i, seg in enumerate(segments, 1):
            start = float(seg.get("start", 0))
            end = float(seg.get("end", start + 3))
            speaker = speaker_of(seg)
            label = f"{speaker}: " if speaker else ""
            cues.append(f"{i}\n{clock(start, True)} --> {clock(end, True)}\n"
                        f"{label}{(seg.get('text') or '').strip()}\n")
    else:
        end = float(duration) if duration else 0.0
        cues = [f"1\n{clock(0, True)} --> {clock(end, True)}\n{text}\n"]
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(cues))


def format_turn(turn):
    _, speaker, start, pieces = turn
    label = f"{speaker}: " if speaker else ""
    return f"[{clock(start)}] {label}{' '.join(pieces)}"


def main(argv):
    if len(argv) >= 4 and argv[0] == "merge":
        merge(argv[1], argv[2], argv[3:])
    elif len(argv) == 4 and argv[0] == "from-whisper":
        from_whisper(*argv[1:])
    elif len(argv) in (4, 5) and argv[0] == "render":
        render(*argv[1:])
    elif len(argv) == 2 and argv[0] == "provider":
        print(provider_of(json.load(open(argv[1], encoding="utf-8"))))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
