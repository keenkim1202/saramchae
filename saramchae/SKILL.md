---
name: saramchae
description: Make a document read like a person wrote it — AI vocabulary and hedging out, over-long sentences split, source wrapping and paragraph breaks fixed, buried enumerations turned into lists and bullet soup turned back into prose, emoji cut to what carries meaning. Ships a scanner that measures everything before a word is edited. Use on "make this read like a human", "strip the AI tells", "check readability", "clean up this doc", "polish this README". This is the non-Korean one: if the document being edited is written in Korean, use `saramchae-ko` instead, which adds 어체, 번역투 and 한자어 on top of everything here.
---

# saramchae — writing that reads like a person wrote it

사람체: 사람 + 글씨체. The shape of writing a person actually produces.

A document fails in two ways at once, and most tools only see one. It *sounds* generated —
`delve`, `robust`, hedges stacked three deep. And it is *shaped* wrong — one 400-word paragraph, or
nine nested bullets where two sentences belonged. This skill covers both, because the reader
experiences both as the same problem.

**For Korean, use [`saramchae-ko`](../saramchae-ko/SKILL.md).** It carries every check here plus the
ones that only exist in Korean: 어체 consistency, 번역투, 한자어. Do not run both on one document.

---

## 1. Never touch these

Getting this wrong is worse than leaving the document alone.

| Zone | Why |
|---|---|
| **Verbatim records** — transcripts, logs, chat exports | Rewording destroys the thing they exist to prove. When a spec demands an "unedited" record, editing prose *is* editing. Only credential masking is exempt |
| Code fences, command output, stack traces | Line breaks are data there |
| Tables | The row is the unit. Never flatten a table into bullets to "simplify" |
| Numbers, IDs, hashes, paths, API field names, versions | Never paraphrase a value |
| Quotations from a source document | A requirement quoted from a spec stays word-for-word |
| `CLAUDE.md` and agent instruction files | Imperative voice and heavy bold are *functional* there. A 90% bullet ratio is correct for a file an agent parses |
| Anything between `<!-- saramchae:off -->` and `<!-- saramchae:on -->` | The author marked it. Do not edit it and do not report it — the scanner already blanks it |

Frontmatter is exempt from every check — a `description` field is one long line on purpose.

A document *about* bad prose is full of bad prose: a style guide, a changelog quoting a bug report,
a before/after specimen. That is what the `saramchae:off` marker is for. If you find yourself
reporting a document's own examples back to it, the region needs the marker rather than an edit.

If the user says "apply it to everything", still exclude the first row and say why in one line.

---

## 2. Do not add personality

The skill this one descends from has a section telling you to inject opinions, first person, and
lines like *"I genuinely don't know how to feel about this."* **Ignore that for technical
documents.** It was written for blog posts.

A design note, a decision record, or a hiring submission is read by someone deciding whether to
trust the work. Injected voice reads as padding at best and as unseriousness at worst.

What to do instead:

- Plain declarative sentences. Pick one register and hold it for the whole document
- Vary sentence length naturally, but do not manufacture rhythm
- Keep the author's own judgments where they exist. Deleting "this is risky" and leaving only
  neutral description is over-correction, not neutrality

---

## 3. Measure first

The scanner sits next to this file, at `scripts/scan.py`. **Resolve it from this skill's own
directory, not from the working directory** — the working directory is the project being edited,
which is not where the skill is installed:

The directory depends on which agent loaded this skill and whether it was installed for one project
or for all of them. Use whichever of these exists:

```bash
# Claude Code
SCAN=~/.claude/skills/saramchae/scripts/scan.py
SCAN=<project>/.claude/skills/saramchae/scripts/scan.py

# Codex
SCAN=~/.codex/skills/saramchae/scripts/scan.py
SCAN=~/.agents/skills/saramchae/scripts/scan.py
SCAN=<repo-root>/.agents/skills/saramchae/scripts/scan.py

python3 "$SCAN" FILE
```

If none of them resolve, find it instead of guessing: `find ~ -name scan.py -path '*saramchae*'`.

Read the output as triage, not as a verdict. Most documents fail two checks, not seven. Section 7
lists what each number gets wrong; **a finding you cannot see when you look at the line is a false
positive**, so drop it and say you did.

