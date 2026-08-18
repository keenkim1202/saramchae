---
name: saramchae-ko
description: Make a Korean document read like a person wrote it — 어체 mixing and 번역투 out, clause-chained sentences split, source wrapping and paragraph breaks fixed, buried enumerations turned into lists and bullet soup turned back into prose, emoji cut to what carries meaning. Keeps term-level bold and tables; strips sentence-level bold. Ships a scanner that measures all of it first, including a 평서체/존댓말 count. Use on "문체 다듬어", "AI 티 빼줘", "가독성 검토", "읽기 좋게 다듬어", "이 문서 다듬어", "사람체", "이 문서 사람이 쓴 것처럼", "humanize this Korean doc". Never touches verbatim records, code, tables, or numbers. This is the Korean one and covers everything `saramchae` does, so use it whenever the document being edited is written in Korean — reach for `saramchae` only when it is not.
---

# saramchae-ko — Korean documents that read like a person wrote them

사람체: 사람 + 글씨체. The shape of writing a person actually produces.

A document fails in two ways at once. It *sounds* generated — 번역투, a 존댓말 sentence dropped into
평서체 prose. And it is *shaped* wrong — a 340-character paragraph, or nine nested bullets where two
sentences belonged. The reader experiences both as the same problem, so this handles both.

**For a non-Korean document use [`saramchae`](../saramchae/SKILL.md).** The structural checks are the
same there; what is missing is everything in sections 4.1 through 4.3, which only exists in Korean.
Do not run both on one document.

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

If the user says "전부 적용해 줘", still exclude the first row and say why in one line.

---

## 2. Do not add personality

The skill this one descends from has a section telling you to inject opinions, first person, and
lines like *"I genuinely don't know how to feel about this."* **Ignore that for technical
documents.** It was written for blog posts.

A 설계 노트, a 결정 기록, or a hiring submission is read by someone deciding whether to trust the
work. Injected voice reads as padding at best and as unseriousness at worst.

What to do instead:

- Plain declarative sentences. **Pick one 어체 and hold it to the end of the document**
- Vary sentence length naturally, but do not manufacture rhythm
- Keep the author's own judgments. Deleting `이건 위험하다` and leaving only neutral description is
  over-correction, not neutrality

---

## 3. Measure first

The scanner sits next to this file, at `scripts/scan.py`. **Resolve it from this skill's own
directory, not from the working directory** — the working directory is the project being edited,
which is not where the skill is installed:

The directory depends on which agent loaded this skill and whether it was installed for one project
or for all of them. Use whichever of these exists:

```bash
# Claude Code
SCAN=~/.claude/skills/saramchae-ko/scripts/scan.py
SCAN=<project>/.claude/skills/saramchae-ko/scripts/scan.py

# Codex
SCAN=~/.codex/skills/saramchae-ko/scripts/scan.py
SCAN=~/.agents/skills/saramchae-ko/scripts/scan.py
SCAN=<repo-root>/.agents/skills/saramchae-ko/scripts/scan.py

python3 "$SCAN" FILE
```

If none of them resolve, find it instead of guessing: `find ~ -name scan.py -path '*saramchae-ko*'`.

Read the output as triage, not as a verdict. Most documents fail two of the seven checks. Section 7
lists what each number gets wrong; **a finding you cannot see when you look at the line is a false
positive**, so drop it and say you did.

If everything is clean, say so and stop. Not every document needs this.

---

## 4. The checks

### 4.1 어체 — the most common Korean-specific tell

LLMs drop a 존댓말 sentence into 평서체 prose, and the reverse. It is the single most frequent
Korean slip and the easiest to miss by eye. The scanner counts both and points at the minority:

```
[1] register: 평서체 6 / 존댓말 2  — mixed. minority 존댓말, 2 of them (25%)
    L3  …수 있도록 작성되었습니다.
```

Do not simply convert the minority. **Pick the 어체 that fits the document's purpose** and move
everything to it: 존댓말 for a README or user-facing guide, 평서체 for a 설계 노트 or 결정 기록.
Either way, check the last paragraph against the first.

### 4.2 번역투 and filler

