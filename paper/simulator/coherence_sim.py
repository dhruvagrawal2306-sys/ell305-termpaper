#!/usr/bin/env python3
"""
coherence_sim.py -- trace-driven snooping cache-coherence simulator
ELL305 term paper: "Cache Coherence Overhead: MESI vs MOESI"

What it models
--------------
* N cores, each with a private write-back cache of 64-byte blocks
  (LRU, fully associative, capacity in blocks; None = unbounded).
* One snooping bus. Protocols: MSI, MESI, MOESI (write-invalidate).
* Memory traffic is *counted*, not timed. Byte costs follow the report's
  Table "Counting rules" (tab:counting-rules):
      control message (request, invalidate, upgrade)  8 B
      data message (block to a cache)                72 B  (64 + 8 header)
      writeback message                              72 B  (64 B reach memory)
      a bus broadcast is counted once.

Protocol rules (all three are write-invalidate)
-----------------------------------------------
Read miss
  MSI/MESI, remote M : owner flushes to memory, memory supplies
                       8 + 72 (writeback) + 72 (data) ; both -> S   <-- the
                       "forced writeback" (bytes_fwb counts its 72 B)
  MOESI,    remote M/O: owner supplies directly, 8 + 72; owner -> O
  otherwise          : memory supplies, 8 + 72; E holder -> S;
                       requester -> E (MESI/MOESI, no sharer) or S
Write hit
  M: nothing.  E: silent -> M.  S or O: upgrade (8 B), invalidate others -> M
Write miss
  owner (M/O) supplies directly, else memory supplies: 8 + 72 ; all other
  copies invalidated ; requester -> M.
  (ASSUMPTION: a dirty block is *transferred* on a write miss in all three
  protocols; no memory write is needed because the requester becomes the new
  dirty owner. This is not in the report's four sharing patterns, so it does
  not affect the validated numbers.)
Eviction
  M or O: writeback 72 B (64 B to memory).  S, E: silent.
End of run ("drain")
  every block still in M or O is written back once, so deferred writebacks
  are charged to the protocol that deferred them.

Checks (on by default in validation)
------------------------------------
  * at most one M/E/O copy per block; M or E implies no other copy
  * MESI never holds O, MSI never holds E or O
  * every valid copy carries the latest written version (data-value check)
  * if no cache holds the block dirty, memory holds the latest version

Usage
-----
  python3 coherence_sim.py validate     # reproduce the report's analytic numbers
  python3 coherence_sim.py sweep        # all experiments -> results/*.csv, *.png
"""
import sys
import csv
import os
import random
from collections import OrderedDict

CTRL, DATA, WB, BLOCK = 8, 72, 72, 64      # bytes (report Table 'Counting rules')

PROTOCOLS = ("MSI", "MESI", "MOESI")


class CoherenceError(AssertionError):
    pass


