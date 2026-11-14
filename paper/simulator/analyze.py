#!/usr/bin/env python3
"""analyze.py -- turn results/*.csv into figures and results_summary.md"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import coherence_sim as cs

BLUE, ORANGE, GREY, GREEN, RED = "#2B6CB0", "#E07B00", "#6B7280", "#2F855A", "#C53030"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 150})
OUT = "results"
os.makedirs(OUT, exist_ok=True)
md = []

# ---------------------------------------------------------------- Fig 1: B(C), simulated vs formula
Cs = list(range(1, 16))
sim_mesi = [cs.per_unit(cs.tr_prodcons, 20, "MESI", C + 1, C=C) for C in Cs]
sim_moesi = [cs.per_unit(cs.tr_prodcons, 20, "MOESI", C + 1, C=C) for C in Cs]
f_mesi = [160 + 80 * (C - 1) for C in Cs]
f_moesi = [88 + 80 * (C - 1) for C in Cs]
assert sim_mesi == f_mesi and sim_moesi == f_moesi
fig, ax = plt.subplots(figsize=(6.4, 4))
ax.plot(Cs, f_mesi, "-", color=BLUE, lw=2, label="MESI, report formula 160+80(C-1)")
ax.plot(Cs, f_moesi, "-", color=ORANGE, lw=2, label="MOESI, report formula 88+80(C-1)")
ax.plot(Cs, sim_mesi, "o", color=BLUE, mfc="white", ms=7, label="MESI, simulator")
ax.plot(Cs, sim_moesi, "s", color=ORANGE, mfc="white", ms=7, label="MOESI, simulator")
ax.set_xlabel("consumers per producer write, C")
ax.set_ylabel("interconnect bytes per round")
ax.set_title("Simulator reproduces the analytical model exactly")
ax.legend(fontsize=9, frameon=False)
fig.tight_layout(); fig.savefig(f"{OUT}/fig1_validation_BC.png"); plt.close(fig)

# F(C) for the producer-consumer model
Fm = [72 / b for b in f_mesi]
md.append("## 1. Validation\n")
md.append("All 22 checks in `python3 coherence_sim.py validate` pass: the simulator gives "
          "160/160/160 (MSI), 152/160/160 (MESI) and 152/88/88 (MOESI) bytes for the private, "
          "producer-consumer and migratory patterns, 80 B per reader for read-only data, and "
          "B(C) = 160+80(C-1) (MESI), 88+80(C-1) (MOESI) for C = 1..15, identical to the "
          "closed forms in the report.\n")
md.append("Steady-state forced-writeback fraction of the producer-consumer pattern, F(C) = 72/B(C):\n")
md.append("| C | " + " | ".join(str(c) for c in (1, 2, 4, 8, 15)) + " |")
md.append("|---|" + "---|" * 5)
md.append("| F (MESI) | " + " | ".join(f"{Fm[c-1]*100:.1f} %" for c in (1, 2, 4, 8, 15)) + " |")
md.append("| MOESI saving per round | " + " | ".join(f"{(1-f_moesi[c-1]/f_mesi[c-1])*100:.1f} %" for c in (1, 2, 4, 8, 15)) + " |\n")

# ---------------------------------------------------------------- main sweep
df = pd.read_csv(f"{OUT}/sweep_main.csv")
k = ["N", "d", "seed", "pc_write_p"]
M = df[df.protocol == "MESI"].set_index(k)
O = df[df.protocol == "MOESI"].set_index(k)
S = df[df.protocol == "MSI"].set_index(k)
j = pd.DataFrame({"DSR": M.DSR, "DSR_rm": M.DSR_rm, "F": M.F,
                  "B_msi": S.B_tot, "B_mesi": M.B_tot, "B_moesi": O.B_tot,
                  "W_mesi": M.mem_write_B, "W_moesi": O.mem_write_B}).reset_index()
j["save"] = 1 - j.B_moesi / j.B_mesi
j["mem_save"] = 1 - j.W_moesi / j.W_mesi.replace(0, np.nan)
j["mesi_vs_msi"] = 1 - j.B_mesi / j.B_msi
j.to_csv(f"{OUT}/summary_per_run.csv", index=False)
sh = j[j.d > 0]                       # runs that contain any sharing

# ---------------------------------------------------------------- Fig 2: F and MOESI saving vs N
g = sh[sh.d >= 0.1].groupby("N")
fig, ax = plt.subplots(figsize=(6.4, 4))
x = np.arange(4); w = 0.38
fm = g.F.mean().values; fo = g.save.mean().values
ax.bar(x - w/2, fm*100, w, color=BLUE, label="F: forced-writeback share of MESI traffic")
ax.bar(x + w/2, fo*100, w, color=ORANGE, label="MOESI traffic saved vs MESI")
for i in range(4):
    ax.text(x[i]-w/2, fm[i]*100+0.6, f"{fm[i]*100:.1f}", ha="center", fontsize=9)
    ax.text(x[i]+w/2, fo[i]*100+0.6, f"{fo[i]*100:.1f}", ha="center", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels([2, 4, 8, 16]); ax.set_xlabel("cores N")
ax.set_ylabel("percent of interconnect bytes"); ax.set_ylim(0, 52)
ax.set_title("RQ1: F(W,N) shrinks as cores are added\n(mixed workloads with dirty-sharing share d >= 0.1)", fontsize=11)
ax.legend(fontsize=8.5, frameon=False, loc="upper right")
fig.tight_layout(); fig.savefig(f"{OUT}/fig2_F_vs_cores.png"); plt.close(fig)

# ---------------------------------------------------------------- Fig 3: DSR vs saving
fig, ax = plt.subplots(figsize=(6.4, 4.2))
cols = {2: BLUE, 4: GREEN, 8: ORANGE, 16: RED}
for N, c in cols.items():
    t = sh[sh.N == N]
    ax.scatter(t.DSR, t.save*100, s=14, color=c, alpha=0.65, label=f"N = {N}")
a, b = np.polyfit(sh.DSR, sh.save*100, 1)
xs = np.linspace(0, 0.52, 50); ax.plot(xs, a*xs+b, color="black", lw=1.4, ls="--")
r = sh.DSR.corr(sh.save)
ax.text(0.02, 0.9*ax.get_ylim()[1] if False else 41, f"fit: saving = {a:.2f}·DSR {b:+.1f} %\nPearson r = {r:.3f}", fontsize=9)
ax.set_xlabel("Dirty Sharing Ratio, measured under MESI")
ax.set_ylabel("MOESI traffic saved (% of MESI bytes)")
ax.set_title("RQ3: DSR predicts the MOESI gain (synthetic workloads)", fontsize=11)
ax.legend(fontsize=9, frameon=False, loc="lower right")
fig.tight_layout(); fig.savefig(f"{OUT}/fig3_dsr_vs_saving.png"); plt.close(fig)

# ---------------------------------------------------------------- cache-size sweep
c = pd.read_csv(f"{OUT}/sweep_cachesize.csv")
k2 = ["N", "d", "seed", "cap"]
cM = c[c.protocol == "MESI"].set_index(k2); cO = c[c.protocol == "MOESI"].set_index(k2)
x = pd.DataFrame({"save": 1 - cO.B_tot/cM.B_tot, "DSR": cM.DSR, "F": cM.F,
                  "ev_mesi": cM.evict_wb, "ev_moesi": cO.evict_wb,
                  "hit": cM.hit_rate, "Bm": cM.B_tot, "Bo": cO.B_tot}).reset_index()
gx = x.groupby(["d", "cap"]).mean(numeric_only=True).reset_index()
fig, ax = plt.subplots(figsize=(6.4, 4))
for d, col in zip((0.2, 0.5, 0.8), (BLUE, GREEN, ORANGE)):
    t = gx[gx.d == d]
    ax.plot(t.cap, t.save*100, "-o", color=col, label=f"dirty-sharing share d = {d}")
ax.set_xscale("log", base=2); ax.set_xlabel("private cache capacity (64-byte blocks, log scale)")
ax.set_ylabel("MOESI traffic saved vs MESI (%)")
ax.set_title("RQ4: small caches erode the MOESI gain (N = 8)", fontsize=11)
ax.legend(fontsize=9, frameon=False, loc="lower right")
fig.tight_layout(); fig.savefig(f"{OUT}/fig4_cache_size.png"); plt.close(fig)
x.to_csv(f"{OUT}/summary_cachesize_per_run.csv", index=False)

# ---------------------------------------------------------------- text summary
md.append("## 2. Main sweep (RQ1, RQ3)\n")
md.append(f"{len(j)} configurations (N in 2,4,8,16; 11 sharing mixes; 3 seeds; 3 producer-write "
          f"probabilities), each run for the same trace under MSI, MESI and MOESI "
          f"({60000:,} accesses, 64 KB private caches so capacity does not interfere). "
          f"Bytes include one deferred writeback for every block still dirty at the end.\n")
md.append(f"* MOESI never moved more bytes than MESI in any of {len(j)} runs "
          f"(max B_MOESI / B_MESI = {(j.B_moesi/j.B_mesi).max():.3f}).")
md.append(f"* MESI never moved more bytes than MSI (min saving {j.mesi_vs_msi.min()*100:.2f} %, mean {j.mesi_vs_msi.mean()*100:.2f} %; "
          "the E state removes the upgrade on private data).\n")
md.append("| N | mean F (d>=0.1) | max F | mean MOESI saving | max MOESI saving | mean DSR |")
md.append("|---|---|---|---|---|---|")
for N, t in sh[sh.d >= 0.1].groupby("N"):
    md.append(f"| {N} | {t.F.mean()*100:.1f} % | {t.F.max()*100:.1f} % | {t.save.mean()*100:.1f} % | "
              f"{t.save.max()*100:.1f} % | {t.DSR.mean():.3f} |")
md.append("")
md.append(f"Over the {len(sh)} runs that contain any sharing: Pearson r(DSR, saving) = "
          f"{sh.DSR.corr(sh.save):.3f}; r(F, saving) = {sh.F.corr(sh.save):.5f}; "
          f"least-squares fit saving = {a:.3f}·DSR {b:+.2f} %.\n")
# error of the DSR predictor
pred = (a*sh.DSR + b)
err = (sh.save*100 - pred).abs()
md.append(f"Prediction error of the straight-line DSR model: mean {err.mean():.2f} points, "
          f"95th percentile {np.percentile(err,95):.2f} points, max {err.max():.2f} points of saving.\n")
md.append("**Important caveat.** In a bytes-only model the traffic MOESI saves is exactly the forced-writeback "
          "bytes MESI would have sent, minus any writeback MOESI merely defers. That is why F tracks the saving almost "
          "perfectly (r ~ 1.000) and is true by construction, not a discovery. DSR is the quantity a real "
          "workload can supply cheaply (one counter under MESI); its predictive quality on real traces, where "
          "timing, banking and block-size effects exist, is the actual test and is not shown here.\n")

md.append("## 3. Cache-capacity sweep (RQ4), N = 8\n")
md.append("| d | capacity (blocks) | DSR | MESI hit rate | MOESI saving | evict-WBs MESI | evict-WBs MOESI |")
md.append("|---|---|---|---|---|---|---|")
for _, rr in gx.iterrows():
    md.append(f"| {rr.d:.1f} | {int(rr.cap)} | {rr.DSR:.3f} | {rr.hit*100:.1f} % | {rr.save*100:.1f} % | "
              f"{rr.ev_mesi:,.0f} | {rr.ev_moesi:,.0f} |")
md.append("")
md.append(f"MOESI moved no more bytes than MESI in any of {len(x)} cache-size runs "
          f"(max ratio {(x.Bo/x.Bm).max():.3f}). With tiny caches MOESI does perform more eviction writebacks than MESI "
          "(MESI has already cleaned the block at the earlier remote read, so its later eviction is silent); "
          "even so, total bytes were never higher. Whether the deferral hurts *time* (owner-supplied "
          "data holding the owner's cache port, slower cache-to-cache path than memory) cannot be answered by a "
          "byte-counting model and needs the timing simulation planned for RQ2/RQ4.\n")

with open(f"{OUT}/results_summary.md", "w") as f:
    f.write("# Simulator results\n\n" + "\n".join(md))
print("\n".join(md))
