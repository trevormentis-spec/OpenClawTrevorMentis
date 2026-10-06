#!/usr/bin/env python3
"""Resilient byte-range chunk downloader for intermittently-503 CDN.

Normal HTTP GET / Range only. No auth bypass, no cookies beyond a referer.
Re-fetches a fresh get.php?key from the libgen ads page on repeated failure and
rotates gateway mirrors. Reconstructs the file from many small ranged chunks,
retrying each chunk patiently until the byte-range is served, then verifies the
final size (and md5 if provided).
"""
import argparse, hashlib, re, sys, time, os
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")
MIRRORS = ["https://libgen.li", "https://libgen.vg", "https://libgen.gl",
           "https://libgen.la", "https://libgen.bz"]
CDN_HOSTS = ["cdn3.booksdl.lc", "cdn1.booksdl.lc", "cdn2.booksdl.lc",
             "cdn.booksdl.lc", "cdn4.booksdl.lc"]


def fresh_get_url(md5, log):
    """Fetch ads.php from mirrors until we get a get.php?md5=..&key=.. link."""
    for m in MIRRORS:
        try:
            r = requests.get(f"{m}/ads.php?md5={md5}",
                             headers={"User-Agent": UA, "Referer": f"{m}/edition.php"},
                             timeout=30)
            m2 = re.search(r'(?:href=")?(?:/?)?(get\.php\?md5=%s&key=[A-Z0-9]+)' % md5, r.text)
            if m2:
                link = m2.group(1).lstrip("/")
                log(f"[key] {m} -> {link}")
                return link
            log(f"[key] {m} no link (http {r.status_code})")
        except Exception as e:
            log(f"[key] {m} err {e}")
        time.sleep(1)
    return None


def probe_total(get_link, log):
    """Try HEAD then a range GET to learn total size + a working cdn host."""
    for attempt in range(120):
        for host in CDN_HOSTS[:1] + CDN_HOSTS:
            url = f"https://{host}/{get_link}"
            try:
                r = requests.get(url, headers={"User-Agent": UA,
                                               "Referer": "https://libgen.li/",
                                               "Range": "bytes=0-0"},
                                 timeout=25, allow_redirects=True)
                if r.status_code in (200, 206):
                    cr = r.headers.get("Content-Range", "")
                    if "/" in cr:
                        total = int(cr.split("/")[-1])
                        log(f"[probe] {host} ok total={total}")
                        return host, total
                    cl = r.headers.get("Content-Length")
                    if cl:
                        log(f"[probe] {host} ok len={cl} (no content-range)")
                        return host, int(cl)
                else:
                    log(f"[probe] {host} http {r.status_code}")
            except Exception as e:
                log(f"[probe] {host} err {e}")
        time.sleep(3)
    return None, None


def download(md5, dest, expected_md5=None, chunk=1 << 20, log=print):
    if os.path.exists(dest):
        log(f"[dl] resuming existing {dest} ({os.path.getsize(dest)} bytes)")
    get_link = fresh_get_url(md5, log)
    if not get_link:
        log("[dl] FATAL: no get link")
        return False
    host, total = probe_total(get_link, log)
    if not total:
        log("[dl] FATAL: no total size")
        return False
    log(f"[dl] md5={md5} total={total} host={host}")

    pos = os.path.getsize(dest) if os.path.exists(dest) else 0
    if pos > total:
        log("[dl] local bigger than total; restarting")
        os.remove(dest); pos = 0

    failed = 0
    with open(dest, "r+b" if pos else "wb") as f:
        f.seek(pos)
        while pos < total:
            end = min(pos + chunk - 1, total - 1)
            got = False
            for attempt in range(80):
                url = f"https://{host}/{get_link}"
                status = 0
                try:
                    r = requests.get(url, headers={"User-Agent": UA,
                                                   "Referer": "https://libgen.li/",
                                                   "Range": f"bytes={pos}-{end}"},
                                     timeout=90, stream=True)
                    if r.status_code == 206:
                        data = r.content
                        if len(data) == end - pos + 1:
                            f.seek(pos); f.write(data); f.flush(); os.fsync(f.fileno())
                            pos += len(data); got = True
                            failed = 0
                            break
                        log(f"[chunk] short {len(data)}/{end-pos+1} @ {pos}")
                    elif r.status_code == 200:
                        # server ignored Range; use it only if covering whole file
                        data = r.content
                        log(f"[chunk] 200 @ {pos} len={len(data)} (range ignored)")
                        if pos == 0 and len(data) == total:
                            f.seek(0); f.write(data); f.flush(); pos = total; got = True
                            break
                    else:
                        status = r.status_code
                        log(f"[chunk] http {r.status_code} @ {pos}")
                except Exception as e:
                    log(f"[chunk] err {type(e).__name__} @ {pos}")
                time.sleep(2 if status == 503 else 3)
            if not got:
                failed += 1
                log(f"[dl] chunk failed after retries @ {pos}; refreshing key (fail#{failed})")
                time.sleep(5)
                ng = fresh_get_url(md5, log)
                if ng:
                    get_link = ng
                if failed >= 3:
                    log("[dl] too many chunk failures; aborting")
                    return False
            else:
                if pos % (5 << 20) < chunk:
                    log(f"[dl] progress {pos}/{total} ({100*pos//total}%)")

    size = os.path.getsize(dest)
    log(f"[dl] done size={size} expected={total}")
    if size != total:
        return False
    if expected_md5:
        h = hashlib.md5(open(dest, "rb").read()).hexdigest()
        log(f"[dl] md5={h} expected={expected_md5} " +
            ("MATCH" if h.lower() == expected_md5.lower() else "MISMATCH"))
        return h.lower() == expected_md5.lower()
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("md5")
    ap.add_argument("dest")
    ap.add_argument("--expect-md5", default=None)
    ap.add_argument("--chunk", type=int, default=1 << 20)
    a = ap.parse_args()
    ok = download(a.md5, a.dest, a.expect_md5, a.chunk)
    sys.exit(0 if ok else 1)
