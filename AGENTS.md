# Wisdom library

Tooling for a personal knowledge library: ingest a source, distill it into an
OKF note, apply notes to real situations. This repo is public. The user's notes
are private and live in `library/`, a separate git repo that is gitignored here.
**Never copy note content into this repo, and never commit `library/` or `inbox/` here.**

Workflow:

1. `bin/transcribe <video-url | local-media-file>` turns any yt-dlp URL or local
   audio/video into a timestamped transcript in `inbox/`. Two providers:
   - Mistral Voxtral (cloud, speaker labels), the default when `MISTRAL_API_KEY` is set;
   - local whisper.cpp (`--local`: free, private, no speaker labels).
   `bin/extract <pdf | article-url | text-file>` handles text sources locally: PDF
   via pdftotext plus Tesseract OCR, articles via HTML strip, text copied as-is.
   Both write `inbox/<base>.meta.json` and reuse saved output unless given `--force`.
2. `/wisdom-ingest <url-or-file>` routes to transcribe or extract, distills into
   an OKF note in `library/notes/` tagged with 1-2 usage areas, then **updates the
   methods automatically, without asking**:
   - it creates an area's first method at 3 notes;
   - after that it makes minimal edits only when the note adds, refines, or contradicts a step;
   - either way, it records the note in the method's `notes:` list.
3. `/wisdom-apply ...` applies the library to a personal situation, citing notes and methods.
4. `/wisdom-build <area>` is **on demand only**: a clean full rebuild of
   `library/methods/<area>.md` from all the area's notes, or building one early.
5. `bin/check` validates `library/`: frontmatter, naming, index, methods. It prints
   each area's note count and method state. It warns, without failing, when a method
   is missing or hasn't taken a note into account.

Layout:

- `bin/`: shell entry points; `bin/_common.sh` holds the shared helpers (bash 3.2 compatible);
  `bin/lib/*.py` are stdlib-only Python helpers
- `.agents/skills/`: the `wisdom-ingest`, `wisdom-apply`, `wisdom-build` skills (Agent Skills
  format; the only copy, read natively by Vibe, Codex and others). Edit skills here.
- `.claude/skills/`: one symlink per skill into `.agents/skills/`, for Claude Code. Add a
  link when adding a skill; `bin/check` warns if one is missing.
- `tests/`: stdlib `unittest` suite (`python3 -m unittest discover -s tests`), with fixture
  notes and no network access. Run it, and `shellcheck -x` on the shell scripts, before
  committing. `.github/workflows/ci.yml` runs both on every push (GitHub Actions).
- `inbox/`: raw transcripts and audio, local only (gitignored)
- `library/` (private, gitignored, created by `bin/init-library`):
  - `notes/`: OKF v0.2 bundle (spec: github.com/openknowledge-sh/openknowledge), one
    Markdown note per source, named `topic--name.md`; `index.md` is the reserved listing
  - `methods/`: one merged method per usage area (decisions, idea-testing, brainstorming,
    discussions), named `<area>.md`, with frontmatter `area`, `built`, `updated`, `notes`
  - `journal/`: decision records