| Tell | Fix |
|---|---|
| ~에 있어서 | ~에서 |
| ~을 통해 (overused) | ~로, ~으로 |
| ~하는 데 있어 | ~할 때 |
| ~의 경우 (unnecessary) | delete |
| ~라고 할 수 있다 / ~로 볼 수 있다 | state it directly |
| ~을 진행하다 / ~을 수행하다 | use the verb: 한다, 만든다, 돌린다 |
| 결론적으로 / 요약하면 / 종합해보면 | delete; the conclusion is the sentence itself |

**Inflated significance (번역투 과장)**

| Tell | Fix |
|---|---|
| ~에 있어 중요한 역할을 한다 | say what it does |
| ~의 분수령 / 이정표 / 큰 획을 긋는 | usually delete; if the claim is real, state it plainly |
| ~을 시사한다 / 방증한다 | 보여준다, or name the evidence |
| 핵심적인, 필수적인, 획기적인 (overused) | keep at most one per document |

> `이번 마이그레이션은 팀 배포 문화의 분수령이 될 것이다.`
> → `이 마이그레이션이 끝나면 배포가 주 1회에서 하루 여러 번으로 바뀐다.`

**Structural tells** — negative parallelism (`단순히 ~가 아니라 ~이다`: write the positive half
only), forced triads (three items because three sounds complete — if there are two, write two),
synonym cycling (사용자 → 유저 → 회원 for one thing: **in technical writing, repeat the term**), and
hedge stacking (`~일 수도 있을 것 같습니다` → say it once, or say it is unknown).

**Chat residue** — `도움이 되셨길`, `궁금한 점이 있으시면`, `~해보시기 바랍니다`, `물론입니다`,
`살펴보겠습니다`. Delete outright.

### 4.3 Hard words

The target is a 한자어 with a plain everyday equivalent.

> ⚠️ **This is where it goes wrong most often.** 멱등성, 역직렬화, 레이스 컨디션, 백프레셔 are not
> hard words, they are the words. Replacing a precise term with a description makes the document
> longer and less exact. If a term has no shorter accurate equivalent, it stays.

| Swap | For |
|---|---|
| 활용하다 | 쓰다 |
| 수행하다 / 진행하다 | 한다, 돌린다, 만든다 |
| 상이하다 | 다르다 |
| 소요된다 | 걸린다 |
| 기입하다 | 적는다 |
| 용이하다 | 쉽다 |
| 제반 ~ | delete it |
| 도모하다 / 극대화하다 | 늘린다, 높인다 |

### 4.4 Sentence length

**In Korean, clause count beats character count.** The tell is chaining, not length: `~하며`,
`~하고`, `~이며`, `~는데`, `~지만` strung together until one sentence carries four claims. Three or
more connectives is the signal whatever the length. Character count (flag at 90자) is the secondary
knob.

Split at the connective and promote the second half:

> `캐시 무효화는 배포마다 전체를 비우는 방식으로 동작하며, 이는 스테일 데이터를 방지하기 위한
> 것이고, 운영에서는 비용을 유발할 수 있으므로 버전 프리픽스를 활용하여 부분 무효화를 수행하는
> 것이 권장된다`
>
> → `캐시 무효화는 배포마다 전체를 비운다. 스테일 데이터를 막기 위해서다. 다만 운영에서는 비용이
> 크다. 버전 프리픽스로 부분만 비우는 편이 낫다.`

**Do not chop everything to one length.** Uniform short sentences are their own tell — generated
prose runs at one readability level while human writing is lumpy. Fix the sentences carrying more
than one claim; leave a long sentence that is genuinely one thought.

### 4.5 Line breaks

Three different things get called 줄바꿈. Fix them separately.

