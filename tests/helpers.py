"""Shared test helpers. Tests use only the standard library.

Run all tests:  python3 -m unittest discover -s tests -v
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BIN = REPO / "bin"
sys.path.insert(0, str(BIN / "lib"))


def load_script(name):
    """Import an extension-less script from bin/ (e.g. bin/check) as a module."""
    from importlib.machinery import SourceFileLoader
    loader = SourceFileLoader(name, str(BIN / name))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def run(*cmd, **kw):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)


NOTE = """---
type: Book Note
title: Example
description: One sentence.
resource: local:example.pdf
status: stable
tags: [decision-making, bias]
sources:
  - id: source
    resource: local:example.pdf
    title: "Author: Example book"
    author: Example Author
generated: {{ by: agent:test, at: 2026-11-08T12:00:00Z }}
date_added: 2026-11-08
usage_areas: [{areas}]
---
## Core idea
Text.
"""


def make_library(root, notes, methods=None):
    """notes: {filename: usage areas string}; methods: {filename: frontmatter body}."""
    (root / "notes").mkdir(parents=True)
    (root / "methods").mkdir()
    index = ["# Notes index", ""]
    for name, areas in notes.items():
        (root / "notes" / name).write_text(NOTE.format(areas=areas), encoding="utf-8")
        index.append(f"- [{name}]({name}) — Example.")
    (root / "notes" / "index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    for name, body in (methods or {}).items():
        (root / "methods" / name).write_text(f"---\n{body}\n---\n## Steps\n", encoding="utf-8")
    return root
