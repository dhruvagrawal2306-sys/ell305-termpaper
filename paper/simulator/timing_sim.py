#!/usr/bin/env python3
"""
timing_sim.py -- timing layer on top of coherence_sim.py
ELL305 term paper: "Cache Coherence Overhead: MESI vs MOESI"

Purpose
-------
The byte-counting simulator cannot say whether traffic saved by MOESI becomes
*time* saved (RQ2) or when deferring writebacks hurts (RQ4). This layer adds
time, using the latencies the report itself assumes, in a discrete-event
simulation with one clock per core. It replaces the gem5 cross-check with a
model the team can read and defend. It is NOT cycle-accurate gem5.

Latencies taken from the report (Chapters 2 and 8)
--------------------------------------------------
  T_L1   = 1 cycle      cache hit                     (eq:amat example, Sarangi Ex.147)
  T_MEM  = 100 cycles   memory read                   (same example; hierarchy figure: 100-300)
  T_COH  = 60 cycles    block obtained from another cache *including the
                        writeback the protocol performs on the way* (eq:amat-coh,
                        fig:amat-bars). We read this as the MESI forced-writeback
                        read miss.
  one message on the bus at a time; requests queue in the arbiter (sec:scale-bus)

Assumptions added here (NOT in the report; all swept in sensitivity runs)
------------------------------------------------------------------------
  BUS_BW   = 8 B/cycle          bus data rate  -> 72 B data = 9 cycles
  ARB      = 1 cycle            arbitration per message
  T_UPG    = 10 cycles          upgrade / invalidate round trip
  MEM_OCC  = 10 cycles          memory port busy per 64 B access (read or write)
  OWN_OCC  = 10 cycles          owner cache port busy per block it supplies
  think    = mean compute cycles between a core's memory operations
                                (exponential, same draws for every protocol)
  Derived: cache-to-cache supply latency without a writeback
      L_C2C = T_COH - 9 = 51 cycles   (the 9-cycle writeback transfer removed)

Two readings of the forced writeback
------------------------------------
  serial  : the reader waits for the flush, i.e. dirty read costs T_COH = 60
            (this is what the report's T_COH implies)  <- default
  overlap : memory captures the flushed block while it travels to the reader,
            so the reader waits only L_C2C = 51; the writeback still occupies
            the bus (72 B) and the memory port. Reported as a sensitivity.

Resources (each is a single server, first-come first-served in time order)
  bus          occupancy per message = ceil(bytes/BUS_BW) + ARB
  memory port  MEM_OCC per memory read or write
  owner cache  OWN_OCC per block supplied cache-to-cache
Split-transaction idealisation: the bus is busy only while messages are on it,
not while memory is accessing; the reply slot is reserved with the request.
"""
import heapq
import math
import random
from dataclasses import dataclass, replace

import coherence_sim as cs


@dataclass(frozen=True)
class Params:
    T_L1: int = 1
    T_MEM: int = 100
    T_COH: int = 60            # serial MESI dirty read (report, eq:amat-coh)
    BUS_BW: int = 8
    ARB: int = 1
    T_UPG: int = 10
    MEM_OCC: int = 10
    OWN_OCC: int = 10
    wb_mode: str = "serial"    # "serial" | "overlap"

    @property
    def t_wb(self):            # data-transfer cycles of a 72 B message
        return math.ceil(cs.DATA / self.BUS_BW)

    @property
    def L_C2C(self):           # cache-to-cache latency with no writeback
        return self.T_COH - self.t_wb

    def msg(self, nbytes):     # bus occupancy of one message
        return math.ceil(nbytes / self.BUS_BW) + self.ARB


def split_streams(trace, N):
    streams = [[] for _ in range(N)]
    for core, addr, w in trace:
        streams[core].append((addr, w))
    return streams


def make_think(streams, mean, seed):
    """Per-core think-time draws; identical for every protocol."""
    out = []
    for c, s in enumerate(streams):
        r = random.Random(seed * 7919 + c)
        out.append([r.expovariate(1.0 / mean) if mean > 0 else 0.0 for _ in range(len(s) + 1)])
    return out


