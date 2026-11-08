#!/usr/bin/env python3
"""Strip a saved HTML page to readable text (stdlib only).

Prefers the page's <article>, then <main>, then the whole <body>; drops scripts,
navigation, headers, footers, and forms. Honors the page charset.

Usage: html2text.py URL IN.html OUT.txt [CONTENT_TYPE_HEADER]
Prints the page title on stdout.
"""
import html
import re
import sys
from html.parser import HTMLParser

SKIP = {"script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg", "template"}
BLOCK = {"p", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "div", "section", "article",
         "blockquote", "pre", "tr", "figcaption"}
MIN_CONTENT = 500  # chars; shorter <article>/<main> is probably a teaser, use the body instead


class Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.depth = {"article": 0, "main": 0}
        self.buf = {"article": [], "main": [], "body": []}

    def _emit(self, s):
        if self.skip:
            return
        self.buf["body"].append(s)
        for zone in ("article", "main"):
            if self.depth[zone]:
                self.buf[zone].append(s)

    def handle_starttag(self, tag, attrs):
        if tag in self.depth:
            self.depth[tag] += 1
        if tag in SKIP:
            self.skip += 1
        if tag in BLOCK:
            self._emit("\n")
        if tag in ("h1", "h2", "h3"):
            self._emit("#" * int(tag[1]) + " ")
        elif tag == "li":
            self._emit("- ")

    def handle_endtag(self, tag):
        if tag in BLOCK:
            self._emit("\n")
        if tag in SKIP and self.skip:
            self.skip -= 1
        if tag in self.depth and self.depth[tag]:
            self.depth[tag] -= 1

    def handle_data(self, data):
        self._emit(data)


def decode(raw, content_type):
    m = re.search(r"charset=([\w-]+)", content_type or "", re.I) \
        or re.search(rb"<meta[^>]+charset=[\"']?([\w-]+)", raw[:4096], re.I)
    charset = m.group(1) if m else "utf-8"
    if isinstance(charset, bytes):
        charset = charset.decode("ascii", "replace")
    try:
        return raw.decode(charset, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def clean(parts):
    text = "".join(parts)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"^(#+ |- )\n", "", text, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def main(argv):
    if len(argv) not in (3, 4):
        sys.exit(__doc__)
    url, in_path, out_path = argv[:3]
    page = decode(open(in_path, "rb").read(), argv[3] if len(argv) == 4 else "")

    m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', page, re.I) \
        or re.search(r"<title[^>]*>(.*?)</title>", page, re.I | re.S)
    title = html.unescape(m.group(1)).strip() if m else ""

    p = Extractor()
    p.feed(page)
    text = ""
    for zone in ("article", "main", "body"):
        text = clean(p.buf[zone])
        if len(text) >= MIN_CONTENT:
            break

    header = f"Source: {url}\n" + (f"Title: {title}\n" if title else "") + "\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header + text + "\n")
    print(title)


if __name__ == "__main__":
    main(sys.argv[1:])
