#!/usr/bin/env python3
"""saramchae — readability and AI-tell triage for a markdown document, in any language.

Section 4 of SKILL.md says what each check means; section 7 says what each one gets wrong.
Every number here is a heuristic, not a verdict. A finding you cannot see in the line is a
false positive — drop it.

Sentence length is measured in words for alphabetic scripts and in characters for CJK, because
a CJK character carries roughly a word's worth of meaning and word-splitting on whitespace
under-counts it by an order of magnitude.
"""
import re, sys, pathlib, statistics, argparse, json, io, contextlib

CJK   = re.compile(r"[぀-ヿ㐀-䶿一-鿿가-힯]")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U0001F900-\U0001F9FF☀-⛿✀-➿]️?")
ABBR_NEVER = re.compile(r"\b(e\.g|i\.e|vs|cf|Mr|Dr|Fig|No|approx)\.$", re.I)
ABBR_MAYBE = re.compile(r"\b(etc|al)\.$", re.I)

VOCAB = ["delve", "leverage", "utilize", "foster", "embark", "robust", "seamless", "comprehensive",
         "moreover", "furthermore", "ultimately", "notably", "essentially", "crucial", "pivotal",
         "realm", "landscape", "underscore", "testament", "navigate", "synergy", "tapestry",
         "intricate", "multifaceted", "paradigm", "holistic", "streamline", "harness"]
HEDGE = ["might", "could", "perhaps", "possibly", "potentially", "arguably", "somewhat",
         "relatively", "fairly", "generally", "typically", "often", "may"]
NEGPAR = re.compile(r"\b(not (just|only|merely|simply)|isn't (just|only)|more than (just|simply))\b", re.I)
CHAT   = re.compile(r"\b(hope this helps|let me know if|feel free to|certainly!|great question|"
                    r"i'd be happy to|dive into|in conclusion|in summary|to sum up)\b", re.I)


def strip_noise(s):
    s = re.sub(r"`[^`]*`", "CODE", s)                  # inline code: a token, never deleted
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


