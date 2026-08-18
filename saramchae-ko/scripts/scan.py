#!/usr/bin/env python3
"""saramchae-ko — voice and structure triage for a Korean markdown document.

Section 4 of SKILL.md says what each check means; section 7 says what each one gets wrong.
Every number here is a heuristic, not a verdict. A finding you cannot see in the line is a
false positive — drop it.
"""
import re, sys, pathlib, statistics, argparse, json, io, contextlib

HANGUL = re.compile(r"[가-힣]")
EMOJI  = re.compile("[\U0001F300-\U0001FAFF\U0001F900-\U0001F9FF☀-⛿✀-➿]️?")
# Verb-stem-anchored on purpose: a bare 고/며 matches nouns like 참고, 사고, 명세 and the count
# stops being usable.
ABBR_NEVER = re.compile(r"\b(e\.g|i\.e|vs|cf|Mr|Dr|Fig|No|approx)\.$", re.I)
ABBR_MAYBE = re.compile(r"\b(etc|al)\.$", re.I)
CONN = re.compile(r"(하고|되고|이고|지고|않고|없고|같고|많고|좋고|넣고|놓고|쓰고|만들고|찾고"
                  r"|하며|되며|이며|으며|면서|는데|은데|인데|지만|거나|하여|되어|아서|어서)\s")
# Only the `고` form needs a stem list. `지만`, `는데`, `으며` are already listed bare, so 않지만,
# 없는데 and 같으며 were never the gap. The stems above were picked by testing each against real
# compounds and rejecting every one that lives inside a noun: 알고 loses to 알고리즘, 보고 to
# 보고서, 가고 to 국가고시, 맞고 to 맞고소, 주고 to 주고받다. What is left cannot start a noun.
# Past-tense connectives surface as a syllable carrying the ㅆ 받침: 했고, 됐고, 봤고, 늘렸고,
# 시켰고. Listing stems cannot follow them because the contraction lands on a different syllable
# every time, so match the 받침 instead — jongseong index 20 in the precomposed Hangul block.
# Without this a fully chained sentence reported `0 clauses`, which is the one number this check
# exists to produce.
_SS = "".join(chr(0xAC00 + c * 588 + v * 28 + 20) for c in range(19) for v in range(21))
CONN_PAST = re.compile(f"[{_SS}](고|으며|지만|는데|어서|으니)\\s")
# Check 존댓말 first: 습니다/입니다 also end in 다, so the reverse order leaks all of them into 평서체.
# `[가-힣]요` covers 해요체 wholesale — 해요, 돼요, 세요, 어요, 지요. Listing the endings one by one
# missed 해요/돼요 entirely, and a 해요체 document then matched neither pattern and vanished from
# both totals, so a mixed document was reported as consistent.
# One `니다` catches the rest. A literal `ㅂ니다` never matches 줍니다/둡니다: that ㅂ is a 받침 living
# inside a precomposed syllable, not the standalone jamo ㅂ (U+3142). 아니다 is the one 평서체 exception.
JONDAE = re.compile(r"((?<!아)니다|십시오|[가-힣]요|죠)[.!?。！？]?$")
PYEONG = re.compile(r"(는다|ㄴ다|이다|한다|된다|았다|었다|겠다|없다|있다|같다|아니다|다)[.!?。！？]?$")

TRANSLATIONESE = {
    "~에 있어": r"에 있어", "~을 통해": r"[을를] 통해", "~하는 데 있어": r"하는 데 있어",
    "~의 경우": r"의 경우", "~라고 할 수 있": r"라고 할 수 있", "~로 볼 수 있": r"로 볼 수 있",
    "~을 진행": r"[을를] 진행", "~을 수행": r"[을를] 수행", "결론적으로": r"결론적으로",
    "요약하면": r"요약하면", "단순히 ~가 아니라": r"단순히 .{0,20}가 아니라",
}
HANJA = {"활용": "쓰다", "수행": "한다", "진행": "한다", "상이": "다르다", "소요": "걸린다",
         "기입": "적는다", "용이": "쉽다", "제반": "(삭제)", "도모": "높인다", "극대화": "높인다"}
