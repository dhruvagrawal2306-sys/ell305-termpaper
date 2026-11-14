# Part III — Source Audit and Verification Notes

ELL305 Term Paper, Draft v0.3. This file maps every technical claim in Part III
(`chapters/part_III.tex`) to the source that supports it. It also lists what could
not be verified. Keep it alongside the Zotero collection *ELL305 – Part III*.

Status key:
- **Read**: the passage was read in the source, at the stated location.
- **Inferred**: our conclusion from rules stated in the source. Marked "inferred" in the text.
- **Ours**: our analytical model. Labelled as such in the text.
- **Not accessed**: metadata verified, but the full text was not read.

## 1. Source audit

| # | Claim in Part III | Where | Source | Location | Status |
|---|---|---|---|---|---|
| 1 | Berkeley is an "ownership-based" protocol for a single-chip VLSI controller; interlocks emphasised; carried to CMOS layout | §11.2.1 | Katz et al., UCB/CSD-84-207 | abstract page | Read (abstract only) |
| 2 | Berkeley states: Invalid, Valid, Shared-Dirty, Dirty | §11.2.2, Tab. 11.1 | Archibald & Baer 1986 | pp. 277–278 | Read |
| 3 | Berkeley owner supplies on remote read; owner → SD, requester → Valid; no memory update | §11.2.3 | Archibald & Baer 1986 | pp. 277–278 | Read |
| 4 | Berkeley SD/Dirty written back on replacement | §11.2.3 | Archibald & Baer 1986 | p. 277 | Read |
| 5 | Berkeley write to Valid/SD needs an invalidation first; writer → Dirty | §11.2.4 | Archibald & Baer 1986 | p. 278 | Read |
| 6 | Berkeley "surpasses the Illinois scheme at levels of high sharing", because it does not update memory on a miss to a modified block | §11.5, §14.4 | Archibald & Baer 1986 | p. 295 | Read |
| 7 | MOESI is a *class* of compatible protocols; quote on consistency | §11.3.1 | Sweazey & Smith 1986 | p. 415, abstract | Read |
| 8 | Berkeley and Dragon are members; Illinois, Firefly and Write-Once are adaptable | §11.3.1 | Sweazey & Smith 1986 | abstract | Read |
| 9 | Three attributes (validity, exclusiveness, ownership); three bits; five states | §11.3.2 | Sweazey & Smith 1986 | p. 416 | Read |
| 10 | M and O are intervenient and must supply data on a read miss | §11.3.2 | Sweazey & Smith 1986 | pp. 418–419 | Read |
| 11 | Owner duties: update memory, pass ownership, or substitute for memory | §11.3.2, §11.5 | Sweazey & Smith 1986 | p. 417 | Read |
| 12 | Futurebus signals CH, DI, IM, BS | §11.3.3, Fig. 11.3 | Sweazey & Smith 1986 | pp. 417–418 | Read |
| 13 | Futurebus cannot update memory during a cache-to-cache transfer; Write-Once and Firefly abort, write back and restart | §11.3.5, §14.3 | Sweazey & Smith 1986 | p. 418 | Read |
| 14 | Dragon updates memory "only on a replacement" | §12.1.2 | Sweazey & Smith 1986 | p. 420 | Read |
| 15 | W_MESI(k)=k, W_MOESI(k)=1 | Eq. 11.2 | — | — | Ours |
| 16 | gem5 MOESI_CMP_directory invalidates on a forwarded read in M instead of sharing dirty data; implementations differ in many states | §11.5, §14.4 | Mallya et al. 2015 | results discussion | Read |
| 17 | MOESI advantage shrinks with a larger L2 | §11.5 | Fagundes & Souza 2024 | conclusions | Read |
| 18 | MESI downgrade writebacks reach DRAM; O removes them; MOESI-prime has 7 states in 3 bits; runtime −0.51 % to +0.61 % | §11.5, §13.1.3, §14.3 | Loughlin et al. 2022 | abstract, §§ on sources and results | Read |
| 19 | Firefly: Dirty and Shared tag bits; MShared signal | §12.1.1 | Thacker et al., SRC RR-23 | p. 7 | Read |
| 20 | Firefly: write to shared line is written through; caches and main storage updated | §12.1.1 | Thacker et al., SRC RR-23 | p. 7 | Read |
| 21 | Firefly: caches supply on a read miss; memory inhibited | §12.1.1 | Thacker et al., SRC RR-23 | p. 8 | Read |
| 22 | Firefly: dirty block supplied and written to memory at the same time; all → Shared | §12.1.1 | Archibald & Baer 1986 | p. 280 | Read |
| 23 | "Firefly must send distributed writes to memory while the Dragon sends them to the caches only" | §12.1.1 | Archibald & Baer 1986 | p. 295 | Read |
| 24 | Dragon: states VE, SC, SD, Dirty; owner supplies → SD; requester SC | §12.1.2 | Archibald & Baer 1986 | p. 281 | Read |
| 25 | Dragon: shared write does not go to memory; last writer is SD owner, responsible on replacement | §12.1.2 | Archibald & Baer 1986 | pp. 281–282 | Read |
| 26 | Dragon shared write: writer → SD, others → SC | §14.2 | Archibald & Baer 1986 | p. 282 | Read |
| 27 | Illinois, Firefly and Dragon VE → Dirty with no bus transaction | Tab. 14.3 note, Table D | Archibald & Baer 1986 | pp. 279, 281, 282 | Read |
| 28 | Distributed write "yields the best performance in the handling of shared data" | §12.1 | Archibald & Baer 1986 | p. 294 | Read |
| 29 | Update vs invalidate traffic (Eqs. 12.1–12.3; Fig. 12.2) | §12.1.3 | — | — | Ours |
| 30 | MESIF completed 2001; directory needs at least three serial communications | §12.2.1 | Goodman & Hum 2009 | §1 | Read |
| 31 | F state definition; F moves to the requester; "coherent with memory" | §12.2.2 | Goodman & Hum 2009 | §2.1, §2.1.1 case ii | Read |
| 32 | Read of an M line handled "as if… Read-for-Ownership"; variant keeps S and cleanses, or uses FM | §12.2.3 | Goodman & Hum 2009 | §2.1.1 case iv | Read |
| 33 | No memory update described for the basic M case | §12.2.3 | Goodman & Hum 2009 | §2.1.1 case iv | Read (absence noted) |
| 34 | MVA projection of 6–11 %, algorithms undisclosed; no benefit for hitI/hitS; snoop stalls; 3 virtual channels | §12.2.4, §14.3 | Goodman & Hum 2009 | §§2.1–2.3, §3 | Read |
| 35 | Synapse: NAK; holder writes back; requester retries | Fig. 12.3 | Archibald & Baer 1986 | p. 276 | Read |
| 36 | Write-once: dirty cache supplies and writes back | Fig. 12.3 | Archibald & Baer 1986 | p. 276 | Read |
| 37 | Illinois: dirty block also written to memory when supplied | Fig. 12.3 | Archibald & Baer 1986 | p. 279 | Read |
| 38 | DASH directory states and cache states | §13.1.2 | Lenoski et al. 1990 | §4 | Read |
| 39 | DASH entry: one state bit plus a 16-bit cluster vector (17 bits) | §13.1.2 | Lenoski et al. 1990 | §3 | Read; the 17-bit total is our count |
| 40 | DASH remote dirty read: forward; data to requester; sharing writeback updates memory and directory | §13.1.2, Fig. 13.2a | Lenoski et al. 1990 | §4.1 | Read |
| 41 | DASH latencies of about 80 vs 61 clocks | §13.1.2, §14.3 | Lenoski et al. 1990 | §4.2, Fig. 6 | Read |
| 42 | DASH NAK and reissue; directory scaling remedies | §13.1.2, §13.3 | Lenoski et al. 1990 | §§4.1, 4.6, 6 | Read |
| 43 | Owner-retaining directory transaction (Fig. 13.2b) | §13.1.3 | — | — | Ours |
| 44 | Token rules: T tokens; all to write; one to read | §13.2.1 | Martin et al. 2003 | §3.1 | Read |
| 45 | Owner token must carry data; maps to MOESI O | §13.2.2 | Martin et al. 2003 | §3.1 | Read |
| 46 | On a shared request, data is sent with one non-owner token; on eviction, tokens and data go to memory | §13.2.2 | Martin et al. 2003 | §§3.1, 4.2 | Read |
| 47 | No memory update on a read of a dirty block | §13.2.2, Table D | Martin et al. 2003 | — | **Inferred** |
| 48 | Migratory optimisation: data and all tokens sent | §13.2.2 | Martin et al. 2003 | §4.2 | Read |
| 49 | Persistent requests; TokenB broadcast; unordered torus; 3.0 % / 0.2 %; speed and traffic results; 2+log2T bits; 8-byte messages | §13.2.3–4 | Martin et al. 2003 | §§3.1–3.2, 4.1–4.2, 5.1–5.2, 6 | Read |
| 50 | B_TokenB(N) = 8(N−1)+72 | Eq. 13.1 | — | — | Ours |
| 51 | All of Table 14.3, Figs. 14.3–14.4 and Table 14.4 | §14.2 | — | — | Ours |
| 52 | A&B method: synthetic, one bus, 1–15 processors, "system power" | §14.4 | Archibald & Baer 1986 | pp. 283–287 | Read |
| 53 | Yang et al.: MVA queueing models of 7 protocols on a packet-switched bus | §14.4 | Yang et al. 1989 | abstract | Read (abstract only) |
| 54 | Adaptive migratory protocol, detected dynamically | §14.5.2 | Stenström et al. 1993 | abstract | Read (abstract only) |
| 55 | Migratory detection rule (write by a processor other than the last writer) | §14.5.2 | Nilsson & Stenström 1994 | detection section | Read |
| 56 | A&B shared-reference fraction parameter | §14.5.2 | Archibald & Baer 1986 | p. 286 | Read |

