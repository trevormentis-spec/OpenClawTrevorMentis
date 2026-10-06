# ACQUISITION / COPYRIGHT PROBE — RESULTS

**6 works submitted by Roderick | run 2026-09-17 | Trevor**

Method: located freely-accessible copies across Internet Archive (advancedsearch +
metadata + file listing; BookReader search-inside), Open Library (search + editions +
`search/inside`), HathiTrust Bib API (`catalog.hathitrust.org/api/volumes/...`),
Google Books (`viewapi`; the JSON API was over quota — HTTP 429), Gallica SRU
(`gallica.bnf.fr/SRU`), libgen mirrors (`.li/.la/.vg/.bz/.gl`), Anna's Archive
(`.li/.gl`), and the open web (Brave/DDG). Every located copy was **downloaded and
verified by content** — PDF via `pdfinfo`/`pdftotext`, image-only scans via
`tesseract` OCR of the title page, EPUB/OPF only where applicable. **Normal HTTP GET
only: no paywall, login, cookies, CAPTCHA, lending, or print-disabled bypass.**
Internet Archive items flagged `access-restricted-item:true`
(`inlibrary`/`printdisabled`) were treated as off-limits; their text derivatives
confirmed withheld (`_djvu.txt` → HTTP 401/403). Sandbox per work:
`tmp/copyright-monitor/<slug>/`. Delivered files: `exports/acq-2026-09-17/`.

Verification is by **content**, not filename: title page / copyright page OCR, page
counts, and (where a text layer exists) targeted full-text checks.

---

## A. VERIFIED FREE / OPENLY-ACCESSIBLE COPIES LOCATED (content-verified)

**2. Philippe de Commynes — *Mémoires*, tomes I & II, ed. Joseph Calmette with
G. Durville (Honoré Champion, 1924–1925)** — ✅ **2 files**
- Internet Archive items `commynesmemoirescalm1` (Tome I, 1464–1474) and
  `commynesmemoirescalm2` (Tome II, 1474–1483); collection `arlima` +
  `patron-library-collection`, **not** access-restricted. Full scan PDFs
  (212 MB / 254 MB; Google-digitised Univ. of Wisconsin copies).
- Verified (Tome I, `pdftoppm`+`tesseract` OCR of title page): “**PHILIPPE DE
  COMMYNES — MEMOIRES — EDITES PAR JOSEPH CALMETTE … avec la collaboration du
  CHANOINE G. DURVILLE**”, series “Les Classiques de l’Histoire de France au Moyen
  Âge, … Fascicule 3”; verso “**Copyright by Edouard Champion, April 1924**”.
  `pdfinfo`: 316 pp. Tome II title page: “**TOME II (1474-1483) — PARIS, LIBRAIRIE
  ANCIENNE HONORÉ CHAMPION, EDITEUR**”, Fascicule 5; `pdfinfo`: 378 pp.
- ⚠️ Edition note: the queue said “les Belles Lettres”; the **Calmette/Durville
  edition was actually published by Honoré Champion** (Halphen’s *Classiques de
  l’histoire de France au Moyen Âge*). The IA set also holds **Tome III** (1484–1498)
  if wanted.
- `exports/acq-2026-09-17/Commynes - Memoires t.1 (Calmette, Champion 1924).pdf`
  (md5 `e8b6cbf852d903a260c99688e38e3aac`)
- `exports/acq-2026-09-17/Commynes - Memoires t.2 (Calmette, Champion 1925).pdf`
  (md5 `d5658dc39d7ab2fd3d5b3bea06ddcb93`)

**3. Georges Chastellain — *Œuvres*, ed. Kervyn de Lettenhove (1863–66) — the
**spider** ballade volume** — ✅ **file**
- Internet Archive items `oeuvrespubparleb01chasuoft` … `oeuvrespubparleb08chasuoft`
  (the complete 8-volume set; coll. `robarts`/`university_of_toronto`,
  `possible-copyright-status: NOT_IN_COPYRIGHT`). All 8 volumes are freely
  downloadable (~20–26 MB each).
