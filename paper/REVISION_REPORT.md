# ELL305 Term Paper: v2.0 revision report

v1.0 (163 pages) is kept unchanged. v2.0 is a separate copy of the project.

## 1. Page-count comparison

| Block | v1.0 pages | v2.0 pages |
|---|---|---|
| Front matter (title, copyright, acknowledgements, abstract, ToC, LoF, LoT) | 12 (no copyright or acknowledgements page) | 13 |
| Ch1 + Part I (Ch1–6) | 28 | 19 |
| Part II (Ch7–10) | 17 | 12 |
| Part III (Ch11–14) | 26 | 18 |
| Part IV (Ch15–16) | 26 | 16 |
| Part V (Ch17–18) | 19 | 10 |
| Part VI (Ch19–20) | 18 | 12 |
| Part VII (Ch21–22) | 10 | 6 |
| Appendices, glossary, bibliography, index | 7 | 13 |
| **Total PDF pages** | **163** | **119** |

Running prose (paragraphs of 25+ words, measured from the PDFs): v1.0 29,300 words; v2.0 21,800 words.
The rest of the drop comes from compacting the layout (chapters no longer always start a new page,
smaller mind maps, tighter float spacing), not from smaller fonts, margins or line spacing.
Geometry, 11pt font and single spacing are unchanged.

**Why not 105:** the remaining length is almost all figures, tables and mind maps that the professor
asked for (state diagrams, message-log tables, AMAT/NoC graphs, a mind map before every topic) or
that hold results. Reaching 105 would mean deleting about 14 pages of them. The professor's form says
"approximately 150 pages / 35000 words". v2.0 is now below that page figure, so the team should decide
whether the professor's figure or the 105 target matters more before cutting further.

## 2. Chapter-wise change summary

All chapters: humanizer pass (no em dashes in prose; "not X but Y" contrasts, staged openers and
one-line closers, stock words, decorative bold and repeated summaries removed); sentences shortened;
"Summary of Chapter N" boxes and per-chapter "Textbook basis" boxes removed (the second duplicated
Table 1.1, which still maps every chapter to Sarangi); mind maps kept under every Part, chapter and
section but drawn smaller and left out of the List of Figures.

- **Ch1**: "Parts" table removed (the report mind map shows the same structure); map-legend figure folded into the report-map caption; textbook table compressed to one line per chapter.
- **Ch2**: write-policy figure and access decision tree placed side by side; two sections merged; locality code rewritten as pseudo-code (Turnitin match).
- **Ch3**: one-core-to-many figure removed; topology figure and table side by side; Amdahl and "where coherence enters" merged; Flynn definition reworded (Turnitin missing-quotation match).
- **Ch4**: snooping and directory sections merged; order-axiom and FSM-notation figures side by side; directory and bus figures side by side.
- **Ch5**: all state diagrams and tables kept; read-miss tree moved into the MOESI section; prose condensed.
- **Ch6**: lineage figure removed (Table 6.1 and one sentence cover it); DASH sentence reworded (Turnitin match).
- **Ch7–10**: sections merged (messages + worked bill; transaction + root cause; patterns + traffic model; problem in words + formal statement); scaling plots side by side; requirements tree kept.
- **Part III (Ch11–14)**: every quotation, citation and Tables A–D kept. The Katz et al. sentence flagged by Turnitin as a close paraphrase is rewritten in our own words. Subsections became paragraphs. The hardware table was folded into Table D row 10 plus one paragraph. Traffic bar graphs placed side by side.
- **Part IV (Ch15–16)**: proofs of Propositions 15.1 and 16.1 moved to Appendix D (rule 7). The confounders table was replaced by one paragraph (the attribution tree covers it). The contributions subsection (which re-derived C4, C5 and C7 and repeated the crossover figure) became one table, C1–C16. The AMAT-comparison bar chart was removed; its numbers stay in Table 16.3.
- **Part V (Ch17–18)**: code listings and reproduction commands moved to Appendix E (rule 7); the simulator data-structure table, event-loop figure and experiment-to-hypothesis tree were removed (their content is in the text or the experiments table); the two verification tables were merged.
- **Part VI (Ch19–20)**: all plots and result tables kept; prediction boxes replaced by one sentence each; AMAT plot and memory-port plot side by side; the verdict map was removed (the verdict table covers it).
- **Part VII (Ch21–22)**: claims list turned into prose; the research-question answers no longer repeat the table line by line; the closing remark is merged into Future Work.
- **New**: copyright page (p. ii), acknowledgements (p. iii), Appendix A (Turnitin slot), Appendix B (reading indices), Appendix D (proofs), Appendix E (code), glossary, index.

## 3. Quality audit (open items for the team)

1. **Turnitin (rule 5)**: Appendix A needs the Turnitin report of *this* version. Submit the final PDF to Turnitin, save the report as `turnitin_report.pdf` in the project folder and rebuild; LaTeX inserts it automatically. The v1.0 report no longer matches.
2. **Acknowledgements**: they thank the course teaching assistants; delete that sentence if there were none, or add names. The copyright page has signature lines for all five members.
3. **Sources not read in full** (unchanged from v1.0, stated in the paper): the Katz et al. report and ISCA paper (states taken from Archibald & Baer); Yang et al. 1989 (listed as "full text not consulted"); the UnOwned / Owned Exclusively state names (flagged as unconfirmed).
4. **Inferred claim** (flagged in the text): token coherence serves a dirty read without a memory update, inferred from the token rules.
5. **Numbers**: every decimal and multi-digit number in v2.0 also appears in v1.0 (automated check, 520 distinct values); no simulation was re-run.
6. **LaTeX**: builds with `latexmk -pdf main.tex` with no errors or undefined references; three small overfull boxes (under 13 pt) remain, in the glossary and in two scriptsize Part III tables.
7. **Reading indices (rule 6)**: computed with `simulator/readability.py` (textstat 0.7.3) on running prose. Whole report: mean grade 8.7 (v1.0: 9.5), Flesch Reading Ease 71.0 (v1.0: 62.1). Re-run after any edit.
8. **AI detectors**: the rewrite improves the writing; it cannot guarantee any detector's verdict.

## 4. Professor-requirement checklist

| Rule | Status |
|---|---|
| LaTeX, A4, 1in margins, 0.5in gutter, 11pt, single spacing | kept (preamble geometry unchanged) |
| ~150 pages / 35,000 words | now 119 pages; see section 1 |
| Figures in TikZ / text-to-diagram | all figures TikZ, pgfplots or forest |
| References in Zotero, rendered with BibTeX | refs.bib + unsrtnat unchanged; no references added or removed |
| Mapping to the Sarangi textbook | Table 1.1, every chapter row |
| Topic brief: MESI transitions, MOESI Owned state, 2/4/8/16 cores, bus traffic and time, state diagrams, message logs, AMAT and congestion graphs | all present (Ch5, Ch15, Part VI, Appendix C); NoC congestion is modelled as bus utilisation and queueing, as stated in Table 18.1 |
| Mind maps before every topic | under every Part, chapter, section and appendix |
| Rule 5: plagiarism report as Appendix A | slot ready; needs the new Turnitin report |
| Rule 6: reading indices in Appendix B | done |
| Rule 7: explanations over half a page in their own appendix | proofs → App. D, code → App. E; no prose block left over half a page |
| Rule 8: auto ToC, LoT, LoF, Index, Glossary | all generated by LaTeX (index via makeindex, glossary via glossaries) |
| Rule 9: copyright assignment on page 2 | done (page ii) |
| Rule 10: acknowledgements on page 3 (people, Dept of EE, IIT Delhi) | done (page iii) |
