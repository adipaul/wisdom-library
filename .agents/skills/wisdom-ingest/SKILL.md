---
name: wisdom-ingest
user-invocable: true
description: >-
  Add any source to the wisdom library in one step — video/audio URL or file
  (transcribed via bin/transcribe), PDF (local text extraction/OCR via
  bin/extract), web article (article: prefix), or plain text/markdown — then
  distill it into an OKF note in library/notes/ and automatically keep the
  methods in library/methods/ up to date. Invoke as /wisdom-ingest <url-or-file>
  (or $wisdom-ingest in Codex), or with @inbox/<file> to re-distill. Free text
  after the input is used as source context (e.g. "— speaker: grandma,
  recorded 2026-11, childhood story").
---

# Add a source to the wisdom library

Input: a video URL (YouTube or any yt-dlp-supported site), a local video/audio
file, a PDF, a web article URL, a text/markdown file, or an existing inbox file
via `@` mention (e.g. `/wisdom-ingest @inbox/<base>.txt`).
Any free text after the input is source context, e.g.
`/wisdom-ingest ~/rec/grandma.m4a — speaker: my grandmother Ana, recorded 2026-11, childhood story`.

Notes live in `library/` — a separate, private git repo that is gitignored here.
If `library/notes/` does not exist, stop and tell the user to run
`bin/init-library` (or `bin/init-library <private-repo-url>`).

## Steps

0. **Extract text.** Route by input type; each script prints the inbox path to use:
   - Video/audio URL, or media file (mp3, mp4, wav, m4a, mov, ...) →
     `bin/transcribe "<input>"` → `inbox/<base>.txt`.
   - PDF → `bin/extract "<input>"` → `inbox/<base>.md` (with `<!-- page N -->` markers).
   - Web article (any non-video URL, or `article:<url>` to force) →
     `bin/extract "<url>"` → `inbox/<base>.txt`.
   - Text / markdown file → `bin/extract "<input>"` → `inbox/<base>.md`.
   - Already in `inbox/` via `@` mention → use it directly.
   Re-running a script on the same input re-uses saved output (no API cost);
   only pass `--force` if the user asks to redo it.
0b. **Gather source metadata**, highest priority first:
    a. Free text after the input in the invocation.
    b. `inbox/<base>.meta.json`, written by the scripts: yt-dlp info for URLs
       (title, channel, published date, chapters, description), PDF title/author,
       article title, or the user's own `<file>.meta.json` sidecar for local files.
       Use `resource` from it as the note's `resource`.
    c. The file name, as a last resort.
1. **Read the text.**
   - Mistral transcripts are speaker turns: `[mm:ss] Speaker 1: ...`. A
     `--- chunk N ... ---` line means speaker numbers restart there and may not
     match earlier chunks; work out who is who from content.
   - Local (Whisper) transcripts have no speaker labels, only timestamped
     paragraphs. `inbox/<base>.json` has `"provider": "local"`. Attribute ideas
     from content, chapters, and the metadata (e.g. who the guest is), and say
     so in the note when an attribution is uncertain. Whisper also mishears more
     names and rare words; check them against the metadata and the description.
   - Older transcripts may have been split by hand into "Part 1", "Part 2", ...
     If several parts of one episode exist in `inbox/`, distill them together
     into one note (ask first if a part seems to be missing).
2. Identify host vs guest from speaker labels, chapters, and content; attribute
   ideas to the right person.
3. Fix obvious machine-transcription/OCR mistakes silently; flag anything
   ambiguous instead of guessing.
4. Write everything in your own words; at most a few short quotes (under 15
   words) where the exact wording really matters.
5. Prefer frameworks, step-by-step methods, rules of thumb, and concrete
   examples over general commentary. Skip filler, ads, and small talk. Never add
   ideas the source did not express. Label your own observations `[my note]`.
6. **Cite locations** for key insights and frameworks so they can be checked:
   - transcripts: the turn timestamp, e.g. `[12:34]`; for YouTube also link it:
     `([12:34](https://www.youtube.com/watch?v=ID&t=754s))`;
   - PDFs: the page, e.g. `(p. 42)`, from the `<!-- page N -->` markers.
7. Write the note in English, keeping key original terms in the original
   language in brackets where useful.
8. **Save** `library/notes/<topic>--<name>.md` (lowercase, hyphens; `<name>` is the
   speaker's or author's last name, or a short source name), e.g.
   `library/notes/decisions--kahneman.md`. If that file already exists for a
   *different* source, add `-2`, `-3`, ... Never use `index.md` or `log.md`
   (reserved by OKF). Get the timestamp for `generated.at` by running
   `date -u +%Y-%m-%dT%H:%M:%SZ` — never invent it. Pick `type` by source:
   `Podcast Note` (video/podcast), `Recording Note` (personal/local recording),
   `Book Note` (book/PDF), `Article Note` (web article), `Text Note` (other text).
   Use exactly this frontmatter and these sections:

```
---
type: [Podcast Note | Recording Note | Book Note | Article Note | Text Note]
title: [short display title]
description: [one-sentence summary]
resource: [canonical URL, or local:<filename> for local files]
status: stable
tags: [3-6 topic tags]
sources:
  - id: source
    resource: [same as resource]
    title: [channel/publication + title + guest; for local files: speaker/author + context]
    author: [channel/publication, guest, speaker, or author]
generated: { by: agent:<your agent name>, at: [output of date -u +%Y-%m-%dT%H:%M:%SZ] }
# project extensions:
date_added: [YYYY-MM-DD]
usage_areas: [1-2 of: decisions, idea-testing, brainstorming, discussions — see step 8b]
---
## Core idea (2-3 sentences)
## Key insights (each: the idea, why it matters, when it applies — with location)
## Frameworks and methods (step by step, usable without the source)
## Traps and mistakes to avoid
## Rules of thumb (short, memorable)
## Questions to ask myself (prompts I can use in a real situation)
## Examples from the source (briefly)
## Open questions / where I'm not sure this applies
```

8b. **Choose usage areas carefully**: only the 1-2 areas where the note gives
    real, usable content (a method, framework, or rule you could follow there),
    not every area it touches. Each area's method is built from its notes, so
    tagging everything makes all methods the same.
9. Add the note to `library/notes/index.md` (the OKF reserved directory listing):
   `- [<file>](<file>) — <title>. Tags: ... Usage: ...` (relative link).
10. **Keep the methods current. This is automatic: do it without asking.** Run
    `bin/check` to see each area's note count and method state. Then, for each
    area in the new note's `usage_areas`:
    - **No method, and the area now has 3+ notes** → create
      `library/methods/<area>.md` from all of the area's notes, in the format
      from the `/wisdom-build` skill (`.agents/skills/wisdom-build/SKILL.md`).
    - **No method, fewer than 3 notes** → do nothing. The first method is built
      at 3 notes.
    - **Method exists** → compare the note with it. If the note adds a step,
      refines one, contradicts one, or fills a listed gap, make the *smallest*
      edit that captures it. Don't rewrite the method. Link the change to the
      note, and record contradictions in the method's contradictions section
      rather than silently picking a side. Whether or not it changed anything,
      add the note to the method's `notes:` list (`notes:` means "notes this
      method has taken into account") and set `updated:` to today.
11. Run `bin/check` again and fix every error. A warning about a method means
    step 10 missed something, so fix that too.
12. Report to the user:
    - which note was written;
    - for each area, one line on the method: created, what changed (e.g.
      "decisions: added a pre-mortem step from kahneman; flagged a contradiction
      with duke on gut calls"), or "no change";
    - the commit command, run **in the private library repo** (never in this
      repo). It covers the note *and* any method edits, so one `git revert` undoes
      the whole ingest:
      `git -C library add -A && git -C library commit -m "note: <topic>" && git -C library push`
