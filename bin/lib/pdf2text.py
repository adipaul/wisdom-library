#!/usr/bin/env python3
"""Extract text from a PDF locally — no cloud API.

Pages with a real text layer are read with `pdftotext` (exact, instant).
Pages with almost no text that contain an image (scans, photos) are rendered with
`pdftoppm` and OCR'd with `tesseract`. Pages with almost no text and no image
(blank pages, section dividers) are kept as they are; OCR would find nothing.

Usage: pdf2text.py IN.pdf OUT.md [OCR_LANGS]     (OCR_LANGS like "eng+ron")
Prints a JSON summary (title, author, pages, ocr_pages) on stdout for meta.json.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

MIN_CHARS = 40  # fewer non-space characters than this → a candidate for OCR (if it has an image)


def run(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def pdfinfo(path):
    info = {}
    for line in run("pdfinfo", path).splitlines():
        key, _, value = line.partition(":")
        info[key.strip()] = value.strip()
    return info


def ocr_languages(requested):
    """Keep only languages tesseract actually has; fall back to eng."""
    out = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True)
    installed = set((out.stdout + out.stderr).split())
    usable = [lang for lang in requested.split("+") if lang in installed]
    missing = [lang for lang in requested.split("+") if lang not in installed]
    if missing:
        print(f"note: tesseract language(s) not installed: {', '.join(missing)} "
              "(macOS: brew install tesseract-lang)", file=sys.stderr)
    return "+".join(usable) or "eng"


def has_image(pdf, page):
    """True if the page contains at least one image (pdfimages lists 2 header lines first)."""
    out = run("pdfimages", "-list", "-f", str(page), "-l", str(page), pdf)
    return len(out.strip().splitlines()) > 2


def ocr_page(pdf, page, langs, tmp):
    prefix = os.path.join(tmp, f"p{page}")
    run("pdftoppm", "-r", "300", "-f", str(page), "-l", str(page), "-png", "-singlefile", pdf, prefix)
    return run("tesseract", prefix + ".png", "stdout", "-l", langs)


def main(argv):
    if len(argv) not in (2, 3):
        sys.exit(__doc__)
    pdf, out_path = argv[0], argv[1]
    requested = argv[2] if len(argv) == 3 else "eng"

    info = pdfinfo(pdf)
    pages = int(info.get("Pages", "0") or 0)
    texts = run("pdftotext", "-enc", "UTF-8", pdf, "-").split("\f")

    ocr_pages, langs = [], None
    parts = []
    with tempfile.TemporaryDirectory() as tmp:
        for page in range(1, pages + 1):
            text = texts[page - 1] if page - 1 < len(texts) else ""
            if len("".join(text.split())) < MIN_CHARS:
                if not has_image(pdf, page):
                    print(f"==> page {page}/{pages}: almost no text and no image — skipping OCR",
                          file=sys.stderr)
                    parts.append(f"<!-- page {page} -->\n{text.strip()}")
                    continue
                if langs is None:
                    if not shutil.which("tesseract"):
                        sys.exit("error: page has no text layer and 'tesseract' is not installed "
                                 "(macOS: brew install tesseract tesseract-lang)")
                    langs = ocr_languages(requested)
                print(f"==> OCR page {page}/{pages} ({langs})", file=sys.stderr)
                text = ocr_page(pdf, page, langs, tmp)
                ocr_pages.append(page)
            parts.append(f"<!-- page {page} -->\n{text.strip()}")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(parts).strip() + "\n")

    summary = {"title": info.get("Title") or None, "author": info.get("Author") or None,
               "pages": pages, "ocr_pages": ocr_pages or None}
    print(json.dumps({k: v for k, v in summary.items() if v}))


if __name__ == "__main__":
    main(sys.argv[1:])
