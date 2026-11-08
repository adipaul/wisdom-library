#!/usr/bin/env python3
"""Write inbox/<base>.meta.json — source metadata that /wisdom-ingest reads.

Usage:
  meta.py OUT.json [--ytdlp INFO.json] [--sidecar SIDECAR.json] [key=value ...]

Priority (later wins): yt-dlp info < key=value defaults < sidecar written by the user.
"""
import argparse
import json
import sys


def from_ytdlp(path):
    info = json.load(open(path, encoding="utf-8"))
    date = info.get("upload_date") or ""
    if len(date) == 8:
        date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
    meta = {
        "source_type": "video",
        "title": info.get("title"),
        "channel": info.get("channel") or info.get("uploader"),
        "published": date or None,
        "resource": info.get("webpage_url") or info.get("original_url"),
        "duration_seconds": info.get("duration"),
        "language": info.get("language"),
        "description": (info.get("description") or "")[:1500] or None,
        "chapters": [
            {"start": int(c.get("start_time", 0)), "title": c.get("title")}
            for c in (info.get("chapters") or [])
        ] or None,
    }
    return {k: v for k, v in meta.items() if v not in (None, "", [])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--ytdlp")
    ap.add_argument("--sidecar")
    ap.add_argument("pairs", nargs="*", help="key=value defaults")
    a = ap.parse_args()

    meta = {}
    if a.ytdlp:
        meta.update(from_ytdlp(a.ytdlp))
    for pair in a.pairs:
        key, _, value = pair.partition("=")
        if value:
            meta[key] = value
    if a.sidecar:
        meta.update(json.load(open(a.sidecar, encoding="utf-8")))

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    sys.exit(main())