## 2. New references added (`part_III.bib`)

| Key | Reference | Metadata verified against |
|---|---|---|
| `katz1985implementing` | Katz, Eggers, Wood, Perkins, Sheldon, ISCA 1985, pp. 276–283, DOI 10.1145/327070.327237 | DBLP / UW publication record |
| `katz1984implementing` | same authors, UCB/CSD-84-207, Oct 1984 | Berkeley EECS technical-report page |
| `thacker1987firefly` | Thacker, Stewart, Satterthwaite, SRC Research Report 23, Dec 1987 (reprint of the ASPLOS II paper) | the report itself |
| `yang1989analysis` | Yang, Bhuyan, Liu, IEEE TC 38(8):1143–1153, 1989, DOI 10.1109/12.30868 | URI Digital Commons record |
| `stenstrom1990survey` | Stenström, *Computer* 23(6), 1990, DOI 10.1109/2.55497 | DOI only (see §3) |
| `stenstrom1993adaptive` | Stenström, Brorsson, Sandberg, ISCA 1993, DOI 10.1145/165123.165147 | DOI landing page (see §3) |
| `nilsson1994adaptive` | Nilsson, Stenström, PARLE 1994 | the paper itself |
| `mallya2015simulation` | Mallya, Patil, Raveendran, iNIS 2015, pp. 125–130, DOI 10.1109/iNIS.2015.52 | the paper itself |
| `fagundes2024evaluation` | Fagundes, Souza, SSCAD 2024 extended proceedings, pp. 17–24, DOI 10.5753/sscad_estendido.2024.244058 | SBC citation export |
| `loughlin2022moesiprime` | Loughlin, Saroiu, Wolman, Manerkar, Kasikci, ISCA 2022, DOI 10.1145/3470496.3527427 | the paper itself |