**Source line width.** [Semantic line breaks](https://sembr.org/) — one sentence per source line,
breaking after an independent clause, wrapping under 80 characters. A one-word change stays a
one-line diff instead of reflowing the paragraph. Worth doing on anything under version control.

> ⚠️ **Check the renderer first.** In a `.md` file a single newline joins with a space, so this is
> invisible in the output. In a GitHub issue or PR comment, in Notion, and in most chat renderers, a
> single newline **is** a line break, and applying sembr there reshapes the rendered document. The
> spec's own rule is that semantic line breaks must not alter rendered output — on those targets,
> obeying it means not doing this.

**Paragraph breaks.** Over ~300 characters with no blank line is a wall. Korean packs far more
meaning per character than an alphabetic script, so the same count is a much denser block — this
threshold is under half the English one. Break at the topic shift, not at a count.

The opposite failure is as common: every paragraph one sentence long, which is a list that forgot
its bullets. If consecutive one-sentence paragraphs are parallel, make them a list (4.6). If not,
join them.

**Rendered breaks.** Never use a trailing double-space — invisible in source, and most formatters
strip it. Use a blank line, or a list. `<br>` only inside a table cell, where nothing else works.

### 4.6 Lists and numbering

Both directions matter. The scanner reports a bullet ratio: **over ~60% is soup; under ~10% in a
procedural document usually means a buried list.**

**Prose → list** when the prose contains:

- An enumeration in sentence form — `첫째 … 둘째 … 셋째`, `먼저 … 다음으로 … 마지막으로`
- Three or more parallel items chained with `~하고`, `~며`, or commas
- Ordered steps buried in a paragraph → **numbered**, not bulleted
- Two or more things compared on the same axes → a **table**, not a list

**List → prose** when one idea needs explanation rather than segmentation (a bullet is not a
paragraph with a dot on it), when a list has exactly one item (that is a sentence), when items run
past ~200 characters, when adjacent items depend on each other (the dependency is the connective
that got dropped), or when the whole document is bullets — readers describe that as running an
obstacle course.

| Rule | Detail |
|---|---|
| Length | 2–7 items. Over 7, group under sub-headings or use a table |
| Nesting | Two levels. A third is an outline pretending to be a list |
| Order | Bulleted for unordered, numbered for sequence or priority — never numbered to look organized |
| Parallelism | Every item the same grammatical shape: all `~다`, all 명사형, or all `~음`. **Mixed endings inside one list is the most common slip** |
| Lead-in | A complete sentence, a fragment ending in a colon, or a heading — not a heading *and* a colon |
| Punctuation | Periods only if items are complete sentences. Never a trailing `,` `;` `그리고` `또는` |

### 4.7 Emoji and decoration

Screen readers speak each emoji's Unicode name aloud, so three in a row is three spoken phrases
dropped into a sentence.

| Use | Verdict |
|---|---|
| A legend defined once and used consistently (`🧩 플러그인 · 📄 스킬`) | Keep |
| A persistent status marker in a working document (`⚠️` on a known trap) | Keep, sparingly |
| Heading decoration | **Cut.** Every one |
| One per bullet as visual rhythm | **Cut** |
| Standing in for a word | **Cut.** It survives neither a screen reader nor a grep |

None in headings, none in a document being submitted or graded, never three in a row. If emoji carry
meaning they need a legend; if they need a legend and there is only one, it is decoration.

**Em dash (—)**: fine as a definition dash, but LLMs cluster them. Roughly one per 20 lines; convert
the rest to 쉼표 or 괄호. **Curly quotes** (`“ ”`): straighten them.

### 4.8 Bold

Blanket bold-stripping ruins technical documents. Classify first.

| Kind | Example | Action |
|---|---|---|
| **Sentence-level** — a clause with a 서술어 | `**이 설정은 운영 환경에서 쓰면 안 된다.**` | **Strip** |
| **Term / value** — a noun phrase, number, or label | `**512MB**`, `**타임아웃 3초**`, `**읽기 전용 모드**` | **Keep.** A scanning aid, not decoration |

Rule of thumb: if it has a 서술어, unbold it. If it is a thing, keep it. Budget: at most one
sentence-level emphasis per section. A document where every third line is bold has no emphasis at
all. A high term-level count is normal in technical writing.

### 4.9 Rules that do not apply to Korean

Do not spend effort here — and **do not invent Korean equivalents**:

- Title case in headings. Korean has no case
- Copula avoidance (`serves as`, `boasts`). The Korean analogue — `~로 자리매김한다`, `~을 자랑한다`
  — is already covered under inflated significance in 4.2
- The rule of three as a *word*-level pattern. In Korean it shows up at the list level, covered in 4.6

---

## 5. Procedure

1. **Scan** (section 3). Note which checks fired
2. **Read the whole file.** 어체 consistency and bullet ratio cannot be judged from a diff
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
before:  **캐시 무효화**: 배포 때마다 전체를 비운다. 키 전략은 **버전 프리픽스로** 바꿨다
after:   캐시 무효화**: 배포 때마다 전체를 비운다. 키 전략은 **버전 프리픽스로 바꿨다
```

The marker count stays even, so a balance check does not catch it — the bold silently moved to the
wrong words.

The same trap applies to every rule here. A global substitution for `~하며` hits 하며 inside a noun
and reaches into a quotation you were told not to touch. If you must batch, operate on one `**…**`
span at a time and skip any line with more than one. Better: targeted edits on the lines you
actually decided to change.

---

## 7. What the scanner gets wrong

- **Sentence splitting is punctuation-based.** A sentence ending in `다` with no period merges with
  the next one, so a document that omits terminal periods reports inflated lengths
- **The connective regex is verb-stem-anchored** (`하고`, `되며`, `는데`) because a bare `고`/`며`
  matches 참고, 사고, 명세. Past-tense forms are caught separately by their ㅆ 받침 (`했고`, `늘렸고`,
  `시켰고`), since the contraction lands on a different syllable each time and no stem list follows
  it. Only the `고` form needs stems at all: `지만`, `는데` and `으며` are listed bare, so 않지만 and
  없는데 were never the gap. The stem list stays short on purpose — a stem is added only when it
  cannot begin a noun, which rules out `알고` (알고리즘), `보고` (보고서), `가고` (국가고시), `맞고`
  (맞고소) and `주고` (주고받다). Sentences chained on those are caught by length alone or not at all
- **`, ` counts toward the clause total but cannot trigger the check on its own.** A sentence needs
  at least one real connective before the clause rule fires, so `A, B, C, D` reads as the list it is.
  The cost is that a genuinely long comma-spliced sentence is caught by its length alone or not at all
- **어체 detection reads sentence endings only.** 존댓말 inside a quotation counts; every `니다`
  except 아니다 is treated as 존댓말; and because 해요체 is caught by the bare `요` ending, a sentence
  that happens to end on a noun like 필요 or 중요 is miscounted as 존댓말
- **Bullet ratio counts lines, not ideas.** A file of one-line reference entries is legitimately 90%
  bullets — `CLAUDE.md` is the standard case
- **Parallelism is checked on the last character only.** It catches `~다` mixed with 명사형 and
  nothing subtler
- **Emoji ranges are approximate.** Arrows and `·` are excluded deliberately as technical
  punctuation, so a document decorating with `→` reports zero

---

## 8. Verification

Restructuring can drop content in a way that re-reading does not catch.

```bash
# Nothing left the document: fences, tables, headings unchanged in count
grep -cE '^\s*(`{3,}|~{3,})' FILE; grep -c '^|' FILE; grep -c '^#' FILE
# Values that must survive verbatim
grep -o '[0-9][0-9.]*\(ms\|초\|MB\|%\)' FILE | sort | uniq -c
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

It tracks delimiter parity across lines rather than grepping: bold wrapped onto the next line is
normal in prose, and a naive check reports every legitimate `**항목**: 설명` as damage.

---

## 9. Extra rules for graded or submitted documents

When a reviewer is judging the work:

- No emoji anywhere, including body text
- No first-person color (`제 생각에는`, `~인 것 같아요`). State the judgment and its basis
- Quotations from the spec stay verbatim, in quotes — never paraphrase a requirement
- Keep every number, log line, and reproduction command. **Density of evidence is the point**;
  trimming it to read smoothly defeats the document
- One 어체 throughout. Check the last paragraph against the first

---

## Credits

Sections 1, 2, 4.2, 4.8, 4.9 and 6 are a **derivative work**. The rest — the 어체 check (4.1), the
structural checks (4.4 through 4.7), the scanner, and the verification — is original.

| | |
|---|---|
| Adapted from | [`humanizer`](https://github.com/softaworks/agent-toolkit/tree/main/skills/humanizer) in softaworks/agent-toolkit — MIT |
| Original skill by | [@blader](https://github.com/blader/humanizer) |
| Underlying source | [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup |

What this changes from upstream: it drops the "inject personality" section (§2), splits the bold rule
into sentence-level and term-level instead of stripping all of it (4.8), adds the protected zones
(§1), replaces the English pattern list with Korean ones, names the upstream rules that have no
Korean equivalent so nobody invents one (4.9), and adds the structural half that upstream does not
address at all.

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