def run_timed(streams, thinks, protocol, N, cache_blocks, P):
    sim = cs.Sim(protocol, N, cache_blocks)
    heap = [(thinks[c][0], c) for c in range(N) if streams[c]]
    heapq.heapify(heap)
    idx = [0] * N
    finish = [0.0] * N
    bus_free = 0.0
    mem_free = 0.0
    own_free = [0.0] * N
    bus_busy = mem_busy = 0.0
    wait_sum = 0.0
    n_tx = 0
    op_time = 0.0                       # sum of per-operation memory time (for AMAT)
    n_ops = 0
    dirty_lat_sum = 0.0
    dirty_n = 0
    miss_lat_sum = 0.0
    miss_n = 0
    cm, mm = P.msg(cs.CTRL), P.msg(cs.DATA)

    while heap:
        t, c = heapq.heappop(heap)
        i = idx[c]
        addr, w = streams[c][i]
        sim.access(c, addr, w)
        kind = sim.ev_kind
        n_ops += 1
        if kind == "hit" and not sim.ev_evict:
            lat = P.T_L1
        else:
            if kind == "hit":
                lat = P.T_L1
                ready = t
            else:
                owner = sim.ev_owner
                if kind == "upg":
                    occ = cm
                elif sim.ev_fwb:
                    occ = cm + mm + mm              # request + writeback + data
                else:
                    occ = cm + mm                   # request + data
                g = max(t, bus_free)
                wait_sum += g - t
                n_tx += 1
                bus_free = g + occ
                bus_busy += occ
                if kind == "upg":
                    ready = g + P.T_UPG
                elif owner is None:                  # memory supplies
                    m = max(g, mem_free)
                    mem_free = m + P.MEM_OCC
                    mem_busy += P.MEM_OCC
                    ready = m + P.T_MEM
                else:                                # owner cache supplies
                    o = max(g, own_free[owner])
                    own_free[owner] = o + P.OWN_OCC
                    if sim.ev_fwb:                   # MSI/MESI: flush to memory as well
                        mw = max(o, mem_free)
                        mem_free = mw + P.MEM_OCC
                        mem_busy += P.MEM_OCC
                        if P.wb_mode == "serial":
                            ready = max(o + P.T_COH, mw + P.MEM_OCC)
                        else:
                            ready = o + P.L_C2C
                    else:
                        ready = o + P.L_C2C
                lat = P.T_L1 + (ready - t)
                miss_lat_sum += lat
                miss_n += 1
                if kind == "rmiss" and owner is not None:
                    dirty_lat_sum += lat
                    dirty_n += 1
            if sim.ev_evict:                         # posted writeback: bus + memory port, no stall
                g2 = max(t, bus_free)
                bus_free = g2 + mm
                bus_busy += mm
                m2 = max(g2, mem_free)
                mem_free = m2 + P.MEM_OCC
                mem_busy += P.MEM_OCC
        op_time += lat
        done = t + lat
        idx[c] = i + 1
        finish[c] = done
        if idx[c] < len(streams[c]):
            heapq.heappush(heap, (done + thinks[c][idx[c]], c))

    r = sim.finish()
    T = max(finish)
    r.update(T=T, T_mean=sum(finish) / N, AMAT=op_time / n_ops,
             bus_util=min(bus_busy / T, 1.0) if T else 0.0,
             mem_util=min(mem_busy / T, 1.0) if T else 0.0,
             bus_busy=bus_busy, avg_wait=(wait_sum / n_tx) if n_tx else 0.0,
             dirty_read_lat=(dirty_lat_sum / dirty_n) if dirty_n else float("nan"),
             miss_lat=(miss_lat_sum / miss_n) if miss_n else float("nan"))
    return r