Existing entries updated:
- `sweazey1986moesi`: pp. 414–423.
- `lenoski1990dash`: pp. 148–159.
- `goodman2009mesif`: note added (manuscript dated 17 Nov 2009, no report number).

## 3. Unresolved items to check manually before v1.0

1. **Berkeley state names in the original.** The full text of Katz et al. (both the report and the paper) could not be read: the report PDF is a scanned image and the paper's host refused access. Part III uses Archibald & Baer's names (Invalid, Valid, Shared-Dirty, Dirty). The original terms (UnOwned, Owned Exclusively, Owned NonExclusively) should be checked against the ISCA 1985 paper, pp. 276–283, through the IIT Delhi library (ACM DL).
2. **Stenström 1990 survey.** RESOLVED (10 Nov): *Computer* 23(6), June 1990, pp. 12–24 confirmed (scilit record); added to both .bib files.
3. **Stenström, Brorsson and Sandberg 1993.** RESOLVED (10 Nov): authors and ISCA 1993 pp. 109–118 confirmed (researchr record); pages added to both .bib files.
4. **Yang, Bhuyan and Liu 1989.** Only the abstract was read. Their findings are deliberately not reported in Table 14.6.
5. **Token coherence and memory updates.** The claim that a read of a dirty block causes no memory update is our inference from the token rules. The paper does not state it directly, and the text marks it "inferred".
6. **Thacker et al. authorship.** The SRC reprint lists three authors (with Satterthwaite). Some catalogues list the ASPLOS II paper under Thacker and Stewart only. Cite whichever version is consulted.
7. **AMD64 manual entry.** RESOLVED (10 Nov): Publication No. 24593, Revision 3.10, February 2005; MOESI is in Section 7.2 and Fig. 7-2 "MOESI State Transitions". Added to refs.bib.

## 4. Zotero

This session had no access to Zotero. `part_III.bib` was written by hand from the verified metadata above, in the same key style as `refs.bib`. To meet the course requirement:

1. Create the collection *ELL305 – Part III*.
2. Use File → Import to bring in `part_III.bib`.
3. Attach the PDFs.
4. Let Better BibTeX pin the existing keys.
5. Re-export.

If Better BibTeX generates different keys, update the `\cite` commands in `part_III.tex` to match.
