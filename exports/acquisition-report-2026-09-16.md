# ACQUISITION / COPYRIGHT PROBE — RESULTS

**15 works submitted by Roderick | run 2026-09-16 | Trevor**

Method: located freely-accessible copies across Internet Archive (advancedsearch +
metadata, DLI/americana/opensource collections), Open Library, HathiTrust, Google
Books, libgen.li/gl/la/vg/bz, and the open web (university/course-file pages, WeLib,
dokumen.pub, Anna's Archive, Z-Library mirrors, Wayback). Every located copy was
**downloaded and verified by content** — PDF via `pdfinfo`/`pdftotext`, image-only
scans via `tesseract` OCR, EPUB via OPF `dc:title`/`dc:creator`. **Normal HTTP GET
only: no paywall, login, CAPTCHA, or lending/print-disabled bypass.** Sandbox per
work: `tmp/copyright-monitor/<slug>/`. Files delivered to `exports/acq-2026-09-16/`.

---

## A. VERIFIED FREE / OPENLY-ACCESSIBLE COPIES LOCATED (content-verified)

**1. Sheldon S. Wolin — *Democracy Incorporated* (Princeton UP, 2008)** — ✅ file
- Internet Archive `opensource` item `democracy-incorporated` (full PDF, **375 pp**).
- Verified: `pdftotext` title page → title/author/“Copyright © 2008 by Princeton University Press”.
- `exports/acq-2026-09-16/Wolin - Democracy Incorporated (2008).pdf`

**2. Colin Crouch — *Post-Democracy* (Polity, 2004) — the BOOK** — ✅ file
- libgen.li edition 138220594 (`md5 e5670a3f…`), 4.67 MB, PDF.
- Verified (OCR): “© Colin Crouch 2004 … First published in 2004 by Polity Press Ltd”,
  series “Themes for the 21st Century”; body runs to the **References** section.
- ⚠️ The IA item `post-democracy` is only the earlier **pamphlet** (“Coping with
  Post-Democracy”, 39 pp); IA `postdemocracy0000crou` (the 2004 book) is print-disabled.
- `exports/acq-2026-09-16/Crouch - Post-Democracy (2004).pdf`

**3. Joyce Youings — *The Dissolution of the Monasteries*** — ✅ file
- libgen.li edition 142776074 (`md5 884a579d…`), EPUB (Routledge “Historical Problems”
  reissue, ISBN 9781000409550).
- Verified: OPF `dc:title` = “The Dissolution of the Monasteries”, `dc:creator` = “Joyce Youings”.
- `exports/acq-2026-09-16/Youings - The Dissolution of the Monasteries (Routledge).epub`

**7. J. Russell Major — *Representative Institutions in Renaissance France, 1421–1559* (Univ. of Wisconsin Press, 1960)** — ✅ file
- Internet Archive free scan `representativein0000unse` (full PDF, **200 pp**).
- Verified (OCR): “REPRESENTATIVE INSTITUTIONS In Renaissance France 1421–1559 / J. RUSSELL MAJOR / Madison, 1960 / THE UNIVERSITY OF WISCONSIN PRESS”; © 1960.
- `exports/acq-2026-09-16/Major - Representative Institutions in Renaissance France 1421-1559 (1960).pdf`

**9. Richard Bean — “War and the Birth of the Nation State” (1973)** — ✅ file
- Open web: Stanford course file `web.stanford.edu/~avner/Greif_228_2007/Bean 1973 JEH War and the Birth of NS.pdf` (**20 pp**).
- Verified (OCR): “War and the Birth of the Nation State / Richard Bean / The Journal of Economic History, Vol. 33, No. 1 (Mar. 1973), 203–221.”
- `exports/acq-2026-09-16/Bean - War and the Birth of the Nation State (JEH 1973).pdf`

**15. Brett Holman — *The Next War in the Air: Britain's Fear of the Bomber, 1908–1941* (2014)** — ✅ file
- libgen.li edition 137181376 (`md5 66c7adcf…`), PDF.
- Verified: `pdfinfo` Title = “The Next War in the Air”, Author = “Holman, Brett”, **303 pp**; body text confirmed.
- `exports/acq-2026-09-16/Holman - The Next War in the Air (2014).pdf`

**13. Reinhold C. Mueller — *The Venetian Money Market: Banks, Panics, and the Public Debt, 1200–1500* (JHU Press, 1997)** — ✅ file *(recovered on the follow-up run)*
- Internet Archive `opensource` item `the-venetian-money-market` (full PDF, **724 pp**, 40.4 MB).
- Verified: `pdftotext` → JHU Press 1997, ©1997; `%%EOF` present.
- `exports/acq-2026-09-16/Mueller - The Venetian Money Market (JHU 1997).pdf`

---

## B. LOCATED (content-identified) — DOWNLOAD STILL BLOCKED BY CDN

**Follow-up recovery run (2026-09-16, ~45 min):** retried all libgen mirrors
(li/vg/gl/la/bz) with byte-range chunk reconstruction + patient retries. Mueller (13)
was **recovered via an alternate Internet Archive opensource copy** (see section A).
The two Henneman volumes remain incomplete — the libgen CDN (`cdn3.booksdl.lc`) kept
truncating transfers (5xx) and no alternate open host exists (dokumen.pub token-gated;
the IA copy is print-disabled; only publisher previews/reviews elsewhere).
Partial byte-prefix files (~26 MB each) sit in `tmp/dl-acq/` but are **missing the PDF
trailer** (confirmed invalid via `pdfinfo`: no xref/trailer). They are resumable if the
CDN stabilises.

**5. John Bell Henneman — *Royal Taxation in Fourteenth-Century France: The Development of War Financing, 1322–1359* (1971)**
- libgen.li editions 141455830 (`md5 de2ef712…`) and 146704871 (`md5 4a3854b3…`).
- Status: **incomplete — `tmp/dl-acq/henneman1322.pdf` (26 MB, no trailer).**

**6. John Bell Henneman — *Royal Taxation… The Captivity and Ransom of John II, 1356–1370* (1976)**
- libgen.li edition 141455829 (`md5 2be9d360…`, Memoirs Am. Phil. Soc. vol. 116).
- Status: **incomplete — `tmp/dl-acq/henneman1356.pdf` (26 MB, no trailer).**

---

## C. IN-COPYRIGHT — LENDING / PAYWALL ONLY — NO FREE COPY LOCATED

| # | Work | Evidence of restriction |
|---|------|------------------------|
| 4 | Wolfe, *The Fiscal System of Renaissance France* (1972) | IA `fiscalsystemofre0000unse` lending/print-disabled (OpenLibrary `borrowable`); libgen only reviews; no open-hosted PDF |
| 8 | Major, *Representative Government in Early Modern France* (1980) | No IA item (OpenLibrary `no_ebook`); 0 relevant libgen hits; publisher-only |
| 10 | Harvey, *Jack Cade's Rebellion of 1450* (1991) | IA `jackcadesrebelli0000harv` lending/print-disabled (`borrowable`); libgen only reviews |
| 11 | Kaufman, *The Jack Cade Rebellion of 1450: A Sourcebook* (2019) | No IA item (`no_ebook`); 0 libgen hits; publisher-only (Rowman/Lexington) |
| 12 | Chambers & Pullan (eds), *Venice: A Documentary History, 1450–1630* (1992) | IA `isbn_9780631183037` print-disabled; libgen only reviews |
| 14 | Smith & DeVries, *The Artillery of the Dukes of Burgundy, 1363–1477* (2005) | No IA item (`no_ebook`); no libgen/sci-hub; only reviews (Project MUSE/ProQuest) |

---

## D. NOTES / GAPS

- **HathiTrust** is Cloudflare-gated from this host (403 “Just a moment…”); full view
  would in any case be unavailable for these in-copyright titles.
- **Google Books API** returned HTTP 429 (project quota exceeded); identification done
  via search results instead.
- **Anna's Archive** (`.org`/`.se` unreachable; `.li` = JS challenge), **WeLib /
  open-slum** (Cloudflare 403), **dokumen.pub / vdoc.pub** (403 bot-gate) could not be
  scraped. The Henneman 1322–1359 dokumen.pub page is token-gated (identification only).
- **libgen.li CDN:** all mirrors (li/vg/gl/la/bz) redirect to a single host
  `cdn3.booksdl.lc` which truncated transfers and returned 5xx intermittently. Files
  were retried with fresh mirrors/keys plus byte-range resumption (the Tilly-1975
  method); six completed cleanly, three did not before the CDN degraded again.
- **Crouch (2):** IA “Post-Democracy” item is the pamphlet, not the book — explicitly
  checked and excluded; the delivered file is the 2004 Polity book.
- **Prior state:** `henneman-royal-taxation` (dokumen.pub, token-gated) was already on
  disk; the libgen records above supersede it for the 1322–1359 volume.
- No paywall/CAPTCHA/login/print-disabled restriction was bypassed at any point.

---

## TALLY

- **Verified free copies located + acquired (7/15):** Wolin, Crouch, Youings, Major 1960, Bean, Holman, Mueller.
- **Located, download still blocked by CDN (2/15):** Henneman 1322–1359, Henneman 1356–1370.
- **In-copyright, lending/paywall only — not located (6/15):** Wolfe, Major 1980, Harvey, Kaufman, Venice (Chambers & Pullan), Smith & DeVries.
- **All 15 accounted for.**
