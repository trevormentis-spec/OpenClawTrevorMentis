# Acquisition Report — 2026-09-23

**Requested:** 13 works (12 books + 1 journal article), all on Anglo-American relations,
summitry and the machinery of the British state.

**Outcome: 1 of 13 obtained.** The remaining 12 are in-copyright commercial publications with
no legitimately free full text in existence. Details and legal routes below.

**Method:** Internet Archive advanced-search API for every title (checking
`access-restricted-item`), then targeted open-web searches for open-access, repository,
publisher-OA and author-hosted copies. All downloads content-verified with
`scripts/copyright_tools.py` (metadata + text, not filename).

**Rules applied (unchanged):** normal HTTP GET only; **no paywall, login, CAPTCHA, or
lending/print-disabled bypass.** Internet Archive copies that return
`access-restricted-item = true` are borrowing-only and are therefore off-limits to us.

---

## OBTAINED — verified

### [13] Robert D. Putnam — "Diplomacy and Domestic Politics: The Logic of Two-Level Games"
- *International Organization* 42(3), Summer 1988, pp. 427–460 (MIT Press) — journal article
- **Status: FOUND, full text verified.** 35 pages, PDF 1.4, 3,314,520 bytes
- sha256 `1b205c332e5c03d98b06e44579f92ca90290ad6e716e276f313c1559d6a0491c`
- Identity confirmed from page 1 text: *"Diplomacy and Domestic Politics: The Logic of Two-Level
  Games. Author(s): Robert D. Putnam. Source: International Organization, Vol. 42, No. 3
  (Summer, 1988), pp. 427-460. Published by: The MIT Press."*
- Source: `diplomacy.edu` (DiploFoundation course reading, openly served)
- Delivered: `exports/acq-2026-09-23/Putnam - Diplomacy and Domestic Politics (Intl Organization 42-3, 1988).pdf`

---

## NOT FREELY AVAILABLE — in copyright, no legal free copy exists

### [1] Peter Hennessy — "The Prime Minister: The Office and Its Holders Since 1945" (Allen Lane, 2000)
- IA holds 3 scans — **all `access-restricted-item = true`** (borrowing only, off-limits):
  `primeministeroff0000henn_r0c5`, `primeministeroff0000henn`, `primeministeroff0000pete`
- No repository or publisher-OA edition. Access: borrow via IA/Open Library, or library.

### [2] John Dumbrell — "A Special Relationship: Anglo-American Relations from the Cold War to Iraq" (Palgrave, 2nd ed. 2006)
- No IA record, no repository copy, no OA edition.
- Note: a host site (`research-solution.com`) advertises a PDF under this title. **Not used** —
  it is not a legitimate source. Access: publisher or library.

### [3] David Reynolds — "Summits: Six Meetings That Shaped the Twentieth Century" (Basic Books, 2007)
- IA holds 2 records — **both borrowing-only** (`summitssixmeetin0000reyn`, `bwb_W7-CQZ-541`).
- Access: borrow via IA, or library.

### [4] Jonathan Colman — "A 'Special Relationship'? Harold Wilson, Lyndon B. Johnson and Anglo-American Relations 'at the Summit', 1964–68" (Manchester UP, 2004)
- No IA record, no repository copy. Access: publisher (Manchester Hive) or library.

### [5] James Cooper — "A Diplomatic Meeting: Reagan, Thatcher, and the Art of Summitry"
- No IA record, no open copy. Access: publisher or library.

### [6] Marcus Holmes — "Face-to-Face Diplomacy: Social Neuroscience and International Relations" (CUP, 2018)
- No full-text repository copy. Cambridge publishes an **excerpt PDF** only
  (`assets.cambridge.org/97811084/17075/excerpt/9781108417075_excerpt.pdf`).
- Author site (marcusholmes.com) hosts a CV, not the book. Access: CUP/library.

### [7] David Marquand — "Ramsay MacDonald" (Jonathan Cape, 1977; 903 pp.)
- IA holds `ramsaymacdonald0000marq` — **borrowing-only**. Access: borrow via IA, or library.

### [8] Peter Hennessy — "The Secret State: Preparing for the Worst, 1945–2010" (Penguin, 2010)
- IA `secretstateprepa0000henn` — **borrowing-only**. Penguin publishes a **sample PDF**
  (`cdn.penguin.co.uk/.../9780141995663-sample.pdf`) — marketing extract, not the book.
- Access: borrow via IA, or library.

### [9] John H. Maurer & Christopher M. Bell (eds) — "At the Crossroads Between Peace and War: The London Naval Conference of 1930" (Naval Institute Press, 2014)
- No IA record, no open copy. Searches return reviews and *conference documents* (FRUS 1930,
  Hansard, contemporaneous press) — related primary material, not the book.
- Access: publisher, library, or interlibrary loan.

### [10] Nigel J. Ashton — "Kennedy, Macmillan and the Cold War: The Irony of Interdependence" (Palgrave, 2002)
- IA `kennedymacmillan0000asht` — **borrowing-only**. Access: borrow via IA, or library.

### [11] Iver B. Neumann — "Diplomatic Sites: A Critical Enquiry" (OUP, 2013)
- OUP lists it subscription/purchase only; chapters are behind "Get access".
- A related OA item exists — Neumann's article "Sited Diplomacy" (LSE eprints) — **not the book**.
- Access: OUP/library.

### [12] David Reynolds — "A 'Special Relationship'? America, Britain and the International Order Since the Second World War"
- *International Affairs* 62(1), Winter 1985/86, pp. 1–20 (RIIA/OUP)
- Paywalled at Oxford Academic and JSTOR; no OA or repository copy found.
- Access: OUP/JSTOR (institutional), or library.

---

## Why the ratio is 1:12

Every book on this list is a commercial scholarly monograph still in copyright. There is no
lawful free edition of any of them — not because the search failed, but because none exists.
The journal article came through because articles from that era are routinely posted as open
course readings.

**What would actually get you these 12:** institutional library access (the Manchester Hive,
OUP Academic and Cambridge Core editions are all there), Internet Archive *borrowing*, or
interlibrary loan. I can compile direct access links per title on request.

## Standing blocker (unchanged)

Libgen CDN (`cdn3.booksdl.lc`) truncates large transfers — recorded from the prior run and
still true. Shadow-library mirrors were **not** consulted for this request.
