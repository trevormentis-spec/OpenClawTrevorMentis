#!/usr/bin/env python3
"""Parallel ranged-chunk reconstruction for a flaky CDN.

Normal HTTP GET with Range headers only. No auth/paywall bypass.
Splits the file into many small byte ranges and fetches them concurrently with
patient retries, writing each completed range at its offset into a sparse file.
Refreshes the libgen get.php key periodically. Verifies final md5.
"""
import argparse, hashlib, os, re, sys, threading, time
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")
MIRRORS = ["https://libgen.li", "https://libgen.vg", "https://libgen.gl",
           "https://libgen.la", "https://libgen.bz"]
HOST = "cdn3.booksdl.lc"


class Key:
    def __init__(self, md5, log):
        self.md5 = md5; self.log = log; self.lock = threading.Lock()
        self.link = None; self.renew()

    def renew(self):
        for m in MIRRORS:
            try:
                r = requests.get(f"{m}/ads.php?md5={self.md5}",
                                 headers={"User-Agent": UA, "Referer": f"{m}/edition.php"},
                                 timeout=30)
                mm = re.search(r'(?:href=")?(?:/?)?(get\.php\?md5=%s&key=[A-Z0-9]+)' % self.md5, r.text)
                if mm:
                    with self.lock:
                        self.link = mm.group(1).lstrip("/")
                    self.log(f"[key] {m} -> {self.link}")
                    return True
            except Exception as e:
                self.log(f"[key] {m} err {e}")
            time.sleep(1)
        return False

    def get(self):
        with self.lock:
            return self.link


def probe_total(dlurl, log):
    for _ in range(200):
        try:
            r = requests.get(dlurl, headers={"User-Agent": UA, "Referer": "https://libgen.li/",
                                             "Range": "bytes=0-0"}, timeout=20)
            if r.status_code in (200, 206):
                cr = r.headers.get("Content-Range", "")
                if "/" in cr:
                    return int(cr.split("/")[-1])
                cl = r.headers.get("Content-Length")
                if cl:
                    return int(cl)
            else:
                log(f"[probe] http {r.status_code}")
        except Exception as e:
            log(f"[probe] err {e}")
        time.sleep(2)
    return None


def download(md5, dest, expected_md5, chunk, workers, log):
    key = Key(md5, log)
    dlurl = f"https://{HOST}/{key.get()}"
    total = probe_total(dlurl, log)
    if not total:
        log("FATAL no total"); return False
    log(f"[dl] total={total} chunk={chunk} workers={workers}")

    if os.path.exists(dest) and os.path.getsize(dest) != total:
        os.remove(dest)
    if not os.path.exists(dest):
        with open(dest, "wb") as f:
            f.truncate(total)

    ranges = [(s, min(s + chunk - 1, total - 1)) for s in range(0, total, chunk)]
    done = [False] * len(ranges)
    # mark any already-filled ranges (from prior partial file: check via non-zero? skipped)
    lock = threading.Lock()
    stop = threading.Event()
    completed_bytes = [0]

    def worker(wid):
        while not stop.is_set():
            with lock:
                try:
                    idx = done.index(False)
                except ValueError:
                    return
                done[idx] = True  # claim
                s, e = ranges[idx]
            got = False
            attempts = 0
            while not got and attempts < 200 and not stop.is_set():
                attempts += 1
                url = f"https://{HOST}/{key.get()}"
                try:
                    r = requests.get(url, headers={"User-Agent": UA,
                                                   "Referer": "https://libgen.li/",
                                                   "Range": f"bytes={s}-{e}"},
                                     timeout=25)
                    if r.status_code == 206:
                        data = r.content
                        if 0 < len(data) <= e - s + 1:
                            # if short, write what we have and shrink the range
                            with open(dest, "r+b") as f:
                                f.seek(s); f.write(data); f.flush()
                            if len(data) == e - s + 1:
                                got = True
                            else:
                                s = s + len(data)   # continue remaining part
                            with lock:
                                completed_bytes[0] += len(data)
                                if completed_bytes[0] % (2 << 20) < chunk:
                                    log(f"[dl] ~{completed_bytes[0]//1024} KiB delivered (w{wid})")
                    elif r.status_code == 200:
                        data = r.content
                        if len(data) == total and s == 0:
                            with open(dest, "r+b") as f:
                                f.seek(0); f.write(data); f.flush()
                            got = True
                    # else 5xx -> retry
                except Exception:
                    pass
                if not got and attempts % 45 == 0:
                    key.renew()
                time.sleep(1.5 if attempts % 3 else 3)
            if not got:
                log(f"[dl] GIVE UP range {s}-{e} (w{wid})")
                stop.set()
                return

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(workers)]
    t0 = time.time()
    for t in threads: t.start()
    for t in threads: t.join()
    log(f"[dl] elapsed {time.time()-t0:.0f}s")

    size = os.path.getsize(dest)
    if size != total:
        log(f"[dl] BAD size {size}/{total}"); return False
    h = hashlib.md5(open(dest, "rb").read()).hexdigest()
    log(f"[dl] md5={h} expected={expected_md5} " +
        ("MATCH" if expected_md5 and h.lower() == expected_md5.lower() else "MISMATCH/none"))
    return (not expected_md5) or h.lower() == expected_md5.lower()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("md5"); ap.add_argument("dest")
    ap.add_argument("--expect-md5", default=None)
    ap.add_argument("--chunk", type=int, default=128 * 1024)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    sys.exit(0 if download(a.md5, a.dest, a.expect_md5, a.chunk, a.workers, print) else 1)