CHAT = ["도움이 되셨", "궁금한 점이", "해보시기 바랍", "물론입니다", "살펴보겠습니다"]


def strip_noise(s):
    s = re.sub(r"`[^`]*`", "CODE", s)                 # inline code: a token, never deleted
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)  # links: keep the text, drop the URL


def split_sentences(text):
    parts = re.split(r"(?<=[.!?。！？])(\s+)", text)
    out, buf = [], ""
    for k, tok in enumerate(parts):
        if not tok.isspace(): buf += tok; continue
        nxt = parts[k + 1] if k + 1 < len(parts) else ""
        stem = buf.strip()
        # `e.g.` never ends a sentence, so it always joins. `etc.` and `al.` genuinely can, so they
        # join only when what follows looks like a continuation — a lowercase letter. Hangul is
        # caseless, so a Korean word after `etc.` correctly reads as a new sentence.
        if ABBR_NEVER.search(stem) or (ABBR_MAYBE.search(stem) and nxt[:1].islower()):
            buf += tok; continue
        out.append(stem); buf = ""
    if buf.strip(): out.append(buf.strip())
    return [s for s in out if s]


def is_ko(s):
    return len(HANGUL.findall(s)) > len(re.findall(r"[A-Za-z]", s)) / 2


FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")
# A GFM separator row. The table it belongs to may be written without leading or trailing pipes,
# so the separator — not a leading `|` — is what actually identifies a table.
SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")


def fence_mask(lines):
    """True for every line inside (or opening/closing) a fenced block.

    Follows CommonMark closely enough to survive a document that documents markdown, which these
    skills are: the opening run's character *and length* are both kept, and a fence closes only on
    a run of the same character at least as long with nothing but spaces after it. Keeping only the
    character would let a ``` example inside a ```` block close it, and would let a line like
    ```foo — which is content, not a close — end the block early.
    """
    mask, opener, width = [False] * len(lines), None, 0
    for i, l in enumerate(lines):
        m = FENCE.match(l)
        if m:
            run, rest = m.group(1), m.group(2)
            if opener is None:
                opener, width = run[0], len(run); mask[i] = True; continue
            if run[0] == opener and len(run) >= width and not rest.strip():
                opener = None; mask[i] = True; continue
        mask[i] = opener is not None
    return mask


def table_rows(lines, fenced):
    """1-based line numbers belonging to a table, including the pipe-less `A | B` form."""
    rows = set()
    for i, l in enumerate(lines):
        if fenced[i] or not SEP.match(l) or i == 0: continue
        if "|" not in lines[i - 1] or fenced[i - 1]: continue      # header row must sit above
        rows.add(i); rows.add(i + 1)                               # header, then the separator
        for j in range(i + 1, len(lines)):
            if fenced[j] or "|" not in lines[j]: break
            rows.add(j + 1)
    return rows