def measure(sent):
    """(size, unit, warn) — CJK counts characters, alphabetic scripts count words."""
    if len(CJK.findall(sent)) > len(re.findall(r"[A-Za-z]", sent)) / 2:
        return len(sent), "chars", 90
    return len(sent.split()), "words", 25


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
    if lines and lines[0].strip() == "---":                       # frontmatter is exempt
        end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), 0)
        # Blanked, not sliced. Slicing renumbers everything below it, and every `L…` this prints
        # would then be short by the length of the header — pointing the reader at the wrong line.
        lines = [""] * (end + 1) + lines[end + 1:]
    lines = mask_regions(lines)
    units, paras, lists, headings, tbl, fenced = parse(lines)
    bullets = [u for u in units if u[1] == "bullet"]
    prose   = [u for u in units if u[1] == "prose"]
    chunks  = [(p[0][0], " ".join(u[2] for u in p)) for p in paras] + [(u[0], u[2]) for u in bullets]
    # Inline code is stripped before the vocabulary checks: a document listing `delve` as a word to
    # avoid otherwise reports itself. This skill's own section 4.1 is exactly that shape.
    text    = re.sub(r"`[^`]*`", " ", "\n".join(u[2] for u in units))
    low     = text.lower()
    print(f"== {path}")

    # [1] voice
    vocab = [(w, low.count(w)) for w in VOCAB if w in low]
    # Same reason as `text` above: these run on code-stripped chunks so a document quoting
    # "not just X, but Y" as the pattern to avoid does not report itself.
    bare  = [(i, re.sub(r"`[^`]*`", " ", t)) for i, t in chunks]
    negp  = [i for i, t in bare if NEGPAR.search(t)]
    chat  = [i for i, t in bare if CHAT.search(t)]
    hedgy = []
    for i, t in bare:
        for sent in split_sentences(strip_noise(t)):
            if sum(1 for h in HEDGE if re.search(rf"\b{h}\b", sent, re.I)) >= 2:
                hedgy.append((i, sent[:50]))
    print(f"\n[1] voice: flagged words {sum(n for _, n in vocab)}, negative parallelism {len(negp)},"
          f" stacked hedges {len(hedgy)}, chat residue {len(chat)}")
    if vocab: print("    " + ", ".join(f"{w}×{n}" for w, n in sorted(vocab, key=lambda x: -x[1])[:10]))
    for i, s in hedgy[:4]: print(f"    L{i}  {s}…")
    if chat: print(f"    chat residue at L{chat[:6]}")

    # [2] sentence length
    long_s, sizes = [], []
    for i, t in chunks:
        for sent in split_sentences(strip_noise(t)):
            n, unit, warn = measure(sent)
            sizes.append(n)
            conn = len(re.findall(r"\b(and|but|which|while|because|so that)\b", sent, re.I))
            c = conn + sent.count(", ")
            # Clause count alone does not convict: a short sentence listing three terms has three
            # commas. Requiring one real conjunction is what separates a chained sentence from a
            # list written inline.
            if n > warn or (c >= 3 and conn >= 1 and n > warn * 0.6):
                long_s.append((i, n, unit, c, sent[:52]))
    spread = f"median {int(statistics.median(sizes))}, p90 {int(statistics.quantiles(sizes, n=10)[8])}" \
             if len(sizes) > 9 else f"n={len(sizes)}"
    print(f"\n[2] sentence length: {len(long_s)} long ({spread})")
    for i, n, u, c, t in sorted(long_s, key=lambda x: -x[1])[:8]:
        print(f"    L{i}  {n} {u} / {c} clauses  {t}…")

    # [3] line breaks
    ok     = lambda i: i not in tbl and not fenced[i - 1]   # a wrapped code line is not a wrap fault
    widths = [len(l) for i, l in enumerate(lines, 1) if l.strip() and ok(i)]
    over   = [i for i, l in enumerate(lines, 1) if len(l) > 120 and ok(i)]
    walls  = [(p[0][0], t) for p in paras for t in [sum(len(u[2]) for u in p)]
              if t > (300 if CJK.search(" ".join(u[2] for u in p)) else 700)]
    # `<br>` inside a table cell is the one place the skill permits it, so tables are exempt here
    # as well as fenced blocks.
    hard   = [i for i, l in enumerate(lines, 1)
              if ok(i) and (l.endswith("  ") or "<br" in re.sub(r"`[^`]*`", "", l))]
    p90 = int(statistics.quantiles(widths, n=10)[8]) if len(widths) > 9 else max(widths or [0])
    print(f"\n[3] line breaks: p90 width {p90}, over 120 {len(over)}, walls {len(walls)}, hard breaks {len(hard)}")
    for i, n in walls[:5]: print(f"    L{i}  {n}-char paragraph with no blank line")

    # [4] lists
    body = len(prose) + len(bullets)
    deep = [u[0] for u in bullets if u[3] >= 2]
    orph = [g[0][0] for g in lists if len(g) == 1]
    big  = [g[0][0] for g in lists if len(g) > 7]
    fat  = [u[0] for u in bullets if len(u[2]) > 200]
    enum = [u[0] for u in prose
            if len(re.findall(r"\b(first|second|third|finally|next),", u[2], re.I)) >= 2]
    print(f"\n[4] lists: bullet ratio {len(bullets)/body if body else 0:.0%} ({len(bullets)}/{body}),"
          f" depth>=3 {len(deep)}, orphan {len(orph)}, >7 items {len(big)}, fat items {len(fat)}")
    if enum: print(f"    prose that reads as a list: L{enum[:6]}")
    if orph: print(f"    one-item lists: L{orph[:6]}")

    # [5] emoji and decoration
    # Tables are excluded here for the same reason as everywhere else: a ✓ in a comparison table is
    # data, not decoration. Section 1 protects the table and every other check already used ok().
    em    = [(i, EMOJI.findall(l)) for i, l in enumerate(lines, 1) if EMOJI.search(l) and ok(i)]
    inh   = [i for i, s in headings if EMOJI.search(s)]
    runs  = [i for i, e in em if len(e) >= 3]
    dash  = sum(l.count("—") for i, l in enumerate(lines, 1) if ok(i))
    curly = sum(l.count("“") + l.count("”") for i, l in enumerate(lines, 1) if ok(i))
    print(f"\n[5] emoji {sum(len(e) for _, e in em)} on {len(em)} lines, in headings {len(inh)},"
          f" runs of 3+ {len(runs)}, em dash {dash}, curly quotes {curly}")
    if inh: print(f"    headings with emoji: L{inh[:6]}")

    # [6] bold — sentence-level goes, term-level stays
    SENT = re.compile(r"[.!?]$")
    sl = tl = 0
    for i, l in enumerate(lines, 1):
        if i in tbl or fenced[i - 1]: continue
        for m in re.findall(r"\*\*(.+?)\*\*", l):
            if SENT.search(m.strip()) or len(m.split()) > 6: sl += 1
            else: tl += 1
    print(f"\n[6] bold: sentence-level {sl} / term-level {tl}  (only sentence-level comes out)")

    # [7] headings
    tc = []
    for i, s in headings:
        words = [w for w in re.sub(r"[#*`]", "", s).split() if len(w) > 3 and w.isalpha()]
        if len(words) >= 3 and sum(w[0].isupper() for w in words) / len(words) > 0.6:
            tc.append(i)
    dense = len(headings) > len(lines) / 12          # roughly one heading per 12 lines
    print(f"\n[7] headings: {len(headings)} over {len(lines)} lines, title-cased {len(tc)}"
          + (" — heading-heavy for the length" if dense else ""))
    if tc: print(f"    title case at L{tc[:6]}")

    # The same numbers the report above printed, for --json and --fail-over. Counts that describe
    # the document rather than fault it — bullet ratio, em dash, curly quotes, term-level bold —
    # are reported but stay out of `total`.
    return {
        "file": path,
        "checks": {
            "voice":       {"flagged_words": sum(n for _, n in vocab),
                            "negative_parallelism": len(negp),
                            "stacked_hedges": len(hedgy), "chat_residue": len(chat)},
            "sentences":   {"long": len(long_s), "lines": [i for i, *_ in long_s]},
            "line_breaks": {"p90_width": p90, "over_120": len(over),
                            "walls": len(walls), "hard_breaks": len(hard)},
            "lists":       {"bullet_ratio": round(len(bullets) / body, 3) if body else 0,
                            "deep": len(deep), "orphan": len(orph), "over_7": len(big),
                            "fat": len(fat), "prose_as_list": len(enum)},
            "decoration":  {"emoji": sum(len(e) for _, e in em), "in_headings": len(inh),
                            "runs_of_3": len(runs), "em_dash": dash, "curly_quotes": curly},
            "bold":        {"sentence_level": sl, "term_level": tl},
            "headings":    {"count": len(headings), "title_cased": len(tc), "dense": dense},
        },
        "total": (sum(n for _, n in vocab) + len(negp) + len(hedgy) + len(chat)
                  + len(long_s) + len(over) + len(walls) + len(hard)
                  + len(deep) + len(orph) + len(big) + len(fat) + len(enum)
                  + len(inh) + len(runs) + sl + len(tc)),
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
        description="Voice and structure triage for markdown. Reports; never edits.")
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
