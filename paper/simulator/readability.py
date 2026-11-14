"""Reading indices for Appendix B (course rule 6).

Usage:  python3 readability.py ../main.pdf ../main.toc ../data/readability.tex [old.pdf]

Extracts the running prose of the compiled report (paragraphs of at least
25 words; figure labels, table cells, code and captions are mostly dropped
by that filter), and computes the five grade-level indices listed at
https://www.analyzemywriting.com/readability_indices.html with the standard
formulas implemented by the `textstat` package, plus Flesch Reading Ease and
the inputs to the graphical Fry and Raygor estimates.
"""
import re, statistics, subprocess, sys
import textstat


def page_text(pdf, first, last):
    out = subprocess.run(["pdftotext", "-f", str(first), "-l", str(last), pdf, "-"],
                         capture_output=True, text=True).stdout
    out = re.sub(r"-\n(?=[a-z])", "", out)          # re-join hyphenated words
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", out)]
    keep = []
    for p in paras:
        words = p.split()
        if len(words) < 25 or "." not in p:
            continue
        alpha = sum(c.isalpha() for c in p) / max(1, len(p))
        if alpha < 0.72:                              # tables, numbers, code
            continue
        keep.append(p)
    return "\n\n".join(keep)


def arabic_offset(pdf):
    """PDF page number of arabic page 1 (the first page of Chapter 1)."""
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf],
            capture_output=True, text=True).stdout).group(1))
    for i in range(1, n + 1):
        t = subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), pdf, "-"],
                           capture_output=True, text=True).stdout
        if re.search(r"Chapter\s+1\s*\n\s*Introduction", t):
            return i
    raise SystemExit("Chapter 1 not found")


def parts_from_toc(toc):
    s = open(toc).read()
    rows = re.findall(r"\\contentsline \{(part|chapter)\}\{(.*?)\}\{([0-9ivx]+)\}", s)
    parts, appendix_page = [], None
    for kind, title, page in rows:
        if kind == "part":
            name = re.sub(r"\\hspace \{1em\}", " ", title)
            parts.append([name.split(" ")[0], int(page)])
        if "Plagiarism Report" in title:
            appendix_page = int(page)
    return parts, appendix_page


def indices(text):
    words = textstat.lexicon_count(text)
    sents = textstat.sentence_count(text)
    sylls = textstat.syllable_count(text)
    long_words = sum(1 for w in re.findall(r"[A-Za-z]+", text) if len(w) >= 6)
    grade = {
        "fog": textstat.gunning_fog(text),
        "fk": textstat.flesch_kincaid_grade(text),
        "smog": textstat.smog_index(text),
        "cl": textstat.coleman_liau_index(text),
        "ari": textstat.automated_readability_index(text),
    }
    vals = list(grade.values())
    return dict(words=words, sents=sents, wps=words / sents,
                fre=textstat.flesch_reading_ease(text),
                mean=statistics.mean(vals), median=statistics.median(vals),
                fry_s=100 * sents / words, fry_y=100 * sylls / words,
                ray_s=100 * sents / words, ray_l=100 * long_words / words, **grade)


def main():
    pdf, toc, out = sys.argv[1:4]
    old = sys.argv[4] if len(sys.argv) > 4 else None
    off = arabic_offset(pdf) - 1
    parts, app = parts_from_toc(toc)
    spans = [("Ch.~1", 1, parts[0][1] - 1)]
    for k, (name, p) in enumerate(parts):
        end = parts[k + 1][1] - 1 if k + 1 < len(parts) else app - 1
        spans.append((f"Part {name}", p, end))
    rows = []
    for name, a, b in spans:
        rows.append((name, indices(page_text(pdf, a + off, b + off))))
    whole = indices(page_text(pdf, 1 + off, app - 1 + off))
    rows.append(("Whole report", whole))
    if old:
        o_off = arabic_offset(old) - 1
        rows.append(("v1.0, whole", indices(page_text(old, 1 + o_off, int(sys.argv[5]) + o_off))))

    L = []
    L.append(r"""Rule~6 of the course asks for reading indices. The five numeric indices below are
the ones described by the reference the course gives,
\url{https://www.analyzemywriting.com/readability_indices.html}: the Gunning fog
index, the Flesch--Kincaid grade level, the SMOG index, the Coleman--Liau index and
the Automated Readability Index (ARI). Each estimates the United States school grade
needed to read the text: 8 to 12 suits a general adult reader, and scholarly or
technical writing usually scores above 12. As on that site, we also give the mean
and median of the five, and the Flesch Reading Ease score (0--100, higher is
easier). The Fry and Raygor estimates are read off graphs, so we give their inputs.

The indices were computed with the \texttt{textstat} Python package on the running
prose of the compiled report: every paragraph of at least 25 words, taken from the
PDF of this version. Tables, figure labels, code and short captions are left out,
since sentence-based formulas give meaningless values on them. Syllables are
estimated from spelling, so the values can differ slightly from those of the web
tool. The script is \texttt{simulator/readability.py} and can be rerun on any build.
The last row applies the same procedure to the previous version (v1.0) of the
report, for comparison.

\begin{table}[htbp]
\centering
\caption{Reading indices of the prose of each Part (grade levels, except Flesch
Reading Ease).}
\label{tab:readability}
\small
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}l r r r r r r r r r r@{}}
\toprule
 & Words & Words/ & Fog & F--K & SMOG & C--L & ARI & Mean & Median & Flesch \\
 & & sentence & & & & & & grade & grade & ease \\
\midrule""")
    for name, r in rows:
        if name == "Whole report" or name.startswith("v1.0"):
            L.append(r"\midrule")
        L.append(f"{name} & {r['words']:,} & {r['wps']:.1f} & {r['fog']:.1f} & {r['fk']:.1f} & "
                 f"{r['smog']:.1f} & {r['cl']:.1f} & {r['ari']:.1f} & {r['mean']:.1f} & "
                 f"{r['median']:.1f} & {r['fre']:.1f} \\\\")
    L.append(r"""\bottomrule
\end{tabular}
\end{table}
""")
    w = whole
    band = ("a general adult reader" if w["mean"] < 12 else "a university reader")
    L.append(f"""For the whole report the five grade levels range from {min(w['fog'],w['fk'],w['smog'],w['cl'],w['ari']):.1f}
to {max(w['fog'],w['fk'],w['smog'],w['cl'],w['ari']):.1f}, with a mean of {w['mean']:.1f}, which these measures rate as suitable for {band}.
The formulas count syllables and word lengths, so the many short technical terms of
this report (MESI, MOESI, DSR, LLC, AMAT) count as easy words; the indices therefore
understate how hard the text is for a reader new to the subject. The inputs to the
Fry graph are {w['fry_s']:.1f} sentences and {w['fry_y']:.0f} syllables per 100 words, and the inputs to the
Raygor graph are {w['ray_s']:.1f} sentences and {w['ray_l']:.0f} words of six or more letters per 100 words;
these are the coordinates at which the report would be plotted on each graph.
""")
    open(out, "w").write("\n".join(L))
    for name, r in rows:
        print(name, {k: round(v, 1) if isinstance(v, float) else v for k, v in r.items()})


if __name__ == "__main__":
    main()
