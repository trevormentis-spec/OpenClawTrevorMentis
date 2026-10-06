#!/usr/bin/env python3
"""Long-running gentle harvester for a flaky CDN (byte-range reconstruction).

Normal HTTP GET / Range only. No auth/paywall/CAPTCHA/login bypass.
Progress persists in a sidecar bitmap (dest + '.chunks') so it can survive
restarts and run for hours. Refreshes the libgen get.php key on failures.
Writes verified on completion (size + md5).
"""
import argparse, hashlib, os, re, sys, threading, time, json
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")
MIRRORS = ["https://libgen.li", "https://libgen.vg", "https://libgen.gl",
           "https://libgen.la", "https://libgen.bz"]
HOST = "cdn3.booksdl.lc"


def log(*a):
    print(f"{time.strftime('%H:%M:%S')}", *a, flush=True)


class Key:
    def __init__(self, md5):
        self.md5 = md5; self.lock = threading.Lock(); self.link = None
        self.renew_lock = threading.Lock(); self.last_renew = 0
    def renew(self, force=False):
        with self.renew_lock:
            if not force and time.time() - self.last_renew < 25:
                return True
            self.last_renew = time.time()
            for m in MIRRORS:
                try:
                    r = requests.get(f"{m}/ads.php?md5={self.md5}",
                                     headers={"User-Agent": UA, "Referer": f"{m}/edition.php"},
                                     timeout=30)
                    mm = re.search(r'(?:href=")?(?:/?)?(get\.php\?md5=%s&key=[A-Z0-9]+)' % self.md5, r.text)
                    if mm:
                        with self.lock:
                            self.link = mm.group(1).lstrip("/")
                        log("[key]", m, "->", self.link)
                        return True
                except Exception as e:
                    log("[key] err", m, e)
                time.sleep(1)
        return False

    def get(self):
        with self.lock:
            return self.link


def probe_total(md5, key):
    for _ in range(1000):
        url = f"https://{HOST}/{key.get()}"
        try:
            r = requests.get(url, headers={"User-Agent": UA, "Referer": "https://libgen.li/",
                                           "Range": "bytes=0-0"}, timeout=15)
            if r.status_code in (200, 206):
                cr = r.headers.get("Content-Range", "")
                if "/" in cr:
                    return int(cr.split("/")[-1])
                if r.headers.get("Content-Length"):
                    return int(r.headers["Content-Length"])
            else:
                log("[probe] http", r.status_code)
        except Exception as e:
            log("[probe] err", type(e).__name__)
        time.sleep(2)
    return None


def download(md5, dest, expected_md5, chunk, workers, total=None):
    key = Key(md5); key.renew()
    if not total:
        total = probe_total(md5, key)
    if not total:
        log("FATAL no total"); return False
    nchunks = (total + chunk - 1) // chunk
    bmp_path = dest + ".chunks"
    if os.path.exists(bmp_path):
        bmp = bytearray(open(bmp_path, "rb").read())
        if len(bmp) != nchunks:
            bmp = bytearray(nchunks)
        else:
            for i in range(nchunks):
                if bmp[i] != 1:
                    bmp[i] = 0  # claims (2) become missing again
    else:
        bmp = bytearray(nchunks)
    if not os.path.exists(dest) or os.path.getsize(dest) != total:
        with open(dest, "wb") as f:
            f.truncate(total)
    log(f"[dl] total={total} chunk={chunk} nchunks={nchunks} done={sum(bmp)} workers={workers}")

    lock = threading.Lock()
    stop = threading.Event()
    stats = {"206": 0, "200": 0, "err": 0, "written": 0}
    t0 = time.time()

    def save_bmp():
        snap = bytes(1 if b == 1 else 0 for b in bmp)
        tmp = bmp_path + ".tmp"
        open(tmp, "wb").write(snap)
        os.replace(tmp, bmp_path)

    def worker(wid):
        fails = 0
        while not stop.is_set():
            with lock:
                try:
                    idx = next(i for i in range(nchunks) if bmp[i] == 0)
                except StopIteration:
                    stop.set(); return
                bmp[idx] = 2  # claim
            s = idx * chunk
            end = min(s + chunk - 1, total - 1)
            cur = s
            ok = False
            attempts = 0
            while cur <= end and not stop.is_set():
                attempts += 1
                url = f"https://{HOST}/{key.get()}"
                try:
                    r = requests.get(url, headers={"User-Agent": UA,
                                                   "Referer": "https://libgen.li/",
                                                   "Range": f"bytes={cur}-{end}"},
                                     timeout=(3, 5))
                    if r.status_code == 206 and r.content:
                        data = r.content
                        n = min(len(data), end - cur + 1)
                        with open(dest, "r+b") as f:
                            f.seek(cur); f.write(data[:n]); f.flush()
                        cur += n
                        with lock:
                            stats["206"] += 1; stats["written"] += n
                        fails = 0
                        if cur > end:
                            ok = True
                        continue
                    elif r.status_code == 200 and r.content:
                        data = r.content
                        with lock:
                            stats["200"] += 1
                        if len(data) == total and cur == 0:
                            with open(dest, "r+b") as f:
                                f.seek(0); f.write(data); f.flush()
                            for j in range(nchunks): bmp[j] = 1
                            ok = True; break
                        # otherwise unusable
                except Exception:
                    with lock:
                        stats["err"] += 1
                fails += 1
                if fails % 100 == 0:
                    key.renew()
                time.sleep(1.0 if fails < 5 else 2.0)
            if not ok:
                with lock:
                    if bmp[idx] != 1:
                        bmp[idx] = 0  # unclaim for retry
                log(f"[w{wid}] gave up chunk {idx} after {attempts} attempts")
                stop.set()
                return
            else:
                with lock:
                    bmp[idx] = 1  # completed
                    done = sum(1 for b in bmp if b == 1)
                if done % 8 == 0:
                    save_bmp()
                    log(f"[dl] {done}/{nchunks} chunks ({100*done//nchunks}%) stats={stats}")

    ths = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(workers)]
    for t in ths: t.start()
    while any(t.is_alive() for t in ths):
        time.sleep(10)
        with lock:
            done = sum(1 for b in bmp if b == 1)
        log(f"[hb] done={done}/{nchunks} stats={stats} elapsed={time.time()-t0:.0f}s")
    with lock:
        save_bmp()
        done = sum(1 for b in bmp if b == 1)
    if done != nchunks:
        log(f"[dl] incomplete {done}/{nchunks}"); return False
    size = os.path.getsize(dest)
    if size != total:
        log(f"[dl] BAD size {size}/{total}"); return False
    h = hashlib.md5(open(dest, "rb").read()).hexdigest()
    log(f"[dl] FINAL md5={h} expected={expected_md5}")
    if expected_md5 and h.lower() != expected_md5.lower():
        log("[dl] MD5 MISMATCH"); return False
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("md5"); ap.add_argument("dest")
    ap.add_argument("--expect-md5", default=None)
    ap.add_argument("--chunk", type=int, default=256 * 1024)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--total", type=int, default=None)
    a = ap.parse_args()
    sys.exit(0 if download(a.md5, a.dest, a.expect_md5, a.chunk, a.workers, a.total) else 1)
