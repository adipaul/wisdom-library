---
name: wisdom-build
description: Rebuild (or build early) the combined method for one usage area (decisions, idea-testing, brainstorming, discussions) from all of its notes into library/methods/<area>.md. On demand only — /wisdom-ingest already creates and updates methods automatically. Invoke as /wisdom-build <area>.
---

# Rebuild a method from the library (on demand)

Methods are normally maintained automatically: `/wisdom-ingest` creates an
area's first method once it has 3 notes, and makes small edits when a new note
changes something. Use this skill to:
- **rebuild cleanly**, because many small automatic edits slowly erode a method's structure;
- **catch up**, when `bin/check` warns that a method hasn't taken some notes into account;
- **build early**, before an area reaches 3 notes.

## Steps

1. Find the area's notes: `bin/check` lists counts per area. Then grep
   `usage_areas` across `library/notes/` (`library/notes/index.md` lists every note).
2. If the area has fewer than 3 notes, say so and list them, and ask whether to
   build anyway. A method from 1-2 notes is mostly one person's view.
3. If `library/methods/<area>.md` exists, read it first. Keep anything the user
   added by hand (anything not traceable to a note) and say what you kept.
4. Write `library/methods/<area>.md` from **all** the area's notes: one
   practical, step-by-step combined process. Link each step to the notes it
   comes from. Use this format (`/wisdom-ingest` edits files in this format too):

```
---
title: [Area] method
area: [decisions | idea-testing | brainstorming | discussions]
built: [YYYY-MM-DD — date of the last full rebuild]
updated: [YYYY-MM-DD — date of the last change of any kind]
notes: [every note file in this area, e.g. decisions--kahneman.md]
---
## When to use this
## The method (step by step, each step linked to its notes)
## Rules of thumb
## Contradictions between notes (both views, and when each applies)
## Gaps (what none of the notes cover yet)
```

5. Report what changed compared to the previous version, if there was one.
6. Run `bin/check` (it must show the method as "current"), then suggest
   committing in the private library repo:
   `git -C library add -A && git -C library commit -m "method: rebuild <area>"`.