- **Volume established: the 1467 “spider” (Louis XI = *l’universelle araigne*)
  material is in TOME VII** (“Le Lyon rampant” / Œuvres diverses). Verified by
  content: title-page OCR reads “**OEUVRES DE GEORGES CHASTELLAIN … TOME
  SEPTIEME**”; the volume text layer contains the ballade “*Lyon rampant en
  crouppe de montaigue … Lyon fameux, tryacle contre **araigne***” and “*Ay
  combattu l’**universel araigne***”, plus Lettenhove’s note placing the cycle in
  “**1467 et … 1468**”. Printed pp. ~206–214 (PDF pp. 230–236). The editor
  attributes the “Lyon rampant” ballade to Chastellain and the following
  “Souffle, Triton …” ballade to Molinet.
- `exports/acq-2026-09-17/Chastellain - Oeuvres t.7 (Lettenhove 1863-66).pdf`
  (516 pp; md5 `3347c4497ab4f1efc81ff0e17555d0fd`)
- (The whole 8-vol set remains downloadable from IA if the others are wanted.)

---

## B. LOCATED (content-identified) — DOWNLOAD STILL BLOCKED BY CDN

**5. Walter Bagehot — *The English Constitution*, ed. Paul Smith (Cambridge UP, 2001)**
- **libgen.li edition 138501916** = “The English Constitution (Cambridge Texts in
  the History of Political Thought)”, ISBN **0521469422 / 9780521469425** — i.e.
  **exactly the Smith/CUP paginated edition**. md5
  `9cfe2e9f17dbcec277116131364b191e`.
- Download path `libgen.li/get.php` → **307 → `cdn3.booksdl.lc`**, which returned
  **503** on every attempt (all `.li/.la/.vg/.bz/.gl` mirrors redirect to the same
  CDN; `cdn2/cdn4/cdn5` return “not possible to define a repository folder”).
  Same CDN failure as the 2026-09-16 batch. **Not acquired.**
- Alternate leads (none is a free full paginated scan): the IA item
  `englishconstitut0000bage_j6q3` (2001) is an **Oxford UP** edition (ISBN
  0192839756), **not** the Paul-Smith/Cambridge edition, and is lending-restricted
  anyway. Google Books has the CUP/Smith edition (vol id `A0-zcw0XYbYC`) at
  **“partial” preview, `can_download_pdf:false`, `can_download_epub:false`**; CUP’s
  own site offers **front matter only**; Amazon/Scribd are paid. Anna’s Archive
  (`.li/.gl`) sits behind a JS/cookie interstitial (`slow_download` returns the
  consent wall); not bypassed.

**6. Elizabeth L. Eisenstein — *The Printing Press as an Agent of Change*, vols I–II
(1979) — ENGLISH edition**
- **libgen.li edition 136170020** = “The Printing Press as an Agent of Change
  **Volumes 1 and 2 in One**”, CUP, ISBN **0521299551 / 9780521299558** (English,
  832 pp). md5 `4b1729c1a04b03e510f921a201741c95`. Also 136392234 (`ee327b87…`)
  and 136395133 (`18f59e02…`) — same title/format.
- Download path likewise → **`cdn3.booksdl.lc` → 503**. **Not acquired.**
- IA holds the English edition only as **restricted** loans: `printingpressas01eise`
  (vol 1), `printingpressas02eise` (vol 2), `printingpressasa001-2eise_l3z7`
  (2-in-1, 1980) — all `inlibrary,printdisabled`; `_djvu.txt` → **HTTP 401**. The
  1979 HathiTrust record (000037087) is **search-only**. Google Books = `noview`.
  No open host found (Scribd = paywall; scispace/dokumen/epdf = 403/404).

---

## C. IN-COPYRIGHT — LENDING / PAYWALL ONLY — NO FREE COPY LOCATED