def parse(lines):
    """(units, paras, lists, headings, table_lines, fence_mask), with wrapped continuations folded in —
    measuring a sentence per source line is wrong the moment a file is hard-wrapped."""
    units, paras, lists, headings, tbl = [], [], [], [], set()
    para, cur, last = [], [], None
    fenced = fence_mask(lines)
    tbl |= table_rows(lines, fenced)

    def flush():
        nonlocal para, cur
        if para: paras.append(para); para = []
        if cur: lists.append(cur); cur = []

    for i, l in enumerate(lines, 1):
        if fenced[i - 1]: continue
        s = l.strip()
        if not s: flush(); last = None; continue
        if i in tbl or s.startswith("|"): tbl.add(i); continue
        if s.startswith(">"): s = s.lstrip("> ")
        if s.startswith("#"): headings.append((i, s)); flush(); last = None; continue
        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)", l)
        if m:
            if para: paras.append(para); para = []
            u = [i, "bullet", m.group(3), len(m.group(1)) // 2]
            units.append(u); cur.append(u); last = u; continue
        if last and l[:1].isspace(): last[2] += " " + s; continue   # wrapped continuation
        if cur: lists.append(cur); cur = []
        u = [i, "prose", s, 0]
        units.append(u); para.append(u); last = u
    flush()
    return units, paras, lists, headings, tbl, fenced


def mask_regions(lines):
    """Blank the lines between `<!-- saramchae:off -->` and `<!-- saramchae:on -->`.

    Section 1 protects quotations, and a document *about* bad prose is full of it: a style guide,
    a changelog quoting a bug report, a before/after specimen. Without this the document reports
    itself and the reader cannot tell a real finding from a quoted one. Blanked rather than sliced,
    so every `L…` this prints still points at the right line.
    """
    out, off, fence = list(lines), False, False
    for i, l in enumerate(out):
        s = l.strip()
        # A marker shown inside a code fence is documentation of the marker, not a marker. This
        # file's own README demonstrates the syntax that way and would otherwise mask itself.
        if s.startswith("```") or s.startswith("~~~"):
            fence = not fence
        elif not fence:
            if s.startswith("<!-- saramchae:off"):
                off = True
            elif s.startswith("<!-- saramchae:on"):
                off, out[i] = False, ""
                continue
        if off:                       # a fence *inside* a marked region is masked with the rest
            out[i] = ""
    return out


def main(path):
    lines = pathlib.Path(path).read_text().splitlines()
    if lines and lines[0].strip() == "---":                        # frontmatter is exempt
        end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), 0)
        # Blanked, not sliced. Slicing renumbers everything below it, and every `L…` this prints
        # would then be short by the length of the header — pointing the reader at the wrong line.
        lines = [""] * (end + 1) + lines[end + 1:]
    lines = mask_regions(lines)
    units, paras, lists, headings, tbl, fenced = parse(lines)
    bullets = [u for u in units if u[1] == "bullet"]
    prose   = [u for u in units if u[1] == "prose"]
    chunks  = [(p[0][0], " ".join(u[2] for u in p)) for p in paras] + [(u[0], u[2]) for u in bullets]
    print(f"== {path}")

    # [1] register mixing — the most common Korean-specific tell
    jon, pyeong = [], []
    for i, text in chunks:
        for sent in split_sentences(strip_noise(text)):
            if not is_ko(sent): continue
            if   JONDAE.search(sent): jon.append((i, sent[-14:]))
            elif PYEONG.search(sent): pyeong.append((i, sent[-14:]))
    total = len(jon) + len(pyeong)
    if total:
        minor, name = (jon, "존댓말") if len(jon) <= len(pyeong) else (pyeong, "평서체")
        pct = len(minor) / total
        print(f"\n[1] register: 평서체 {len(pyeong)} / 존댓말 {len(jon)}"
              + (f"  — mixed. minority {name}, {len(minor)} of them ({pct:.0%})" if minor else "  — consistent"))
        for i, t in minor[:8]: print(f"    L{i}  …{t}")
    else:
        print("\n[1] register: no Korean sentence to judge")

    # [2] translationese, 한자어, chat residue
    # Inline code is stripped: a document listing 도움이 되셨길 as a phrase to avoid otherwise
    # reports itself. This skill's own section 4.2 is exactly that shape.
    text = re.sub(r"`[^`]*`", " ", "\n".join(u[2] for u in units))
    tr = [(k, len(re.findall(v, text))) for k, v in TRANSLATIONESE.items() if re.search(v, text)]
    hj = [(k, len(re.findall(k + r"(하|한|되|된|합|됩)", text))) for k in HANJA
          if re.search(k + r"(하|한|되|된|합|됩)", text)]
    ch = [c for c in CHAT if c in text]
    print(f"\n[2] translationese {sum(n for _, n in tr)}, 한자어 {sum(n for _, n in hj)}, chat residue {len(ch)}")
    if tr: print("    translationese: " + ", ".join(f"{k}×{n}" for k, n in sorted(tr, key=lambda x: -x[1])[:8]))
    if hj: print("    한자어: " + ", ".join(f"{k}→{HANJA[k]}×{n}" for k, n in sorted(hj, key=lambda x: -x[1])[:8]))
    if ch: print("    chat residue: " + ", ".join(ch))

    # [3] sentence length — in Korean the clause count matters more than the character count
    long_s, sizes = [], []
    for i, t in chunks:
        for sent in split_sentences(strip_noise(t)):
            n = len(sent) if is_ko(sent) else len(sent.split())
            warn = 90 if is_ko(sent) else 25
            sizes.append(n)
            conn = len(CONN.findall(sent + " ")) + len(CONN_PAST.findall(sent + " "))
            c = conn + sent.count(", ")
            # A clause count alone does not convict: `A, B, C — delete` is a short sentence with three
            # commas. Requiring one real connective is what separates a chained sentence from a list
            # written inline; without it a quarter of this check's findings were plain enumerations.
            if n > warn or (c >= 3 and conn >= 1 and n > warn * 0.6):
                long_s.append((i, n, "자" if is_ko(sent) else "w", c, sent[:52]))
    spread = f"median {int(statistics.median(sizes))}, p90 {int(statistics.quantiles(sizes, n=10)[8])}" \
             if len(sizes) > 9 else f"n={len(sizes)}"
    print(f"\n[3] long sentences: {len(long_s)} ({spread})")
    for i, n, u, c, t in sorted(long_s, key=lambda x: -x[1])[:8]:
        print(f"    L{i}  {n}{u} / {c} clauses  {t}…")

    # [4] line breaks
    ok     = lambda i: i not in tbl and not fenced[i - 1]   # a wrapped code line is not a wrap fault
    widths = [len(l) for i, l in enumerate(lines, 1) if l.strip() and ok(i)]
    over   = [i for i, l in enumerate(lines, 1) if len(l) > 120 and ok(i)]
    walls  = [(p[0][0], t) for p in paras for t in [sum(len(u[2]) for u in p)] if t > 300]
    # `<br>` inside a table cell is the one place the skill permits it, so tables are exempt here
    # as well as fenced blocks.
    hard   = [i for i, l in enumerate(lines, 1)
              if ok(i) and (l.endswith("  ") or "<br" in re.sub(r"`[^`]*`", "", l))]
    p90 = int(statistics.quantiles(widths, n=10)[8]) if len(widths) > 9 else max(widths or [0])
    print(f"\n[4] line breaks: p90 width {p90}, over 120 {len(over)}, walls {len(walls)}, hard breaks {len(hard)}")
    for i, n in walls[:5]: print(f"    L{i}  {n}-char paragraph with no blank line")

    # [5] lists and numbering
    body  = len(prose) + len(bullets)
    deep  = [u[0] for u in bullets if u[3] >= 2]
    orph  = [g[0][0] for g in lists if len(g) == 1]
    big   = [g[0][0] for g in lists if len(g) > 7]
    fat   = [u[0] for u in bullets if len(u[2]) > 200]
    enum  = [u[0] for u in prose if len(re.findall(r"첫째|둘째|셋째|먼저,|다음으로,|마지막으로,", u[2])) >= 2]
    mixed = [g[0][0] for g in lists
             if len(g) > 2 and len({bool(re.search(r"(다|요|음|함)\.?$", u[2])) for u in g}) > 1]
    print(f"\n[5] lists: bullet ratio {len(bullets)/body if body else 0:.0%} ({len(bullets)}/{body}),"
          f" depth>=3 {len(deep)}, orphan {len(orph)}, >7 items {len(big)}, fat {len(fat)}, mixed endings {len(mixed)}")
    if enum: print(f"    prose that reads as a list: L{enum[:6]}")
    if orph: print(f"    one-item lists: L{orph[:6]}")

    # [6] emoji and decoration
    # Tables are excluded here for the same reason as everywhere else: a ✓ in a comparison table is
    # data, not decoration. Section 1 protects the table and every other check already used ok().
    em   = [(i, EMOJI.findall(l)) for i, l in enumerate(lines, 1) if EMOJI.search(l) and ok(i)]
    head = [i for i, s in headings if EMOJI.search(s)]
    dash = sum(l.count("—") for i, l in enumerate(lines, 1) if ok(i))
    curly = sum(l.count("“") + l.count("”") for i, l in enumerate(lines, 1) if ok(i))
    print(f"\n[6] emoji {sum(len(e) for _, e in em)} on {len(em)} lines, in headings {len(head)},"
          f" em dash {dash}, curly quotes {curly}")
    if head: print(f"    headings with emoji: L{head[:6]}")

    # [7] bold — sentence-level goes, term-level stays
    SENT = re.compile(r"[.!?]$|다$")
    sl = tl = 0
    for i, l in enumerate(lines, 1):
        if i in tbl or fenced[i - 1]: continue
        for m in re.findall(r"\*\*(.+?)\*\*", l):
            if SENT.search(m.strip()) or len(m) > 25: sl += 1
            else: tl += 1
    print(f"\n[7] bold: sentence-level {sl} / term-level {tl}  (only sentence-level comes out)")

    # The same numbers the report above printed, for --json and --fail-over. Counts that describe
    # the document rather than fault it — bullet ratio, em dash, curly quotes, term-level bold —
    # are reported but stay out of `total`.
    return {
        "file": path,
        "checks": {
            "register":       {"평서체": len(pyeong), "존댓말": len(jon),
                               "minority": min(len(jon), len(pyeong))},
            "translationese": {"translationese": sum(n for _, n in tr),
                               "한자어": sum(n for _, n in hj), "chat_residue": len(ch)},
            "sentences":      {"long": len(long_s), "lines": [i for i, *_ in long_s]},
            "line_breaks":    {"p90_width": p90, "over_120": len(over),
                               "walls": len(walls), "hard_breaks": len(hard)},
            "lists":          {"bullet_ratio": round(len(bullets) / body, 3) if body else 0,
                               "deep": len(deep), "orphan": len(orph), "over_7": len(big),
                               "fat": len(fat), "mixed_endings": len(mixed),
                               "prose_as_list": len(enum)},
            "decoration":     {"emoji": sum(len(e) for _, e in em), "in_headings": len(head),
                               "em_dash": dash, "curly_quotes": curly},
            "bold":           {"sentence_level": sl, "term_level": tl},
        },
        "total": (min(len(jon), len(pyeong))
                  + sum(n for _, n in tr) + sum(n for _, n in hj) + len(ch)
                  + len(long_s) + len(over) + len(walls) + len(hard)
                  + len(deep) + len(orph) + len(big) + len(fat) + len(mixed) + len(enum)
                  + len(head) + sl),
    }