class Sim:
    def __init__(self, protocol, n_cores, cache_blocks=None, check=False):
        assert protocol in PROTOCOLS
        self.p = protocol
        self.has_E = protocol != "MSI"
        self.has_O = protocol == "MOESI"
        self.N = n_cores
        self.cap = cache_blocks
        self.check = check
        self.caches = [OrderedDict() for _ in range(n_cores)]  # addr -> [state, ver]
        self.holders = {}            # addr -> {core: line}
        self.latest = {}             # addr -> newest written version
        self.mem_ver = {}            # addr -> version in memory
        # counters
        self.bytes_total = 0         # interconnect bytes
        self.bytes_fwb = 0           # forced-writeback bytes (M->S flush on a remote read)
        self.mem_wr = 0              # bytes written to memory
        self.reads = self.writes = self.hits = 0
        self.read_miss = self.write_miss = self.upgrades = 0
        self.dirty_reads = 0         # read misses served by a cache holding the block dirty
        self.evict_wb = 0            # writebacks caused by capacity evictions
        self.drain_wb = 0

    # ------------------------------------------------------------------ helpers
    def _evict_if_full(self, core):
        c = self.caches[core]
        if self.cap is not None and len(c) >= self.cap:
            addr, line = c.popitem(last=False)          # LRU victim
            del self.holders[addr][core]
            if not self.holders[addr]:
                del self.holders[addr]
            if line[0] in ("M", "O"):
                self.bytes_total += WB
                self.mem_wr += BLOCK
                self.mem_ver[addr] = line[1]
                self.evict_wb += 1
                self.ev_evict = True
            if self.check:
                self._check(addr)

    def _install(self, core, addr, state, ver):
        self._evict_if_full(core)
        line = [state, ver]
        self.caches[core][addr] = line
        self.holders.setdefault(addr, {})[core] = line

    def _invalidate_others(self, addr, keep):
        h = self.holders.get(addr, {})
        for c in [c for c in h if c != keep]:
            del self.caches[c][addr]
            del h[c]

    def _check(self, addr):
        h = self.holders.get(addr, {})
        st = [l[0] for l in h.values()]
        lat = self.latest.get(addr, 0)
        if st.count("M") + st.count("E") + st.count("O") > 1:
            raise CoherenceError(f"two exclusive/owner copies of {addr}: {st}")
        if ("M" in st or "E" in st) and len(st) > 1:
            raise CoherenceError(f"M/E coexists with other copies of {addr}: {st}")
        if not self.has_O and "O" in st:
            raise CoherenceError("O state in a non-MOESI protocol")
        if not self.has_E and "E" in st:
            raise CoherenceError("E state in MSI")
        for l in h.values():
            if l[1] != lat:
                raise CoherenceError(f"stale copy of {addr}: has v{l[1]}, latest v{lat}")
        if not ("M" in st or "O" in st) and self.mem_ver.get(addr, 0) != lat:
            raise CoherenceError(f"memory stale for {addr} with no dirty owner")

    # ------------------------------------------------------------------ access
    def access(self, core, addr, is_write):
        # event record read by the timing layer (timing_sim.py); no effect on counters
        self.ev_kind = "hit"          # hit | rmiss | wmiss | upg
        self.ev_owner = None          # core that supplied the block (M/O holder), else None = memory
        self.ev_fwb = False           # a forced writeback (M->S flush) happened
        self.ev_evict = False         # a dirty victim was written back
        cache = self.caches[core]
        line = cache.get(addr)
        if is_write:
            self.writes += 1
            self._write(core, addr, line)
        else:
            self.reads += 1
            self._read(core, addr, line)
        if self.check:
            self._check(addr)

    def _read(self, core, addr, line):
        if line is not None:                       # M, E, S or O: read hit
            self.hits += 1
            self.caches[core].move_to_end(addr)
            return
        self.read_miss += 1
        self.ev_kind = "rmiss"
        others = self.holders.get(addr, {})
        dirty = None
        for c, l in others.items():
            if l[0] in ("M", "O"):
                dirty = l
                self.ev_owner = c
                break
        ver = self.latest.get(addr, 0)
        if dirty is not None:
            self.dirty_reads += 1
            if self.has_O:
                # owner supplies, keeps dirty ownership (M -> O)
                self.bytes_total += CTRL + DATA
                dirty[0] = "O"
            else:
                # MSI / MESI: forced writeback, then memory supplies
                self.bytes_total += CTRL + WB + DATA
                self.ev_fwb = True
                self.bytes_fwb += WB
                self.mem_wr += BLOCK
                self.mem_ver[addr] = dirty[1]
                dirty[0] = "S"
            new_state = "S"
        else:
            self.bytes_total += CTRL + DATA
            if others:
                for l in others.values():
                    if l[0] == "E":
                        l[0] = "S"
                new_state = "S"
            else:
                new_state = "E" if self.has_E else "S"
        self._install(core, addr, new_state, ver)

    def _write(self, core, addr, line):
        newver = self.latest.get(addr, 0) + 1
        if line is not None:
            self.hits += 1
            st = line[0]
            if st in ("S", "O"):
                self.upgrades += 1
                self.ev_kind = "upg"
                self.bytes_total += CTRL                 # upgrade / invalidate
                self._invalidate_others(addr, core)
            # M: nothing; E: silent upgrade
            line[0] = "M"
            line[1] = newver
            self.caches[core].move_to_end(addr)
        else:
            self.write_miss += 1
            self.ev_kind = "wmiss"
            for c, l in self.holders.get(addr, {}).items():
                if l[0] in ("M", "O"):
                    self.ev_owner = c                    # dirty owner supplies the block
                    break
            self.bytes_total += CTRL + DATA              # request + block
            self._invalidate_others(addr, core)
            self._install(core, addr, "M", newver)
        self.latest[addr] = newver

    # ------------------------------------------------------------------ end
    def finish(self):
        """Return counters; charge remaining dirty blocks as deferred writebacks."""
        nodrain = self.bytes_total
        nodrain_mem = self.mem_wr
        for core in range(self.N):
            for addr, l in self.caches[core].items():
                if l[0] in ("M", "O"):
                    self.bytes_total += WB
                    self.mem_wr += BLOCK
                    self.drain_wb += 1
        tx = self.read_miss + self.write_miss + self.upgrades
        return dict(
            protocol=self.p, N=self.N,
            ops=self.reads + self.writes,
            B_tot=self.bytes_total, B_tot_nodrain=nodrain,
            B_fwb=self.bytes_fwb,
            F=(self.bytes_fwb / self.bytes_total) if self.bytes_total else 0.0,
            mem_write_B=self.mem_wr, mem_write_B_nodrain=nodrain_mem,
            read_miss=self.read_miss, write_miss=self.write_miss, upgrades=self.upgrades,
            dirty_reads=self.dirty_reads, tx=tx,
            DSR=(self.dirty_reads / tx) if tx else 0.0,
            DSR_rm=(self.dirty_reads / self.read_miss) if self.read_miss else 0.0,
            hit_rate=(self.hits / (self.reads + self.writes)) if (self.reads + self.writes) else 0.0,
            evict_wb=self.evict_wb, drain_wb=self.drain_wb,
        )