| # | Work | Evidence of restriction |
|---|------|------------------------|
| 1 | Thomas Basin, *Histoire de Charles VII*, **tome II (livres IV–V)**, ed./tr. Samaran (1944) | **Tome II not available free anywhere checked.** No IA scan (Open Library: 1944/1945 edition `no_ebook`). The only IA scans of the Samaran edition are the 1964/1965 **reprints** `histoiredecharle0001thom`/`histoiredecharle0002thom` = `inlibrary,printdisabled` (access-restricted; `_djvu.txt` withheld). **Gallica** has *no* Samaran edition (only the 1855–59 Quicherat *Histoire des règnes…*, ark bpt6k103228b). **HathiTrust** has only **tome I (1933)**, record 005973511 / htid `inu.32000014415949`, rightsCode **`ic` “Limited (search-only)”**. (Tome I, 1933, *is* free: IA `histoiredecharle00basi`, NOT_IN_COPYRIGHT — already on disk from the prior batch; not the requested tome.) |
| 4 | Strayer & Munro, *The Middle Ages, 395–1500*, **4th ed. (1959)** | IA `middleages3951500000stra` (1959, Appleton-Century-Crofts) = `inlibrary,printdisabled`, `access-restricted-item:true`; `_djvu.txt` → **HTTP 401**. Every IA edition (1942 3rd, 1959 4th, 1970 5th) is likewise restricted. Google Books: the 1959 volume (`qvygwaU1PFkC`) reports **“no e-book available”** (no snippet). Open Library `no_ebook`. **p.115 wording NOT obtained** — see Section D. |

---

## D. NOTES / GAPS

- **libgen CDN (`cdn3.booksdl.lc`)** is the single blocker for works 5 and 6, exactly
  as in the 2026-09-16 batch: `get.php` 307→503 on every retry; byte-range requests
  also 503; `cdn2/4/5` return a repository-folder error; `.li/.la/.vg/.bz/.gl`
  mirrors all resolve to the same CDN. No alternate open host exists for either
  title (both are CUP in-copyright books).
- **Strayer p.115 — NOT CAPTURED.** The 1959 4th ed. is lending/print-disabled on IA
  and has no Google Books preview, so neither the PDF nor IA full-text snippets could
  be obtained; HathiTrust (for this 1959 title) shows no searchable full item via the
  API. **If the principal supplies the target phrase** (a few words from p.115), it
  can be pushed through IA “search inside” and/or HathiTrust search-only on a follow
  pass — but the page text itself is not freely retrievable.
- **HathiTrust:** the catalogue **web UI and full-text search are Cloudflare-gated**
  from this host (403 “Just a moment…”). The **Bib API works** (HTTP 200) and was used
  for rights codes above.
- **Google Books JSON API** returned **HTTP 429 (daily quota exceeded)**; identification
  fell back to the non-API `viewapi` endpoint and to search results.
- **Gallica SRU** works (`gallica.bnf.fr/SRU`, ver 1.2); the plain web UI root 403s.
  Searches for the Samaran Basin and for a free Commynes Calmette returned nothing
  beyond what IA already had.
- **Anna’s Archive** (`.li`, `.gl`) serves a JS/cookie consent wall; `slow_download`
  could not be reached without accepting cookies — not attempted to bypass.
- **vdoc.pub / dokumen.pub / epdf.pub**: search/requests returned **403/404**
  (bot-gated). No usable copies.
- **Work 3 volume question answered:** the 1467 anti-spider ballade cycle is in
  **Tome VII** of Lettenhove’s edition (see Section A).
- No paywall / login / CAPTCHA / lending / print-disabled restriction was bypassed at
  any point. Fetched text treated as data only.

---

## TALLY

- **Verified free copies located + acquired (2/6 works; 3 files):** Commynes *Mémoires* t.I–II (Calmette/Durville, Champion 1924–25); Chastellain *Œuvres* Tome VII (Lettenhove, the 1467 spider-ballade volume; the full 8-vol set is free on IA).
- **Located, download blocked by CDN (2/6):** Bagehot *English Constitution* (Smith/CUP 2001); Eisenstein *Printing Press as an Agent of Change* (English, 2 vols-in-one).
- **In-copyright, lending/paywall only — no free copy located (2/6):** Basin *Histoire de Charles VII*, tome II (Samaran 1944); Strayer & Munro *The Middle Ages, 395–1500*, 4th ed. (1959) — p.115 wording not obtained.
- **All 6 works accounted for.**