If everything is clean, say so and stop. Not every document needs this.

---

## 4. The checks

### 4.1 Vocabulary

Delete before you substitute. Most of these are connectors and intensifiers that carry nothing:

```
delve  leverage  utilize  foster  embark  robust  seamless  comprehensive  moreover
furthermore  ultimately  notably  essentially  crucial  pivotal  realm  landscape
underscore  testament  navigate  synergy  tapestry  intricate  multifaceted  paradigm
holistic  streamline  harness
```

> **Domain terms are not on this list.** Idempotency, backpressure, deserialization, race condition
> are the words. Replacing a precise term with a description makes the document longer and less
> exact. If a term has no shorter accurate equivalent, it stays — even if it looks hard.

### 4.2 Structural voice tells

- **Inflated significance** — `a watershed moment`, `plays a crucial role in`. Say what it does
- **Negative parallelism** — `not just X, but Y`. Overused past the point of invisibility. Write the
  positive half
- **Forced triads** — three items because three sounds complete. If there are two, write two
- **Hedge stacking** — `this might potentially be somewhat useful`. Say it once, or say it is unknown
- **Synonym cycling** — user → customer → account holder for one thing. **In technical writing,
  repeat the term.** A reader tracking `User` should not have to deduce that "account holder" is the
  same object
- **Chat residue** — `Hope this helps`, `Let me know if`, `In conclusion`. Delete outright
- **Uniform sentence length.** Generated prose runs at one readability level; human writing is lumpy
  because some points need more room. A page where every sentence is 18 words is as much a tell as
  one where every sentence is 40
- **Heading inflation** — `##` and `###` in a document too short to need them. Under ~40 lines, one
  heading level is usually enough
- **Title Case In Every Heading.** Sentence case unless the project's style says otherwise

### 4.3 Sentence length

| Script | Flag at | Hard limit |
|---|---|---|
| Alphabetic | 25 words | 30–35 |
| CJK | 90 characters | — use clause count |

Average 15–20 words is the plain-language target; technical writing runs 20–25 and that is fine.
Comprehension holds steady to about 20 words, then falls off sharply.

The fix is to split at the conjunction and promote the second half to its own sentence. **Do not
chop everything to one length** — uniform short sentences are their own tell (4.2). Fix the
sentences carrying more than one claim; leave a long sentence that is genuinely one thought.

### 4.4 Line breaks

Three different things get called a line break. Fix them separately.

