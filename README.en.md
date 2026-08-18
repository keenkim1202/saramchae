<img src="assets/saramchae.png" alt="" width="132">

# saramchae

[한국어](README.md) · English

**사람체** *(saramchae)* —
사람 "person" + 글씨체 "typeface." The shape of writing a person actually produces.

A pair of [Claude Code](https://claude.com/claude-code) and [Codex](https://developers.openai.com/codex) skills that strip the AI tells out of a document.
A scanner measures the document before a word is rewritten,
so the edits land on lines you can point at rather than on a general impression.

## What it does

Three cases. Left is what came in, right is what went out.

### 1. Voice — the AI tells

<!-- saramchae:off -->
<table>
<tr><th width="50%">before</th><th width="50%">after</th></tr>
<tr valign="top"><td>

This document delves into the realm of cache invalidation strategy,
examining the limitations inherent in our existing approach and offering a direction for improvement going forward.

**Therefore,
we propose transitioning to a version-prefix approach.** This method does not simply clear the cache but rather separates the keys themselves,
and it may play a crucial role in terms of overall deployment stability.

In conclusion,
this transition could be seen as a testament to the team's evolving deployment culture.
Feel free to reach out if you have any questions!

</td><td>

Here is how cache invalidation should change.

We move to a version prefix on the key. Instead of flushing the cache we separate the keys,
so a deploy no longer empties the whole cache at once.

That takes a lot of the risk out of deploying.

</td></tr>
</table>
<!-- saramchae:on -->

Same three paragraphs, same claims, same register.
What changed is whether the sentences carry their weight.

- AI vocabulary — `delve`, `realm`, `crucial`, `testament`
- Stacked hedges — `could arguably be considered significant`
- Negative parallelism — `not simply X but rather Y`. Write the positive half only
- Chat residue — `Feel free to reach out if you have any questions!`
- Bold wrapped around a whole sentence
- A 40-word sentence split in two

**No claim changed.** Inventing a number the source never made, or swapping the register,
is rewriting rather than editing, and this skill does not do it.

### 2. Bullets doing the work of prose

<!-- saramchae:off -->
<table>
<tr><th width="50%">before</th><th width="50%">after</th></tr>
<tr valign="top"><td>

- The current approach flushes the entire cache on every deploy,
  which means that for the first minute or so after a release every single request has to go to the database,
  and that is exactly when traffic is highest.
- This is not something we can solve by scaling the database,
  because the cost is in the cold start rather than in steady-state load.

</td><td>

The current approach flushes the whole cache on every deploy,
so for the first minute after a release every request goes to the database —
exactly when traffic peaks.
Scaling the database does not help,
because the cost is in the cold start rather than in steady-state load.

</td></tr>
</table>
<!-- saramchae:on -->

These are not list items. They are two connected sentences of an argument,
and the second depends on the first.
Bulleting them hides that dependency and asks the reader to reconstruct it. The scanner names the shape:

```
[4] lists: bullet ratio 100% (2/2), ... fat items 1
```

A bullet carrying a 200-character clause is prose wearing a bullet.

### 3. An enumeration buried in a sentence

<!-- saramchae:off -->
<table>
<tr><th width="50%">before</th><th width="50%">after</th></tr>
<tr valign="top"><td>

This sprint we made three changes: first, the token refresh logic in the auth module was fixed;
second, the payment API timeout went from 3 to 10 seconds; and finally,
the log collector now includes worker process logs it had been dropping.

</td><td>

Three things changed this sprint:

- Token refresh in the auth module, fixed
- Payment API timeout, 3s → 10s
- Worker process logs the collector had been dropping, now included

</td></tr>
</table>
<!-- saramchae:on -->

Forty-two words holding three parallel items behind `first` / `second` / `finally`:

```
[2] sentence length: 1 long
    L1  42 words / 4 clauses  This sprint we made three changes: first, the token …
[4] lists: ... prose that reads as a list: L[1]
```

This runs opposite to case 2, which is the point.
**Neither fewer bullets nor more bullets is the goal;
the shape that matches the content is.** Parallel items are a list. A connected argument is prose.

A whole document going through the process is in [`demo/`](demo/):
`before.md`, `after.md`, and a table of what the scanner caught in each.

## Quick start

No clone needed. Two lines:

```bash
# Claude Code — inside a session
/plugin marketplace add keenkim1202/saramchae
/plugin install saramchae@saramchae
```

```bash
# Codex — from a terminal
codex plugin marketplace add keenkim1202/saramchae
codex plugin add saramchae@saramchae
```

<details>
<summary>Or copy the directories in by hand</summary>

```bash
git clone https://github.com/keenkim1202/saramchae.git
cd saramchae
cp -r saramchae saramchae-ko ~/.claude/skills/     # Claude Code
cp -r saramchae saramchae-ko ~/.codex/skills/      # Codex
```

For one project only, use `<project>/.claude/skills/` or `<repo-root>/.agents/skills/` instead.
Copy only the directory you need if you work in one language.

</details>

It loads from the next session. Then call it:

```
/saramchae README.md     # Claude Code
$saramchae README.md     # Codex
```

You don't need the name. Any of these reaches it:

> make this read like a human · strip the AI tells · check readability · clean up this doc

### Which one to install

| Skill | Use it when |
|---|---|
| [`saramchae`](saramchae/SKILL.md) | The document is **not** in Korean |
| [`saramchae-ko`](saramchae-ko/SKILL.md) | The document is **in Korean**. Everything below, plus three checks that only exist in Korean |

Install only the one you need. Do not run both on one document.

## What it catches

A document fails in two ways at once, and a reader experiences both as the same problem,
so both get handled.

One is **voice** — the AI vocabulary, the stacked hedges, the chat residue.

The other is **shape** — a 340-character paragraph,
nine nested bullets where two sentences belonged, sentence-level bold on every third line,
which leaves no emphasis at all.

| Check | `saramchae` | `saramchae-ko` |
|---|---|---|
| AI vocabulary and hedging | ✓ | ✓ |
| Sentence length | by word count | by **clause count** |
| Line breaks — source wrapping, paragraph breaks | ✓ | ✓ |
| Lists — buried enumerations out, bullet soup back to prose | ✓ | ✓ |
| Emoji and decoration | ✓ | ✓ |
| Bold — sentence-level goes, term-level stays | ✓ | ✓ |
| Headings — title case, section length | ✓ | — |
| **Speech level** — 평서체 *plain* and 존댓말 *polite* mixed in one document | — | ✓ |
| **Translationese** — 번역투, Korean bent into English syntax | — | ✓ |
| **Hard words** — 한자어 Sino-Korean where a plain native word exists | — | ✓ |

The three Korean-only checks have no English equivalent,
which is why they live in a separate skill rather than as extra rules in this one.

Sentence length is measured differently in each.
English runs long by word count; Korean runs long by **clause chaining** — `~하며`,
`~하고` strung end to end.
A short Korean sentence with five clauses is harder to read than a long one with two,
so counting characters would miss it.

Thresholds are sourced, not invented. Each `SKILL.md` names the reference every number came from.

## What it never touches

Getting this wrong is worse than leaving the document alone.

| Protected | Why |
|---|---|
| **Verbatim records** — transcripts, logs, chat exports | Rewording destroys the thing they exist to prove |
| Code fences, command output, stack traces | Line breaks are data there |
| Tables | The row is the unit. A table never gets flattened into bullets |
| Numbers, IDs, hashes, paths, API field names, versions | A value is never paraphrased |
| Quotations from a source document | A requirement quoted from a spec stays word for word |
| `CLAUDE.md` and agent instruction files | Imperative voice and heavy bold are *functional* there, not decoration |

Frontmatter is exempt from every check.

## Running the scanner alone

Sometimes you want the numbers without the edits. The scanner runs on its own:

```bash
python3 ~/.claude/skills/saramchae/scripts/scan.py FILE
```

The before document above reports this:

```
[1] voice: flagged words 4, negative parallelism 2, stacked hedges 1, chat residue 1
    delve×1, crucial×1, realm×1, testament×1
    L5  It's worth noting that the current system flushes …
    chat residue at L[13]

[2] sentence length: 3 long (n=8)
    L5  40 words / 4 clauses  It's worth noting that the current system flushes th…
    L7  35 words / 4 clauses  **Therefore, we propose transitioning to a version-p…

[6] bold: sentence-level 1 / term-level 0

[7] headings: 1 over 13 lines, title-cased 1
```

**Read the output as triage,
not as a verdict.** Most documents fail two of the checks and that is normal.
A finding you cannot see when you look at the line is a false positive — drop it.
Section 7 of each `SKILL.md` lists what every number gets wrong.

### Wiring it into CI

`--json` gives machine-readable counts and `--fail-over` turns it into a gate.
Both take any number of files and directories; a directory is searched recursively for `*.md`.

```bash
python3 scan.py --json docs/                    # every file, as JSON
python3 scan.py --fail-over 10 docs/ README.md  # exit 1 if any file exceeds 10 findings
```

`total` is a **raw sum, not normalized for length**, so a long document naturally scores higher.
Measure your own repository once before picking a threshold.

### When a document quotes bad prose

A style guide, a changelog quoting a bug report, a before/after specimen —
**a document about bad prose is full of it.** Left alone,
the document reports its own examples back to itself.

Wrap the region and neither the scanner nor the agent will touch it.
These are HTML comments, so they do not render.

```markdown
<!-- saramchae:off -->
This document delves into the realm of improvement opportunities going forward.
<!-- saramchae:on -->
```

The three before/after tables above are wrapped exactly this way.
Unwrapped this README scores 26; wrapped, 12.
The remaining 12 are things the document actually does.

A marker shown inside a code fence, as in the example above,
**does not count as a marker.** A document explaining the syntax would otherwise blank itself.

## License

[MIT](LICENSE).

Parts of each `SKILL.md` are a derivative work of the `humanizer` skill by [@blader](https://github.com/blader/humanizer),
as adapted in [softaworks/agent-toolkit](https://github.com/softaworks/agent-toolkit/tree/main/skills/humanizer) —
both MIT.
Each skill's Credits section names exactly which of its sections those are.

The upstream copyright notices and license terms are reproduced in full in [NOTICE](NOTICE).

The speech-level check, the structural checks, both scanners, and the verification are original.