def run(trace, protocol, n_cores, cache_blocks=None, check=False):
    s = Sim(protocol, n_cores, cache_blocks, check)
    acc = s.access
    for core, addr, w in trace:
        acc(core, addr, w)
    return s.finish()


# ---------------------------------------------------------------------------
# Micro-pattern traces (the report's sharing patterns)
# ---------------------------------------------------------------------------
def tr_private(): return [(0, 0, 0), (0, 0, 1)]          # read, write, (drain = evict)
def tr_readonly(K): return [(c, 0, 0) for c in range(K)]


def tr_prodcons(rounds, C):
    """producer = core 0 writes once per round, C consumers (cores 1..C) read."""
    t = []
    for _ in range(rounds):
        t.append((0, 0, 1))
        t += [(c, 0, 0) for c in range(1, C + 1)]
    return t


def tr_migratory(handoffs, N):
    """block migrates: core i reads, then writes, then core i+1 ..."""
    t = []
    for i in range(handoffs):
        c = i % N
        t += [(c, 0, 0), (c, 0, 1)]
    return t


def per_unit(trace_fn, units, protocol, ncores, **kw):
    """steady-state bytes per unit = B(units+1) - B(units), drain cancels."""
    a = run(trace_fn(units, **kw), protocol, ncores, check=True)["B_tot"]
    b = run(trace_fn(units + 1, **kw), protocol, ncores, check=True)["B_tot"]
    return b - a