def collect(paths):
    """Expand file and directory arguments into the markdown files to scan."""
    out = []
    for p in paths:
        q = pathlib.Path(p)
        if q.is_dir():
            out += sorted(q.rglob("*.md"))
        elif q.exists():
            out.append(q)
        else:
            sys.exit(f"scan.py: no such file or directory: {p}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        prog="scan.py",
        description="Voice and structure triage for Korean markdown. Reports; never edits.")
    ap.add_argument("paths", nargs="+", metavar="FILE",
                    help="files or directories to scan (directories are searched for *.md)")
    ap.add_argument("--json", action="store_true",
                    help="emit the counts as JSON instead of the readable report")
    ap.add_argument("--fail-over", type=int, metavar="N", default=None,
                    help="exit 1 when any file's finding total exceeds N, for use as a CI gate")
    args = ap.parse_args()

    files = collect(args.paths)
    if not files:
        sys.exit("scan.py: nothing to scan")

    records = []
    for f in files:
        try:
            if args.json:
                # The report is built by printing, so run it into a buffer and keep only the record.
                with contextlib.redirect_stdout(io.StringIO()):
                    records.append(main(str(f)))
            else:
                if records: print()
                records.append(main(str(f)))
        except UnicodeDecodeError:
            # One unreadable file must not end a directory sweep, which is the whole point of
            # accepting a directory. Say which file and carry on.
            print(f"scan.py: skipped, not UTF-8 text: {f}", file=sys.stderr)

    if not records:
        sys.exit("scan.py: nothing could be read")

    if args.json:
        out = records if len(records) > 1 else records[0]
        print(json.dumps(out, ensure_ascii=False, indent=2))

    if args.fail_over is not None and max(r["total"] for r in records) > args.fail_over:
        sys.exit(1)