**Source line width.** [Semantic line breaks](https://sembr.org/) — one sentence per source line,
breaking after an independent clause, wrapping under 80 characters. A one-word change stays a
one-line diff instead of reflowing the paragraph. Worth doing on anything under version control.

> ⚠️ **Check the renderer first.** In a `.md` file a single newline joins with a space, so this is
> invisible in the output. In a GitHub issue or PR comment, in Notion, and in most chat renderers, a
> single newline **is** a line break, and applying sembr there reshapes the rendered document. The
> spec's own rule is that semantic line breaks must not alter rendered output — on those targets,
> obeying it means not doing this.

**Paragraph breaks.** Over ~700 characters with no blank line is a wall (~300 for CJK, which packs
far more per character). Break at the topic shift, not at a count.

The opposite failure is as common: every paragraph one sentence long, which is a list that forgot
its bullets. If consecutive one-sentence paragraphs are parallel, make them a list. If not, join them.

**Rendered breaks.** Never use a trailing double-space — invisible in source, and most formatters
strip it. Use a blank line, or a list. `<br>` only inside a table cell, where nothing else works.

### 4.5 Lists and numbering

Both directions matter. The scanner reports a bullet ratio: **over ~60% is soup; under ~10% in a
procedural document usually means a buried list.**

**Prose → list** when the prose contains an enumeration in sentence form (`first… second… finally`),
three or more parallel items chained with `and`, ordered steps buried in a paragraph
(→ **numbered**), or two things compared on the same axes (→ a **table**).

**List → prose** when one idea needs explanation rather than segmentation, when a list has exactly
one item, when items run past ~200 characters, when adjacent items depend on each other (the
dependency is the connective that got dropped), or when the whole document is bullets — readers
describe that as running an obstacle course.

| Rule | Detail |
|---|---|
| Length | 2–7 items. Over 7, group under sub-headings or use a table |
| Nesting | Two levels. A third is an outline pretending to be a list |
| Order | Bulleted for unordered, numbered for sequence or priority — never numbered to look organized |
| Parallelism | Every item the same grammatical shape: all noun phrases, or all verb-initial |
| Lead-in | A complete sentence, a fragment ending in a colon, or a heading — not a heading *and* a colon |
| Punctuation | Periods only if items are complete sentences. Never a trailing `,` `;` `and` `or` |

### 4.6 Emoji and decoration

Screen readers speak each emoji's Unicode name aloud, so three in a row is three spoken phrases
dropped into a sentence.

| Use | Verdict |
|---|---|
| A legend defined once and used consistently (`🧩 plugin · 📄 skill`) | Keep |
| A persistent status marker in a working document (`⚠️` on a known trap) | Keep, sparingly |
| Heading decoration | **Cut.** Every one |
| One per bullet as visual rhythm | **Cut** |
| Standing in for a word | **Cut.** It survives neither a screen reader nor a grep |

None in headings, none in a document being submitted or graded, never three in a row. If emoji carry
meaning they need a legend; if they need a legend and there is only one, it is decoration.

**Em dash**: fine as a definition dash, but generated prose clusters them. Roughly one per 20 lines;
convert the rest to commas or parentheses. **Curly quotes**: straighten them.

### 4.7 Bold

Blanket bold-stripping ruins technical documents. Classify first.

| Kind | Example | Action |
|---|---|---|
| **Sentence-level** — a clause with a verb | `**Do not use this in production.**` | **Strip** |
| **Term / value** — a noun phrase, number, or label | `**512MB**`, `**read-only mode**` | **Keep.** A scanning aid, not decoration |

Budget: at most one sentence-level emphasis per section. A document where every third line is bold
has no emphasis at all. A high term-level count is normal and healthy in technical writing.

---

## 5. Procedure

1. **Scan** (section 3). Note which checks fired
2. **Read the whole file.** Bullet ratio and register cannot be judged from a diff
3. **Restructure before rewording** — move text between prose and lists first, since that decides
   which sentences still exist
4. **Then split sentences and fix words**, line by line — see section 6
5. **Re-scan** and confirm the numbers moved the way you intended
6. **Report as a table**: check, before, after. Name the findings you dropped as false positives

Apply the edits without waiting for approval. Stop and ask only when a fix would change what the
document *claims* rather than how it reads.

---

## 6. The regex trap

Do not do this:

```python
re.sub(r"\*\*(.{25,}?)\*\*", r"\1", line)     # WRONG
```

On a line with two bold spans it swallows the gap between them:

```
before:  **Cache invalidation**: flushed on deploy. Keys moved to a **version prefix**
after:   Cache invalidation**: flushed on deploy. Keys moved to a **version prefix
```

The marker count stays even, so a balance check does not catch it — the bold silently moved to the
wrong words. If you must batch, operate on one `**…**` span at a time and skip any line with more
than one. Better: targeted edits on the lines you actually decided to change.

The same applies to every rule here. A global substitution for a hedge word will hit it inside a
quotation you were told not to touch.

---

## 7. What the scanner gets wrong

- **Sentence splitting is punctuation-based.** A heading or a list item with no terminal period
  merges with what follows
- **Commas count toward the clause total but cannot trigger the check on their own.** A sentence
  needs at least one conjunction before the clause rule fires, so `alpha, beta, gamma, delta` reads
  as the list it is. The cost is that a long comma-spliced sentence is caught by its length alone
  or not at all
- **Bullet ratio counts lines, not ideas.** A file of one-line reference entries is legitimately 90%
  bullets — `CLAUDE.md` is the standard case
- **The vocabulary list has no context.** `robust` is correct in a sentence about error handling.
  This is why the list is triage, not a find-and-replace
- **Bold classification uses word count and terminal punctuation only.** A six-word noun phrase
  reports as sentence-level
- **Emoji ranges are approximate.** Arrows and `·` are excluded deliberately as technical
  punctuation, so a document decorating with `→` reports zero
- **Title-case detection needs three long words**, so a two-word heading is never flagged

---

## 8. Verification

Restructuring can drop content in a way that re-reading does not catch.

```bash
# Nothing left the document: fences, tables, headings unchanged in count
grep -cE '^\s*(`{3,}|~{3,})' FILE; grep -c '^|' FILE; grep -c '^#' FILE
# Values that must survive verbatim
grep -o '[0-9][0-9.]*\(ms\|s\|MB\|%\)' FILE | sort | uniq -c
# Where you only re-wrapped source lines, no words moved
git diff --word-diff=porcelain FILE | grep -c '^[+-][^+-]'
```

The last one is the sembr check: a pure re-wrap adds and removes no words. Any hit means the re-wrap
also changed the text.

Then one structural test — **a bold span whose content starts with punctuation**, which is the exact
shape section 6 damage takes:

```bash
python3 - FILE <<'PY'
import re,sys,pathlib
fence=open_bold=False; n=0
for i,raw in enumerate(pathlib.Path(sys.argv[1]).read_text().splitlines(),1):
    if raw.lstrip().startswith("```"): fence = not fence; continue
    if fence or raw.startswith("|"): continue      # code blocks and tables are exempt
    line=re.sub(r"`[^`]*`","·",raw)                # inline code → placeholder, never deleted:
                                                   # `**`Int`**` would collapse to **** and read as empty
    parts=line.split("**")
    if not open_bold:                              # only self-contained spans are readable
        for j in range(1,len(parts),2):            # odd indices are bold contents
            if parts[j][:1] in ":：,，.。)]" or not parts[j].strip():
                print(f"{i}: bold span starts with punctuation — {parts[j][:50]}"); n+=1
    if (len(parts)-1)%2: open_bold = not open_bold  # bold wrapped onto the next line
