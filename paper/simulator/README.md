# ELL305 coherence simulator (MSI / MESI / MOESI)

Needs Python 3.9+, numpy, pandas, matplotlib. Seeds are fixed: reruns are identical.

## Layer 1 -- traffic (bytes)
    python3 coherence_sim.py validate   # 22 checks against the report's analytic numbers
    python3 coherence_sim.py sweep      # ~40 s -> results/sweep_*.csv
    python3 analyze.py                  # figs 1-4 + results/results_summary.md

## Layer 2 -- timing (cycles), replaces the gem5 cross-check
    python3 timing_sim.py validate      # 11 checks: idle latencies, bus occupancy, queueing
    python3 timing_sim.py run           # ~20 s -> results/timing_all.csv
    python3 analyze_timing.py           # figs 5-8 + results/timing_results_summary.md

Report constants: byte costs 8/72/72 B (Table tab:counting-rules); T_L1 = 1, T_MEM = 100, T_COH = 60 cycles
(eq:amat, eq:amat-coh). Everything else in timing_sim.py (bus 8 B/cycle, arbitration 1, upgrade 10, port
occupancies 10) is an ASSUMPTION, listed in its header and swept in experiments E4/E5.
Workloads are synthetic mixtures of the four sharing patterns, NOT real application traces.

## Data for the report's figures (Part VI)
    python3 make_report_data.py ../ell305-termpaper/data   # writes data/*.dat and data/e4_cells.tex
The report plots these files directly with pgfplots, so rerunning the steps above and this script regenerates every figure of Part VI.

## Appendix A tables
    python3 make_appendix_tables.py ../ell305-termpaper/data/appendix_tables.tex   # message logs, built from results/*.csv
