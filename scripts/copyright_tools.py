#!/usr/bin/env python3
"""
Copyright Monitoring — PoC local tooling.

Two jobs, both local:
  1) fetch   : download an openly-accessible URL into a sandbox dir, identify
               the file by *content* (not filename), extract metadata/text.
  2) state   : per-work URL history so repeat checks can report
               new / still-online / disappeared / url-changed.

Safety: normal HTTP GET only. No auth, no cookies, no paywall/CAPTCHA/access
-control bypass. Webpage/document text is treated as data, never instructions.
Sandbox lives under tmp/copyright-monitor (gitignored).
"""
import argparse, hashlib, json, os, re, subprocess, sys, time, zipfile
from datetime import datetime, timezone
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
SANDBOX = WS / "tmp" / "copyright-monitor"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")


def slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:80] or "work"


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd, **kw):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120, **kw)
        return p.stdout.strip()
    except Exception as e:
        return f"<error: {e}>"


# ---------------------------------------------------------------- fetch
def fetch(url: str, work: str) -> dict:
    outdir = SANDBOX / slug(work)
    outdir.mkdir(parents=True, exist_ok=True)
    # derive candidate filename
    base = os.path.basename(url.split("?")[0]) or "download.bin"
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)[:120]
    dest = outdir / base
    if dest.exists():
        dest = outdir / f"{int(time.time())}-{base}"

    hdr_dump = run(["curl", "-sIL", "-A", UA, "--max-time", "30", url])
    cd = ""
    for line in hdr_dump.splitlines():
        if line.lower().startswith("content-disposition"):
            cd = line
    cp = subprocess.run(
        ["curl", "-sL", "-A", UA, "--max-time", "90", "--max-filesize",
         "60000000", "-o", str(dest), "-w",
         "%{http_code}\x1f%{content_type}\x1f%{size_download}\x1f%{url_effective}", url],
        capture_output=True, text=True)
    parts = cp.stdout.split("\x1f")
    code = parts[0] if parts else "?"
    ctype = parts[1] if len(parts) > 1 else "?"
    size = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    final_url = parts[3] if len(parts) > 3 else url

    info = {
        "requested_url": url, "final_url": final_url, "http_status": code,
        "content_type_header": ctype, "bytes": size,
        "content_disposition": cd.strip(), "saved_as": str(dest),
        "fetched_at": now(),
    }
    if not dest.exists() or size == 0:
        info["verdict"] = "empty_or_blocked"
        return info

    info["sha256"] = hashlib.sha256(dest.read_bytes()).hexdigest()
    info["file_cmd"] = run(["file", "-b", str(dest)])

    low = str(dest).lower()
    if "pdf" in info["file_cmd"].lower() or low.endswith(".pdf"):
        info.update(inspect_pdf(dest))
    elif "epub" in info["file_cmd"].lower() or low.endswith(".epub") or zipfile.is_zipfile(dest):
        info.update(inspect_epub(dest))
    elif "text" in info["file_cmd"].lower():
        try:
            txt = dest.read_text(errors="replace")[:3000]
            info["text_head"] = txt
            info["verdict"] = "text_document"
        except Exception:
            pass
    return info


def inspect_pdf(p: Path) -> dict:
    meta = run(["pdfinfo", str(p)])
    d = {"pdfinfo": meta}
    for line in meta.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip().lower()
            if k in ("title", "author", "subject", "keywords", "pages", "creator", "producer", "creationdate"):
                d[f"pdf_{k}"] = v.strip()
    try:
        d["pages_int"] = int(d.get("pdf_pages", "0"))
    except ValueError:
        d["pages_int"] = 0
    txt = run(["pdftotext", "-l", "5", "-q", str(p), "-"])
    d["text_chars_sampled"] = len(txt)
    d["text_head"] = (txt or "")[:3000]
    d["verdict"] = "pdf_inspected"
    return d


def inspect_epub(p: Path) -> dict:
    d = {}
    try:
        with zipfile.ZipFile(p) as z:
            names = z.namelist()
            d["zip_entries"] = len(names)
            opf = [n for n in names if n.lower().endswith(".opf")]
            if opf:
                raw = z.read(opf[0]).decode("utf-8", "replace")
                d["opf_path"] = opf[0]
                for tag, key in (("title", "epub_title"), ("creator", "epub_creator"),
                                 ("publisher", "epub_publisher"), ("language", "epub_language"),
                                 ("identifier", "epub_identifier")):
                    m = re.search(rf"<dc:{tag}[^>]*>(.*?)</dc:{tag}>", raw, re.S)
                    if m:
                        d[key] = re.sub(r"\s+", " ", m.group(1)).strip()
            d["sample_entries"] = names[:25]
        d["verdict"] = "epub_inspected"
    except Exception as e:
        d["verdict"] = f"zip_error: {e}"
    return d


# ---------------------------------------------------------------- state
def state_path(work: str) -> Path:
    p = SANDBOX / slug(work) / "state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_state(work: str) -> dict:
    p = state_path(work)
    if p.exists():
        return json.loads(p.read_text())
    return {"work": work, "first_run": now(), "urls": {}}


def save_state(work: str, st: dict):
    state_path(work).write_text(json.dumps(st, indent=2))


def state_record(work: str, url: str, status: str, note: str = ""):
    st = load_state(work)
    st.setdefault("urls", {})
    rec = st["urls"].get(url, {"first_seen": now()})
    rec["last_seen"] = now()
    rec["status"] = status
    if note:
        rec["note"] = note
    st["urls"][url] = rec
    st["last_run"] = now()
    save_state(work, st)


def state_diff(work: str, current_urls, statuses=None):
    """Compare current run URLs against stored history."""
    st = load_state(work)
    prev = set(st.get("urls", {}).keys())
    cur = set(current_urls)
    return {
        "new": sorted(cur - prev),
        "still_online": sorted(cur & prev),
        "disappeared": sorted(prev - cur),
    }


# ---------------------------------------------------------------- cli
def main():
    ap = argparse.ArgumentParser(description="copyright monitor PoC tools")
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch")
    f.add_argument("url")
    f.add_argument("--work", required=True)

    s = sub.add_parser("state")
    s.add_argument("--work", required=True)
    s.add_argument("--record", nargs=2, metavar=("URL", "STATUS"))
    s.add_argument("--note", default="")

    d = sub.add_parser("diff")
    d.add_argument("--work", required=True)
    d.add_argument("urls", nargs="*")

    g = sub.add_parser("get")
    g.add_argument("--work", required=True)

    a = ap.parse_args()
    if a.cmd == "fetch":
        print(json.dumps(fetch(a.url, a.work), indent=2))
    elif a.cmd == "state":
        if a.record:
            state_record(a.work, a.record[0], a.record[1], a.note)
        print(json.dumps(load_state(a.work), indent=2))
    elif a.cmd == "diff":
        print(json.dumps(state_diff(a.work, a.urls), indent=2))
    elif a.cmd == "get":
        print(json.dumps(load_state(a.work), indent=2))


if __name__ == "__main__":
    main()