if open_bold: print("EOF: a bold span was never closed"); n+=1
print(f"{n} finding(s)")
PY
```

It deliberately tracks delimiter parity across lines rather than grepping: bold wrapped onto the
next line is normal in prose, and a naive check reports every legitimate `**Term**: definition` as
damage.

---

## 9. Extra rules for graded or submitted documents

When a reviewer is judging the work:

- No emoji anywhere, including body text
- No first-person color (`I think`, `it feels like`). State the judgment and its basis
- Quotations from the spec stay verbatim, in quotes — never paraphrase a requirement
- Keep every number, log line, and reproduction command. **Density of evidence is the point**;
  trimming it to read smoothly defeats the document
- One register throughout. Check the last paragraph against the first

---

## Credits

Sections 1, 2, 4.1, 4.2 and 4.7 are a **derivative work**. The rest — the structural checks (4.3
through 4.6), the scanner, and the verification — is original.

| | |
|---|---|
| Adapted from | [`humanizer`](https://github.com/softaworks/agent-toolkit/tree/main/skills/humanizer) in softaworks/agent-toolkit — MIT |
| Original skill by | [@blader](https://github.com/blader/humanizer) |
| Underlying source | [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup |

What this changes from upstream: it drops the "inject personality" section (§2), splits the bold
rule into sentence-level and term-level instead of stripping all of it (4.7), adds the protected
zones (§1), and adds the structural half that upstream does not address at all.

Thresholds in the structural sections are sourced, not invented:

| Claim | Source |
|---|---|
| 15–20 word average, comprehension drops past ~20 | [Readability guidelines](http://readabilityguidelines.wikidot.com/sentence-length) |
| One sentence per line, ≤80 chars, must not alter rendered output | [Semantic Line Breaks](https://sembr.org/) |
| 2–7 items, parallelism, bulleted vs numbered, list punctuation | [Microsoft Writing Style Guide — Lists](https://learn.microsoft.com/en-us/style-guide/scannable-content/lists) |
| When a paragraph beats a list | [Style Manual — bullet lists](https://www.stylemanual.gov.au/style-manual-resources/government-writing-handbook/section-2-write-so-your-meaning-clear/use-structure-make-it-readable-bullet-lists) |
| Screen readers speak emoji names; avoid runs | [Emojis and Web Accessibility](https://www.boia.org/blog/emojis-and-web-accessibility-best-practices) |
| Generated text has uniform readability where human writing varies | [Understanding Readability of LLM Output](https://www.sciencedirect.com/science/article/pii/S1877050924026905/pdf) |

Both upstream skills are MIT. Their copyright notices and license terms are reproduced in full in
[NOTICE](../NOTICE) at the root of this repository.
