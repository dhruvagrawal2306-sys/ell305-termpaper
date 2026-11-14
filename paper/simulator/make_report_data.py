#!/usr/bin/env python3
"""
make_report_data.py -- export the simulation results used by Part VI of the
report as small data files that pgfplots reads directly.

    python3 make_report_data.py ../ell305-termpaper/data

Inputs : results/sweep_main.csv, results/sweep_cachesize.csv,
         results/timing_paired.csv   (produced by coherence_sim.py sweep,
         timing_sim.py run and analyze_timing.py)
Outputs: whitespace-separated .dat files with a header row, plus one TikZ
         snippet (e4_cells.tex) for the latency-sensitivity grid.
"""
import os
import sys
import numpy as np
import pandas as pd

OUT = sys.argv[1] if len(sys.argv) > 1 else "report_data"
os.makedirs(OUT, exist_ok=True)


def save(name, frame):
    frame.to_csv(os.path.join(OUT, name), sep=" ", index=False, float_format="%.4f")


# ------------------------------------------------------------------ traffic (T1)
df = pd.read_csv("results/sweep_main.csv")
k = ["N", "d", "seed", "pc_write_p"]
M = df[df.protocol == "MESI"].set_index(k)
O = df[df.protocol == "MOESI"].set_index(k)
S = df[df.protocol == "MSI"].set_index(k)
j = pd.DataFrame({"DSR": M.DSR, "DSR_rm": M.DSR_rm, "F": M.F, "Bs": S.B_tot, "Bm": M.B_tot,
                  "Bo": O.B_tot, "Ws": S.mem_write_B, "Wm": M.mem_write_B, "Wo": O.mem_write_B,
                  "tx": M.tx, "fwb": M.B_fwb}).reset_index()
j["S"] = (1 - j.Bo / j.Bm) * 100
j["bbar"] = j.Bm / j.tx

# H1: F and dirty share of read misses against N, for selected d
dsel = [0.005, 0.02, 0.1, 1.0]
fN = j.pivot_table(index="N", columns="d", values="F")[dsel] * 100
fN.columns = [f"d{c:g}".replace(".", "p") for c in dsel]
save("h1_F_vs_N.dat", fN.reset_index())
rN = j.pivot_table(index="N", columns="d", values="DSR_rm")[dsel] * 100
rN.columns = fN.columns
save("h1_dirtyshare_vs_N.dat", rN.reset_index())

# traffic of the three protocols, N = 8, normalised to MSI = 100 (interconnect) and MESI = 100 (memory)
t8 = j[j.N == 8].groupby("d").mean(numeric_only=True)
rows = []
for idx, d in enumerate([0.005, 0.02, 0.1, 0.5]):
    r = t8.loc[d]
    rows.append(dict(x=idx, d=d, msi=100.0, mesi=100 * r.Bm / r.Bs, moesi=100 * r.Bo / r.Bs,
                     memmesi=100.0, memmoesi=100 * r.Wo / r.Wm, memmsi=100 * r.Ws / r.Wm))
save("traffic_n8.dat", pd.DataFrame(rows))

# saving against the input knob d (log axis; d > 0 only)
sd = j[j.d > 0].pivot_table(index="d", columns="N", values="S")
sd.columns = [f"N{c}" for c in sd.columns]
save("S_vs_d.dat", sd.reset_index())

# DSR scatter, one file per core count
for N in (2, 4, 8, 16):
    t = j[(j.N == N) & (j.d > 0)][["DSR", "S"]]
    save(f"dsr_scatter_N{N}.dat", t)

# ------------------------------------------------------------------ cache sweep (T2)
c = pd.read_csv("results/sweep_cachesize.csv")
k2 = ["N", "d", "seed", "cap"]
cM = c[c.protocol == "MESI"].set_index(k2)
cO = c[c.protocol == "MOESI"].set_index(k2)
x = pd.DataFrame({"S": (1 - cO.B_tot / cM.B_tot) * 100,
                  "sigma": (cM.B_tot - cO.B_tot) / cM.B_fwb.replace(0, np.nan),
                  "DSR": cM.DSR, "ev_m": cM.evict_wb, "ev_o": cO.evict_wb,
                  "hit": cM.hit_rate * 100}).reset_index()
