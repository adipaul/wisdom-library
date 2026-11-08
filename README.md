# Wisdom library

Turn podcasts, videos, recordings, books, and articles into short, structured,
reusable notes, then apply them to your own decisions, ideas, and discussions.

- **Ingest** a source: video URLs (YouTube or anything [yt-dlp](https://github.com/yt-dlp/yt-dlp)
  supports), local audio/video, PDFs, web articles, or plain text.
- **Distill** it with the AI coding agent of your choice (Mistral Vibe, Claude Code,
  OpenAI Codex, and others) into an [OKF v0.2](https://github.com/openknowledge-sh/openknowledge)
  note: core idea, frameworks, traps, rules of thumb, questions to ask yourself.
- **Apply** the library to a real situation, with every idea cited to its note.
- **Methods build themselves**: notes in the same usage area merge into one
  step-by-step method, which is created and kept up to date automatically as you add notes.

This repo holds only the tooling. Your notes live in `library/`, a separate git
repository that you keep private. It is gitignored here.

## Requirements

- macOS or Linux with `bash`, `python3`, `curl`, `git`
- `yt-dlp` and `ffmpeg` for audio/video
- `poppler` (pdftotext) for PDFs, plus `tesseract` and `tesseract-lang` for scanned PDFs
- For audio transcription, either a [Mistral API key](https://console.mistral.ai/) (cloud)
  or [whisper.cpp](https://github.com/ggml-org/whisper.cpp) (local). See
  [Transcription providers](#transcription-providers). PDFs, articles, and text
  are always processed locally.
- An AI coding agent that supports [Agent Skills](https://agentskills.io). See
  [Supported agents](#supported-agents).

```bash
brew install yt-dlp ffmpeg poppler tesseract tesseract-lang
brew install whisper.cpp              # optional: local transcription
```

## Setup

```bash
git clone https://github.com/adipaul/wisdom-library.git
cd wisdom-library
bin/init-library                      # new, empty library (then add a PRIVATE remote)
# or: bin/init-library <your-private-notes-repo-url>
echo 'MISTRAL_API_KEY=...' > .env     # cloud transcription (or export it, or ~/.vibe/.env)
```

`bin/init-library` also installs a pre-commit hook in `library/` that runs `bin/check`.
`library/` can also be a symlink to a notes repo kept elsewhere. If you move this
folder, re-run `bin/init-library` so the hook points at the new location.

For local transcription, download a Whisper model once (~1.6 GB):

```bash
mkdir -p ~/.cache/whisper.cpp && curl -fL -o ~/.cache/whisper.cpp/ggml-large-v3-turbo.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
```

## Supported agents

The skills use the open [Agent Skills](https://agentskills.io) format and live in
one vendor-neutral folder, `.agents/skills/`. Project instructions are in
`AGENTS.md`, which these agents all read.

| Agent | How it finds the skills | Invoke |
|---|---|---|
| [Mistral Vibe](https://github.com/mistralai/mistral-vibe) | reads `.agents/skills/` | `/wisdom-ingest …` |
| [OpenAI Codex](https://github.com/openai/codex) | reads `.agents/skills/` | `$wisdom-ingest …` |
| [Claude Code](https://code.claude.com) | `.claude/skills/` holds one symlink per skill into `.agents/skills/` | `/wisdom-ingest …` |

Gemini CLI, GitHub Copilot, Cursor, OpenCode, Goose, and Amp also read
`.agents/skills/`. A few of them read `.claude/skills/` too and may list each
skill twice; it's the same skill either way.

There is only one copy of each skill: edit it in `.agents/skills/`. On Windows,
the Claude Code symlinks need `git config core.symlinks true` (and Developer
Mode) before cloning.

## Usage

Open the folder in your agent and trust it once. Then (Codex: `$` instead of `/`):

```bash
/wisdom-ingest "https://www.youtube.com/watch?v=..."          # video / podcast
/wisdom-ingest ~/recordings/interview.m4a                      # local audio or video
/wisdom-ingest ~/rec/grandma.m4a — speaker: my grandmother, childhood story
/wisdom-ingest ~/books/meditations.pdf — author: Marcus Aurelius
/wisdom-ingest article:https://example.com/great-essay         # web article
/wisdom-ingest ~/notes/ideas.md                                 # plain text / markdown
/wisdom-ingest @inbox/<file>.txt                                # re-distill, no API cost

/wisdom-apply <your situation>      # apply the library, citing notes
/wisdom-build decisions             # on demand: rebuild a method from all its notes
```

For local files you can also put metadata in a sidecar next to the file, e.g.
`grandma.meta.json`: `{"speaker": "Grandma Ana", "context": "childhood story", "recorded": "2026-11"}`.

Commit notes in the library repo, never in this one:
`git -C library add -A && git -C library commit -m "note: <topic>" && git -C library push`

### How methods stay up to date

Each note is tagged with the one or two **usage areas** where it gives real,
usable content: `decisions`, `idea-testing`, `brainstorming`, or `discussions`.
Each area gets one merged method in `library/methods/<area>.md`. You don't need
to remember to build it:

- **Automatic, on every `/wisdom-ingest`:**
  - when an area reaches 3 notes, its first method is created;
  - after that, a new note edits the method only if it adds, refines, or
    contradicts a step, and the edit is kept as small as possible;
  - the ingest reports each change in one line, e.g.
    "decisions: added a pre-mortem step from kahneman".

  The suggested commit includes the note and the method edits together, so one
  `git -C library revert <commit>` undoes the whole ingest if you don't like it.
- **On demand, `/wisdom-build <area>`:** rebuilds a method cleanly from all its
  notes. Use it now and then, because many small edits erode structure, or to
  build a method before an area has 3 notes.
- **Safety net, `bin/check`:** shows each area's note count and method state. It
  warns when an area has 3+ notes but no method, or when a method hasn't taken a
  note into account yet. Warnings don't block commits; errors do.

### Shell only

The extraction steps work without an agent:

```bash
bin/transcribe "<video-url-or-media-file>"   # → inbox/<base>.txt (.srt, .json, .meta.json)
bin/transcribe --local "<...>"               # force local Whisper (or --mistral)
bin/extract "<pdf | url | text-file>"        # → inbox/<base>.md or .txt (+ .meta.json)
bin/check                                    # validate library/ and skills, show area/method status
```

- **Transcripts** are timestamped: speaker turns with Mistral
  (`[12:34] Speaker 1: ...`), or one paragraph per minute or so with local Whisper.
  Audio is converted to mono 16 kHz first.
- **Re-runs** reuse saved output unless you pass `--force`, so you never pay twice.
  Switching provider for an existing transcript also needs `--force`.
- **PDFs** are read with `pdftotext`. Pages without a text layer are OCR'd with
  Tesseract (`OCR_LANG`, default `eng+ron`). Output keeps `<!-- page N -->` markers
  so notes can cite pages.

### Transcription providers

| | Mistral Voxtral (cloud) | whisper.cpp (local) |
|---|---|---|
| Setup | `MISTRAL_API_KEY` | `brew install whisper.cpp` + one-time model download |
| Cost / privacy | paid per minute; audio is uploaded | free; audio never leaves your machine |
| Speaker labels | yes (`Speaker 1`, `Speaker 2`, …) | no: the agent works out who's speaking from content |
| Length | max 1 h per request; longer audio is chunked automatically (speaker numbers restart per chunk, marked in the transcript) | no limit |
| Languages | auto-detected | ~100 languages incl. Romanian, auto-detected |

`bin/transcribe` uses Mistral when a key is available, otherwise local. Override
with `--local` / `--mistral` or `TRANSCRIBE_PROVIDER`. Other settings:

- `TRANSCRIBE_LANGUAGE=ro`: forces the language. With Mistral this turns off
  timestamps and speaker labels (the API doesn't allow both), so leave it unset
  unless auto-detection fails.
- `WHISPER_MODEL`: `large-v3-turbo` (default, fast) or `large-v3` (slower, a bit
  more accurate, ~3.1 GB).
- `TRANSCRIBE_CHUNK_SECONDS`: Mistral chunk length (default 3300 = 55 min).

## Development

```bash
python3 -m unittest discover -s tests -v                     # unit tests (stdlib only)
shellcheck -x bin/_common.sh bin/transcribe bin/extract bin/init-library
```

The tests use fixture notes and never call an API or the network.
`.github/workflows/ci.yml` (GitHub Actions) runs the same checks on every push
and pull request.

## Layout

```
bin/            transcribe, extract, check, init-library (+ lib/ helpers)
.agents/skills/ /wisdom-ingest, /wisdom-apply, /wisdom-build (the only copy)
.claude/skills/ symlinks into .agents/skills/ for Claude Code
tests/          unit tests (python3 -m unittest discover -s tests)
.github/workflows/  GitHub Actions CI workflow
inbox/          raw transcripts and audio — local only, gitignored
library/        YOUR notes — separate private repo, gitignored
  notes/          OKF bundle, one note per source; index.md lists them
  methods/        merged methods per usage area, maintained automatically
  journal/        decision records from /wisdom-apply
```

## Privacy

Nothing personal is committed here. `inbox/`, `library/`, and `.env` are
gitignored. Audio goes to Mistral's API when that provider is used, which is the
default whenever `MISTRAL_API_KEY` is set. Use `--local` (or `TRANSCRIBE_PROVIDER=local`)
to keep audio on your machine. PDFs, articles, and text are always
processed locally. The text you distill goes to whichever AI agent you use.

## License

[MIT](LICENSE)
