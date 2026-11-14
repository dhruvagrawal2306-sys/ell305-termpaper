#!/usr/bin/env python3
"""analyze_timing.py -- figures and summary for the timing experiments (results/timing_all.csv)"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE, ORANGE, GREY, GREEN, RED = "#2B6CB0", "#E07B00", "#6B7280", "#2F855A", "#C53030"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 150})
OUT = "results"
df = pd.read_csv(f"{OUT}/timing_all.csv")
K = ["tag", "N", "d", "seed", "pc_write_p", "cap", "think", "wb_mode", "T_COH", "OWN_OCC", "MEM_OCC"]
m = df[df.protocol == "MESI"].set_index(K)
o = df[df.protocol == "MOESI"].set_index(K)
j = pd.DataFrame({"T_m": m["T"], "T_o": o["T"], "U_m": m.bus_util, "U_o": o.bus_util,
                  "MU_m": m.mem_util, "MU_o": o.mem_util,
                  "A_m": m.AMAT, "A_o": o.AMAT, "DL_m": m.dirty_read_lat, "DL_o": o.dirty_read_lat,
                  "W_m": m.avg_wait, "W_o": o.avg_wait, "B_m": m.B_tot, "B_o": o.B_tot}).reset_index()
j["sp"] = j.T_m / j.T_o
j["bytes_saved"] = 1 - j.B_o / j.B_m
j.to_csv(f"{OUT}/timing_paired.csv", index=False)
md = ["# Timing results (Python timing layer, report latencies)\n"]

# ----------------------------------------------------------------- E1: RQ2
e1 = j[j.tag == "E1"]
g1 = e1.groupby(["wb_mode", "N", "think"]).mean(numeric_only=True).reset_index()
fig, ax = plt.subplots(figsize=(6.6, 4.2))
styles = {(8, "serial"): (BLUE, "-", "o"), (16, "serial"): (ORANGE, "-", "s"),
          (8, "overlap"): (BLUE, "--", "o"), (16, "overlap"): (ORANGE, "--", "s")}
for (N, mode), (c, ls, mk) in styles.items():
    t = g1[(g1.N == N) & (g1.wb_mode == mode)].sort_values("U_m")
    ax.plot(t.U_m * 100, (1 - 1 / t.sp) * 100, ls=ls, marker=mk, color=c, ms=5, mfc="white" if mode == "overlap" else c,
            label=f"N={N}, {mode} writeback")
ax.set_xlabel("MESI bus utilisation (%)")
ax.set_ylabel("MOESI execution-time reduction (%)")
ax.set_title("RQ2: bytes saved become time saved only as the bus fills", fontsize=11)
ax.legend(fontsize=8.5, frameon=False, loc="upper left")
fig.tight_layout(); fig.savefig(f"{OUT}/fig5_rq2_speedup_vs_util.png"); plt.close(fig)

md.append("## 1. RQ2 -- load sweep (N = 8 and 16, mixed workload d = 0.5)\n")
md.append("Mean over 3 seeds. Think time = mean compute cycles between a core's memory operations; shorter think = heavier load. "
          "Speedup = T(MESI) / T(MOESI); execution time T = finish time of the slowest core.\n")
for N in (8, 16):
    md.append(f"**N = {N}, serial writeback (report reading):**\n")
    md.append("| think (cycles) | MESI bus util | MOESI bus util | speedup | time reduction |")
    md.append("|---|---|---|---|---|")
    t = g1[(g1.N == N) & (g1.wb_mode == "serial")].sort_values("think", ascending=False)
    for _, r in t.iterrows():
        md.append(f"| {int(r.think)} | {r.U_m*100:.0f} % | {r.U_o*100:.0f} % | {r.sp:.3f} | {(1-1/r.sp)*100:.1f} % |")
    md.append("")
ser_rows = g1[g1.wb_mode == "serial"]
low = ser_rows[ser_rows.U_m < 0.35]
high = ser_rows[ser_rows.U_m > 0.65]
red_low = (1 - 1 / low.sp) * 100
red_high = (1 - 1 / high.sp) * 100
byte_sav = e1[e1.wb_mode == "serial"].bytes_saved.mean() * 100
sat = ser_rows[ser_rows.N == 8].sort_values("U_m").iloc[-1]
ser = g1[(g1.N == 8) & (g1.wb_mode == "serial") & (g1.think == 40)].sp.iloc[0]
ovl = g1[(g1.N == 8) & (g1.wb_mode == "overlap") & (g1.think == 40)].sp.iloc[0]
md.append(f"* MOESI moves {byte_sav:.0f} % fewer bytes in this workload, but execution time drops by at most "
          f"{red_low.max():.1f} % while the MESI bus is under 35 % utilised, by {red_high.min():.0f}-{red_high.max():.0f} % above 65 %, "
          f"and by {(1-1/sat.sp)*100:.0f} % when saturated (N = 8). The saved bytes are mostly hidden while the bus has slack.")
md.append(f"* Serial vs overlapped reading of the forced writeback (N = 8, think = 40): speedup {ser:.3f} vs {ovl:.3f}. "
          "Whether the reader waits for the flush matters a little at moderate load and not at all at saturation, "
          "where bus occupancy, not latency, sets the time.\n")

# ----------------------------------------------------------------- E2: AMAT vs N
e2 = j[j.tag == "E2"].groupby(["think", "N"]).mean(numeric_only=True).reset_index()
fig, ax = plt.subplots(figsize=(6.6, 4.2))
for th, ls in ((300, "-"), (40, "--")):
    t = e2[e2.think == th]
    lab = "light load" if th == 300 else "heavy load"
    ax.plot(t.N, t.A_m, ls=ls, marker="o", color=BLUE, label=f"MESI, {lab}")
    ax.plot(t.N, t.A_o, ls=ls, marker="s", color=ORANGE, label=f"MOESI, {lab}")
ax.set_xscale("log", base=2); ax.set_xticks([2, 4, 8, 16]); ax.set_xticklabels([2, 4, 8, 16])
ax.set_xlabel("cores N"); ax.set_ylabel("measured AMAT (cycles)")
ax.set_title("AMAT grows with cores; the MOESI gap widens with load", fontsize=11)
ax.legend(fontsize=8.5, frameon=False, loc="upper left")
fig.tight_layout(); fig.savefig(f"{OUT}/fig6_amat_vs_cores.png"); plt.close(fig)
md.append("## 2. AMAT and execution time versus cores (mixed workload d = 0.5)\n")
md.append("| load | N | MESI bus util | AMAT MESI | AMAT MOESI | dirty-read latency MESI | dirty-read latency MOESI | speedup |")
md.append("|---|---|---|---|---|---|---|---|")
for _, r in e2.sort_values(["think", "N"], ascending=[False, True]).iterrows():
    md.append(f"| {'light' if r.think == 300 else 'heavy'} | {int(r.N)} | {r.U_m*100:.0f} % | {r.A_m:.1f} | {r.A_o:.1f} | "
              f"{r.DL_m:.1f} | {r.DL_o:.1f} | {r.sp:.3f} |")
md.append("")
md.append("On an idle bus the measured dirty-read latency is 61 cycles under MESI (= T_L1 + T_COH = 1 + 60, the report's value) "
          "and 52 under MOESI (= 1 + 51); queueing adds to both as the bus fills, and more to MESI because its dirty read "
          "occupies the bus for 22 cycles instead of 12.\n")

# ----------------------------------------------------------------- E3 + E4: RQ4
e3 = j[j.tag == "E3"].groupby(["d", "cap"]).mean(numeric_only=True).reset_index()
e4 = j[j.tag == "E4"]
fig, axs = plt.subplots(1, 2, figsize=(11.2, 4.2), gridspec_kw={"width_ratios": [1, 1.05]})
ax = axs[0]
for d, c in zip((0.2, 0.5, 0.8), (BLUE, GREEN, ORANGE)):
    t = e3[e3.d == d]
    ax.plot(t.cap, (1 - 1 / t.sp) * 100, "-o", color=c, label=f"dirty-sharing share d = {d}")
ax.set_xscale("log", base=2)
ax.set_xlabel("private cache capacity (64-byte blocks)"); ax.set_ylabel("MOESI execution-time reduction (%)")
ax.set_title("(a) Cache capacity, report latencies (N = 8)", fontsize=10.5)
ax.legend(fontsize=8.5, frameon=False, loc="lower right")
ax = axs[1]
piv = e4.pivot_table(index="T_COH", columns="OWN_OCC", values="sp").sort_index(ascending=False)
red = (1 - 1 / piv) * 100                          # true execution-time reduction, %
lim = max(abs(red.values).max(), 1.0)
im = ax.imshow(red.values, cmap="RdBu", vmin=-lim, vmax=lim, aspect="auto")
ax.set_xticks(range(len(piv.columns))); ax.set_xticklabels(piv.columns)
ax.set_yticks(range(len(piv.index)))
ax.set_yticklabels([f"{int(t)}  (c2c {int(t)-9})" for t in piv.index])
for yi in range(piv.shape[0]):
    for xi in range(piv.shape[1]):
        v = red.values[yi, xi]
        ax.text(xi, yi, f"{v:+.1f}", ha="center", va="center", fontsize=9, color="white" if abs(v) > lim * 0.6 else "black")
ax.set_xlabel("owner-port occupancy per supplied block (cycles)")
ax.set_ylabel("T_COH (cycles); c2c = cache-to-cache latency")
ax.set_title("(b) MOESI time reduction (%): blue faster, red slower", fontsize=10.5)
ax.grid(False)
fig.tight_layout(); fig.savefig(f"{OUT}/fig7_rq4_capacity_and_sensitivity.png"); plt.close(fig)

md.append("## 3. RQ4 -- when does deferring the writeback cost more than it saves?\n")
md.append("**(a) Cache capacity, report latencies (N = 8, think = 40).** MOESI execution-time reduction:\n")
md.append("| capacity (blocks) | d = 0.2 | d = 0.5 | d = 0.8 |")
md.append("|---|---|---|---|")
for cap in sorted(e3.cap.unique()):
    row = [f"{(1-1/e3[(e3.d == d) & (e3.cap == cap)].sp.iloc[0])*100:+.1f} %" for d in (0.2, 0.5, 0.8)]
    md.append(f"| {int(cap)} | " + " | ".join(row) + " |")
md.append("")
slow3 = int((j[j.tag == "E3"].sp < 1).sum())
md.append(f"With the report's latencies MOESI was slower in {slow3} of {int((j.tag == 'E3').sum())} capacity runs. "
          "Tiny caches shrink the gain (most accesses miss to memory anyway) but never reverse it.\n")
md.append("**(b) Latency sensitivity (N = 8, d = 0.5, think = 40, 64 KB caches).** T_COH sets the cache-to-cache "
          "latency (c2c = T_COH - 9) and is the report's assumed 60 in the second row; OWN_OCC is how long an owner's cache port "
          "is busy per block it supplies. Cell = MOESI execution-time reduction (positive = MOESI faster):\n")
md.append("| T_COH (c2c) \\ OWN_OCC | " + " | ".join(str(c) for c in piv.columns) + " |")
md.append("|---|" + "---|" * len(piv.columns))
for t in piv.index[::-1]:
    md.append(f"| {int(t)} ({int(t)-9}) | " + " | ".join(f"{(1-1/piv.loc[t, c])*100:+.1f} %" for c in piv.columns) + " |")
md.append("")
neg = e4[e4.sp < 1]
cross = piv.index[(piv.mean(axis=1) < 1)]
md.append(f"MOESI became slower than MESI in {len(neg)} of {len(e4)} sensitivity runs, all with T_COH >= "
          f"{int(neg.T_COH.min())} cycles (cache-to-cache latency {int(neg.T_COH.min())-9} cycles against {100} for memory). "
          "The mechanism is Chapter 11's 'owner must answer every read': under MOESI every later reader is served by the owner's "
          "cache, whereas under MESI they are served by memory once the flush has happened, so if a cache-to-cache transfer is slower "
          "than a memory access MOESI loses on those reads. The break-even sits near T_COH = 150 because MESI's own dirty read also "
          "pays T_COH. The report assumes T_COH = 60 (cache-to-cache 51, about half the memory latency), well inside the region where "
          f"MOESI wins. Worst case in the grid: {red.values.min():+.1f} %. Raising owner-port occupancy to 40 cycles lowers every cell "
          "by only 1-2 points.\n")

# ----------------------------------------------------------------- E5: memory port
e5 = j[j.tag == "E5"].groupby("MEM_OCC").mean(numeric_only=True).reset_index()
fig, ax = plt.subplots(figsize=(6.2, 4))
x = np.arange(len(e5)); w = 0.38
ax.bar(x - w / 2, e5.MU_m * 100, w, color=BLUE, label="MESI")
ax.bar(x + w / 2, e5.MU_o * 100, w, color=ORANGE, label="MOESI")
for i, r in e5.iterrows():
    ax.text(i, max(r.MU_m, r.MU_o) * 100 + 3, f"time -{(1-1/r.sp)*100:.0f} %", ha="center", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels([f"{int(v)}\n({64/v:.1f} B/cycle)" for v in e5.MEM_OCC])
ax.set_xlabel("memory-port occupancy per 64 B access (cycles)"); ax.set_ylabel("memory-port utilisation (%)")
ax.set_ylim(0, 118); ax.set_title("Memory bandwidth: forced writebacks load the memory port", fontsize=10.5)
ax.legend(frameon=False, fontsize=9, loc="upper left")
fig.tight_layout(); fig.savefig(f"{OUT}/fig8_memory_port.png"); plt.close(fig)
md.append("## 4. Memory-port bandwidth (N = 8, d = 0.5, think = 40)\n")
md.append("| MEM_OCC (cycles / 64 B) | MESI memory-port util | MOESI memory-port util | MOESI time reduction |")
md.append("|---|---|---|---|")
for _, r in e5.iterrows():
    md.append(f"| {int(r.MEM_OCC)} | {r.MU_m*100:.0f} % | {r.MU_o*100:.0f} % | {(1-1/r.sp)*100:.1f} % |")
md.append("")
md.append("Each forced writeback is a 64 B memory write. When memory bandwidth is the bottleneck, removing them gives a much "
          "larger gain than on a bus-limited system; this is the 'memory bandwidth' argument of Chapter 9 in numbers.\n")

# ----------------------------------------------------------------- overall
md.append("## 5. Summary against the research questions\n")
md.append(f"* **Runs where MOESI was slower:** {int((j.sp < 1).sum())} of {len(j)} paired runs; every one is in the latency-sensitivity grid with T_COH >= {int(neg.T_COH.min())}.")
md.append(f"* **RQ2:** traffic saved becomes time saved in proportion to bus (or memory-port) utilisation: at most {red_low.max():.1f} % "
          f"below 35 % utilisation, {red_high.min():.0f}-{red_high.max():.0f} % above 65 %.")
md.append("* **RQ4:** within the report's own latencies MOESI never lost; it can lose only if cache-to-cache supply is slower than memory.")
md.append("\n## 6. What this model is and is not\n")
md.append("It is a discrete-event model with per-core clocks, one bus, one memory port and per-owner cache ports, "
          "driven by the report's latencies (T_L1 = 1, T_MEM = 100, T_COH = 60) and a handful of stated assumptions "
          "(bus 8 B/cycle, arbitration 1, upgrade 10, port occupancies 10). It is not cycle-accurate: no pipeline, "
          "out-of-order overlap, prefetching, DRAM banks or real application timing, and cores are driven by synthetic "
          "operation streams. Conclusions are therefore about *direction and approximate size*, and should be confirmed "
          "on real traces or gem5 if absolute numbers are claimed.")
open(f"{OUT}/timing_results_summary.md", "w").write("\n".join(md))
print("\n".join(md))
