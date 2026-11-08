---
name: wisdom-apply
user-invocable: true
description: Apply the wisdom library to a personal situation (a decision, a discussion, an idea, or "how would this go?"). Reads library/notes/index.md and the relevant notes and methods, applies their frameworks to the actual situation, and cites the source note for each idea. Can save a decision record to library/journal/. Invoke as /wisdom-apply <situation>.
---

# Apply the library to my situation

1. Read `library/notes/index.md` first (titles, tags, usage areas), then
   `library/methods/` for a merged method covering this kind of situation. Then
   grep `library/notes/` for keywords from the situation and read the matching notes.
2. Apply the relevant frameworks to the actual situation — do not just
   summarize them.
3. Cite each idea to its note, e.g. "per Kahneman (library/notes/decisions--kahneman.md): ...".
4. If notes disagree, show both views and help weigh them.
5. If nothing in the library fits, say so explicitly, then help with general
   reasoning.
6. Ask at most one clarifying question if key information is missing.
7. For a real decision, offer (do not do it unasked) to save a decision record
   so it can be reviewed later on process quality, not just outcome:
   `library/journal/<YYYY-MM-DD>-<slug>.md` with: the situation, options
   considered, the choice and reasoning, notes used, expected outcome, what
   would change my mind, and a review date. Suggest committing it in the
   private library repo: `git -C library add -A && git -C library commit -m "journal: <slug>"`.