gx = x.groupby(["d", "cap"]).mean(numeric_only=True).reset_index()
wide = {"cap": sorted(gx.cap.unique())}
for d in (0.2, 0.5, 0.8):
    t = gx[gx.d == d].set_index("cap")
    tag = f"d{d:g}".replace(".", "p")
    wide[f"S{tag}"] = t.S.values
    wide[f"sig{tag}"] = t.sigma.values
    wide[f"evm{tag}"] = t.ev_m.values
    wide[f"evo{tag}"] = t.ev_o.values
    wide[f"dsr{tag}"] = t.DSR.values
    wide[f"hit{tag}"] = t.hit.values
save("t2_cache.dat", pd.DataFrame(wide))

# ------------------------------------------------------------------ timing
tp = pd.read_csv("results/timing_paired.csv")
tp["red"] = (1 - 1 / tp.sp) * 100
tp["bs"] = tp.bytes_saved * 100
e1 = tp[tp.tag == "E1"].groupby(["wb_mode", "N", "think"]).mean(numeric_only=True).reset_index()
for mode in ("serial", "overlap"):
    for N in (8, 16):
        t = e1[(e1.wb_mode == mode) & (e1.N == N)].sort_values("U_m")
        out = pd.DataFrame({"think": t.think, "Um": t.U_m * 100, "Uo": t.U_o * 100, "red": t.red,
                            "bs": t.bs, "conv": 100 * t.red / t.bs, "Wm": t.W_m, "Wo": t.W_o,
                            "Am": t.A_m, "Ao": t.A_o})
        save(f"e1_{mode}_N{N}.dat", out)

e2 = tp[tp.tag == "E2"].groupby(["think", "N"]).mean(numeric_only=True).reset_index()
for th, name in ((300, "light"), (40, "heavy")):
    t = e2[e2.think == th]
    save(f"e2_{name}.dat", pd.DataFrame({"N": t.N, "Am": t.A_m, "Ao": t.A_o, "Um": t.U_m * 100,
                                          "red": t.red}))

e3 = tp[tp.tag == "E3"].groupby(["d", "cap"]).mean(numeric_only=True).reset_index()
wide = {"cap": sorted(e3.cap.unique())}
for d in (0.2, 0.5, 0.8):
    t = e3[e3.d == d].set_index("cap")
    tag = f"d{d:g}".replace(".", "p")
    wide[f"red{tag}"] = t.red.values
    wide[f"bs{tag}"] = t.bs.values
save("e3_cache.dat", pd.DataFrame(wide))

e5 = tp[tp.tag == "E5"].groupby("MEM_OCC").mean(numeric_only=True).reset_index()
save("e5_memport.dat", pd.DataFrame({"x": range(len(e5)), "occ": e5.MEM_OCC, "MUm": e5.MU_m * 100,
                                      "MUo": e5.MU_o * 100, "Um": e5.U_m * 100, "red": e5.red}))

# E4 grid as TikZ cells (rows: T_COH high to low; columns: OWN_OCC)
e4 = tp[tp.tag == "E4"].pivot_table(index="T_COH", columns="OWN_OCC", values="red")
vmax = float(np.abs(e4.values).max())
lines = ["% generated by make_report_data.py -- do not edit by hand"]
cols = list(e4.columns)
rows_ = sorted(e4.index, reverse=True)
for yi, tc in enumerate(rows_):
    for xi, oc in enumerate(cols):
        v = float(e4.loc[tc, oc])
        shade = int(round(12 + 58 * abs(v) / vmax))
        colour = f"skyC!{shade}" if v >= 0 else f"alertRed!{shade}"
        txt = "white" if shade > 45 else "black"
        label = "0.0" if abs(v) < 0.05 else f"{v:+.1f}"
        lines.append(f"\\node[cell, fill={colour}, text={txt}] at ({xi*1.6:.1f},{-yi*0.75:.2f}) {{{label}}};")
for xi, oc in enumerate(cols):
    lines.append(f"\\node[font=\\sffamily\\scriptsize] at ({xi*1.6:.1f},0.62) {{{int(oc)}}};")
for yi, tc in enumerate(rows_):
    lines.append(f"\\node[font=\\sffamily\\scriptsize, anchor=east] at (-0.9,{-yi*0.75:.2f}) {{{int(tc)} (c2c {int(tc)-9})}};")
open(os.path.join(OUT, "e4_cells.tex"), "w").write("\n".join(lines) + "\n")
print("wrote data files to", OUT)
