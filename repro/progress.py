"""Progress reporting for long runs. A background thread prints a status line every `every` seconds
(default 600 s = 10 min) even when no task has finished in between, so you can see the job is alive.
Usage:  from progress import run_pool
        res = run_pool(pool, fn, items, "label")      # drop-in for pool.map when result ORDER does not matter
Run scripts with `py -3.11 -u ...` (unbuffered) or redirect with `| Tee-Object log.txt`."""
import time, threading, os


class Heartbeat:
    def __init__(self, total, label="", every=600):
        self.total, self.label, self.every = total, label, every
        self.done = 0; self.t0 = time.time(); self._stop = threading.Event(); self._lock = threading.Lock()
        print("[%s] start: %d tasks, status every %d s (pid %d)" % (label, total, every, os.getpid()), flush=True)
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while not self._stop.wait(self.every):
            self.report()

    def tick(self, n=1):
        with self._lock:
            self.done += n

    def report(self, final=False):
        el = time.time() - self.t0
        d = max(self.done, 0); rate = d / el if el > 0 else 0.0
        eta = (self.total - d) / rate if rate > 0 else float("nan")
        print("[%s]%s %d/%d (%.1f%%) elapsed %.1f min, ETA %s" % (
            self.label, " DONE" if final else "", d, self.total, 100.0 * d / max(self.total, 1), el / 60,
            "%.1f min" % (eta / 60) if eta == eta else "n/a"), flush=True)

    def close(self):
        self._stop.set(); self.report(final=True)


def run_pool(pool, fn, items, label, every=600, chunksize=1):
    items = list(items); hb = Heartbeat(len(items), label, every); out = []
    try:
        for r in pool.imap_unordered(fn, items, chunksize=chunksize):
            out.append(r); hb.tick()
    finally:
        hb.close()
    return out