# ---------------------------------------------------------------------------
# Validation against hand-computed, idle-system latencies
# ---------------------------------------------------------------------------
def validate_timing():
    P = Params()
    ok = True

    def row(name, got, want):
        nonlocal ok
        flag = "PASS" if abs(got - want) < 1e-9 else "FAIL"
        ok &= flag == "PASS"
        print(f"  {name:<52s} simulated {got:>7.1f}   expected {want:>7.1f}   {flag}")

    print("Idle-system latencies (cycles, include T_L1 = 1)")
    # Use the real event loop with a single op per core and long separation
    def real_latency(trace, N, protocol, P):
        # every op separated by big gaps -> run_timed bus/mem/owner never queue
        streams = [[] for _ in range(N)]
        times = []
        for k, (c, a, w) in enumerate(trace):
            streams[c].append((a, w))
        # build think arrays so op k starts at time k*big: assign gaps per core
        starts = {}
        th = [[] for _ in range(N)]
        last = [0.0] * N
        for k, (c, a, w) in enumerate(trace):
            t0 = k * 1_000_000.0
            th[c].append(t0 - last[c])
            last[c] = t0
        for c in range(N):
            th[c].append(0.0)
        r = run_timed(streams, th, protocol, N, None, P)
        return r

    # memory read miss
    r = real_latency([(0, 0, 0)], 2, "MESI", P)
    row("read miss served by memory", r["AMAT"], P.T_L1 + P.T_MEM)
    # upgrade: core0 reads (E) -> core1 reads (S,S) -> core1 writes = upgrade
    tr = [(0, 0, 0), (1, 0, 0), (1, 0, 1)]
    r = real_latency(tr, 2, "MESI", P)
    row("MESI: [mem miss, mem miss, upgrade] mean", r["AMAT"] * 3,
        (P.T_L1 + P.T_MEM) * 2 + P.T_L1 + P.T_UPG)
    # dirty read, MESI serial: core0 writes (write miss, memory), core1 reads dirty
    tr = [(0, 0, 1), (1, 0, 0)]
    r = real_latency(tr, 2, "MESI", P)
    row("MESI serial: write miss + dirty read (60+1)", r["AMAT"] * 2, (P.T_L1 + P.T_MEM) + (P.T_L1 + P.T_COH))
    r = real_latency(tr, 2, "MOESI", P)
    row("MOESI: write miss + dirty read (51+1)", r["AMAT"] * 2, (P.T_L1 + P.T_MEM) + (P.T_L1 + P.L_C2C))
    Po = replace(P, wb_mode="overlap")
    r = real_latency(tr, 2, "MESI", Po)
    row("MESI overlap: dirty read (51+1)", r["AMAT"] * 2, (P.T_L1 + P.T_MEM) + (P.T_L1 + P.L_C2C))
    # queueing: two cores miss at t=0 on different blocks -> the second waits one bus occupancy (12)
    streams = [[(0, 0)], [(1, 0)]]
    r = run_timed(streams, [[0.0, 0.0], [0.0, 0.0]], "MESI", 2, None, P)
    row("two simultaneous misses: mean latency (101+113)/2", r["AMAT"], (101 + 101 + P.msg(8) + P.msg(72)) / 2 + 0.0)
    row("two simultaneous misses: average bus wait per tx", r["avg_wait"], (0 + P.msg(8) + P.msg(72)) / 2)
    # sanity: derived constants
    row("derived L_C2C = T_COH - 9", P.L_C2C, 51)
    row("bus cycles: control / data message", P.msg(8) * 100 + P.msg(72), 2 * 100 + 10)

    # byte counts unchanged by the timing layer: bus busy cycles = sum over messages
    tr = [(0, 0, 1), (1, 0, 0)]
    r = real_latency(tr, 2, "MESI", P)
    exp_busy = (P.msg(8) + P.msg(72)) + (P.msg(8) + P.msg(72) + P.msg(72))   # write miss, dirty read
    row("MESI bus-busy cycles (12 + 22)", r["bus_busy"], exp_busy)
    r = real_latency(tr, 2, "MOESI", P)
    row("MOESI bus-busy cycles (12 + 12)", r["bus_busy"], 24)

    print("\nOverall:", "ALL TIMING CHECKS PASSED" if ok else "SOME TIMING CHECKS FAILED")
    return ok


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------
def _job(args):
    (tag, N, d, seed, pcw, cap, think, n_ops, Pdict) = args
    P = Params(**Pdict)
    tr = cs.gen_trace(N, n_ops, d, seed, pc_write_p=pcw)
    streams = split_streams(tr, N)
    th = make_think(streams, think, seed)
    out = []
    for p in ("MESI", "MOESI"):
        r = run_timed(streams, th, p, N, cap, P)
        r.update(tag=tag, d=d, seed=seed, pc_write_p=pcw, cap=cap or 0, think=think,
                 wb_mode=P.wb_mode, T_COH=P.T_COH, OWN_OCC=P.OWN_OCC, MEM_OCC=P.MEM_OCC)
        out.append(r)
    return out


def experiments(outdir="results", n_ops=30000):
    import os
    from multiprocessing import Pool
    os.makedirs(outdir, exist_ok=True)
    base = Params()
    over = replace(base, wb_mode="overlap")
    seeds = (1, 2, 3)
    jobs = []
    # E1  RQ2: load sweep. think time from idle to saturated, N = 8 and 16, both writeback readings
    thinks = (2000, 600, 300, 150, 80, 40, 20, 10, 5, 2)
    for P, mode in ((base, "serial"), (over, "overlap")):
        for N in (8, 16):
            for th in thinks:
                for s in seeds:
                    jobs.append(("E1", N, 0.5, s, 0.3, 1024, th, n_ops, P.__dict__))
    # E2  scaling with cores at a light and a heavy load
    for N in (2, 4, 8, 16):
        for th in (300, 40):
            for s in seeds:
                jobs.append(("E2", N, 0.5, s, 0.3, 1024, th, n_ops, base.__dict__))
    # E3  RQ4: cache capacity at moderate load, N = 8
    for cap in (4, 8, 16, 32, 64, 128, 256, 1024):
        for d in (0.2, 0.5, 0.8):
            for s in seeds:
                jobs.append(("E3", 8, d, s, 0.3, cap, 40, n_ops, base.__dict__))
    # E4  RQ4: latency sensitivity. T_COH sets cache-to-cache latency, OWN_OCC owner-port occupancy
    for tcoh in (30, 60, 100, 150, 200):
        for own in (5, 10, 20, 40):
            for s in seeds:
                P = replace(base, T_COH=tcoh, OWN_OCC=own)
                jobs.append(("E4", 8, 0.5, s, 0.3, 1024, 40, n_ops, P.__dict__))
    # E5  memory-port occupancy sensitivity (memory bandwidth)
    for mo in (5, 10, 20, 40):
        for s in seeds:
            P = replace(base, MEM_OCC=mo)
            jobs.append(("E5", 8, 0.5, s, 0.3, 1024, 40, n_ops, P.__dict__))
    with Pool(2) as pool:
        rows = [r for out in pool.map(_job, jobs, chunksize=3) for r in out]
    cs.write_csv(f"{outdir}/timing_all.csv", rows)
    return rows


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if cmd == "validate":
        sys.exit(0 if validate_timing() else 1)
    elif cmd == "run":
        experiments()
    else:
        print(__doc__)