def validate():
    ok = True

    def row(name, got, want):
        nonlocal ok
        flag = "PASS" if got == want else "FAIL"
        ok &= got == want
        print(f"  {name:<44s} simulated {got:>5}   report {want:>5}   {flag}")

    print("Sharing-pattern traffic per unit (report Table tab:traffic-patterns, C=1)")
    for p, priv, pc, mig in (("MSI", 160, 160, 160), ("MESI", 152, 160, 160), ("MOESI", 152, 88, 88)):
        row(f"{p:<5} private (read,write,evict)", run(tr_private(), p, 2, check=True)["B_tot"], priv)
        row(f"{p:<5} producer-consumer, per round", per_unit(tr_prodcons, 20, p, 2, C=1), pc)
        row(f"{p:<5} migratory, per hand-off", per_unit(tr_migratory, 20, p, 4, N=4), mig)
    for p in PROTOCOLS:
        row(f"{p:<5} read-only, per reader (8 readers/8)", run(tr_readonly(8), p, 8, check=True)["B_tot"] // 8, 80)

    print("\nProducer + C consumers per round: B(C) = 160+80(C-1) [MESI], 88+80(C-1) [MOESI]")
    for C in (1, 2, 4, 8, 15):
        row(f"MESI  C={C}", per_unit(tr_prodcons, 20, "MESI", C + 1, C=C), 160 + 80 * (C - 1))
        row(f"MOESI C={C}", per_unit(tr_prodcons, 20, "MOESI", C + 1, C=C), 88 + 80 * (C - 1))

    # forced-writeback fraction of the producer-consumer model: 72 / B(C)
    print("\nForced-writeback fraction F = 72/B(C) for MESI (report eq. for F(C))")
    for C in (1, 2, 4, 8, 15):
        r_a = run(tr_prodcons(40, C), "MESI", C + 1)
        want = 72 / (160 + 80 * (C - 1))
        print(f"  C={C:<2d} simulated F (40 rounds, incl. cold start) = {r_a['F']:.4f}   steady-state 72/B(C) = {want:.4f}")

    print("\nOverall:", "ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    return ok


# ---------------------------------------------------------------------------
# Synthetic workload generator (mix of the four sharing patterns)
# ---------------------------------------------------------------------------
def gen_trace(N, n_ops, d, seed, pc_write_p=0.3, priv_blocks=96, n_pc=24, n_mig=12, n_ro=24):
    """
    d  : share of operations that belong to the dirty-sharing patterns
         (producer-consumer + migratory); the rest are private and read-only.
    pc_write_p : probability that an access to a producer-consumer block is the
         producer's write (otherwise a random consumer reads).
    Address space: [0, N*priv_blocks) private, then pc, mig, ro pools.
    """
    rnd = random.Random(seed)
    base_pc = N * priv_blocks
    base_mig = base_pc + n_pc
    base_ro = base_mig + n_mig
    w = {"priv": (1 - d) / 2, "ro": (1 - d) / 2, "pc": d / 2, "mig": d / 2}
    kinds, weights = zip(*w.items())
    last_mig = {}
    trace = []
    while len(trace) < n_ops:
        k = rnd.choices(kinds, weights)[0]
        if k == "priv":
            c = rnd.randrange(N)
            a = c * priv_blocks + rnd.randrange(priv_blocks)
            trace.append((c, a, 1 if rnd.random() < 0.3 else 0))
        elif k == "ro":
            trace.append((rnd.randrange(N), base_ro + rnd.randrange(n_ro), 0))
        elif k == "pc":
            b = rnd.randrange(n_pc)
            prod = b % N
            if rnd.random() < pc_write_p:
                trace.append((prod, base_pc + b, 1))
            else:
                c = rnd.randrange(N - 1)
                c = c + 1 if c >= prod else c            # any core except the producer
                trace.append((c, base_pc + b, 0))
        else:                                            # migratory: a new core reads, then writes
            b = rnd.randrange(n_mig)
            prev = last_mig.get(b, -1)
            c = rnd.randrange(N - 1)
            c = c + 1 if c >= prev and prev >= 0 else c
            last_mig[b] = c
            trace.append((c, base_mig + b, 0))
            trace.append((c, base_mig + b, 1))
    return trace[:n_ops]


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------
def _job(args):
    (N, d, seed, pcw, cap, n_ops) = args
    tr = gen_trace(N, n_ops, d, seed, pc_write_p=pcw)
    out = []
    for p in PROTOCOLS:
        r = run(tr, p, N, cache_blocks=cap)
        r.update(d=d, seed=seed, pc_write_p=pcw, cap=cap if cap else 0)
        out.append(r)
    return out


def write_csv(path, rows):
    keys = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(rows)


def sweep(outdir="results", n_ops=60000):
    from multiprocessing import Pool
    os.makedirs(outdir, exist_ok=True)
    Ns = (2, 4, 8, 16)
    ds = [0.0, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]
    seeds = (1, 2, 3)
    pcws = (0.15, 0.3, 0.5)
    # (E1) main sweep: unbounded-ish cache (1024 blocks = 64 KB) so capacity does not interfere
    jobs = [(N, d, s, pw, 1024, n_ops) for N in Ns for d in ds for s in seeds for pw in pcws]
    # (E2) cache-size sweep for RQ4: fixed mix, N=8
    caps = (4, 8, 16, 32, 64, 128, 256, 1024)
    jobs2 = [(8, d, s, 0.3, c, n_ops) for d in (0.2, 0.5, 0.8) for s in seeds for c in caps]
    with Pool(2) as pool:
        r1 = [r for out in pool.map(_job, jobs, chunksize=4) for r in out]
        r2 = [r for out in pool.map(_job, jobs2, chunksize=4) for r in out]
    write_csv(os.path.join(outdir, "sweep_main.csv"), r1)
    write_csv(os.path.join(outdir, "sweep_cachesize.csv"), r2)
    return r1, r2


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if cmd == "validate":
        sys.exit(0 if validate() else 1)
    elif cmd == "sweep":
        sweep()
    else:
        print(__doc__)
