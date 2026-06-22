# Lidl Plus receipt downloader

**Unofficial. Not affiliated with Lidl. Built on reverse-engineered requests and may stop working at any time.**

Fork of [Andre0512/lidl-plus](https://github.com/Andre0512/lidl-plus) that
fixes the parts of the API that broke against the current Lidl backend and
adds a small toolchain to bulk-download every receipt on your Lidl Plus
account and render them as JPG (or PDF) invoices that look like the ones the
app shows.

The upstream `lidl-plus` CLI (`lidl-plus auth`, `lidl-plus receipt`, …) is
intentionally not documented here because the Selenium-based login it relies
on no longer completes — Lidl's login page now serves reCAPTCHA. The
underlying `LidlPlusApi` class is still used as a library; only the auth and
the broken endpoints are handled outside it.

## What was fixed

Two upstream issues are worked around at runtime in `fetch.py` (no fork of
the library code itself):

* **`App-Version` header.** The library sends `App-Version: 999.99.9`, which
  the server now rejects (HTTP 426 / empty body). A realistic value such as
  `15.30.0` is accepted. `fetch.py` overrides the header before any request
  is made.
* **Single-ticket endpoint.** `LidlPlusApi.ticket(id)` calls
  `/api/v2/<CC>/tickets/<id>`, which now returns `405 Method Not Allowed`.
  The working endpoint is `/api/v3/<CC>/tickets/<id>`. `fetch.py` calls v3
  directly.
* **Read timeouts.** The default 10 s timeout is too short for the tickets
  list on large accounts. `fetch.py` bumps it to 60 s and wraps every call
  in an exponential-backoff retry (2 s → 32 s, up to 5 attempts).

Authentication is replaced by a manual OAuth PKCE flow (`auth_manual.py`)
that hands the reCAPTCHA off to your real browser.

## How it works

Four standalone scripts at the repo root:

| Script | What it does |
|---|---|
| `auth_manual.py` | One-time OAuth login per country. Prints a URL you open in your normal browser; you log in (solve reCAPTCHA there), copy the failed `com.lidlplus.app://callback?...` URL back, and the script exchanges the `code` for a refresh token saved to `data/token_<CC>.txt`. |
| `fetch.py` | Uses the saved refresh token to list every ticket on the account and download its full detail JSON. Writes `data/receipts_<CC>.json`. |
| `render.py` | Renders each saved receipt to a JPG (or PDF) using headless Chromium (Playwright). Inlines the Lidl logo and regenerates the fiscal QR code and ITF return-info barcode locally, so the output looks like the in-app receipt. Writes `data/images_<CC>/<ticket_id>.jpg`. There is **no** Lidl endpoint that returns receipt images — the app itself renders the `htmlPrintedReceipt` field client-side, and this script does the same thing offline. |
| `search.py` | Regex search across all saved receipts by line-item description. |

Each Lidl Plus account is bound to one country, so the auth + fetch flow is
run once per country (e.g. `HR`, `SI`, `DE`, `AT`, …).

## Usage

```bash
# 1. clone + venv
git clone https://github.com/johnny2211/lidl-plus.git
cd lidl-plus
python3 -m venv .venv
source .venv/bin/activate

# 2. install the library and the extras these scripts need
pip install "lidl-plus[auth]" playwright "qrcode[pil]" python-barcode
playwright install chromium

# 3. one-time login per country (opens a URL you paste into your browser)
python auth_manual.py -c HR -l hr
python auth_manual.py -c SI -l sl

# 4. download every receipt for that country
python fetch.py -c HR -l hr     # → data/receipts_HR.json
python fetch.py -c SI -l sl     # → data/receipts_SI.json

# 5. render every receipt as a JPG invoice
python render.py -c HR          # → data/images_HR/<id>.jpg
python render.py -c SI          # → data/images_SI/<id>.jpg
#   --format pdf  for PDFs
#   -q 75         for smaller JPGs
#   -n 5          render only the first 5 (smoke test)

# 6. search across saved receipts
python search.py "mlijeko"      # case-insensitive regex, all countries
```

Everything under `data/` is gitignored — tokens, JSONs, and rendered
invoices stay on your machine.

## Caveats

* The login URL produced by `auth_manual.py` is single-use; if you don't
  finish the paste-back step you need to re-run it.
* Refresh tokens rotate. If `fetch.py` starts returning 401, just run
  `auth_manual.py` again for that country.
* Rendered receipts pull the Lidl logo from the Lidl CDN at render time. If
  you want fully offline images, swap the `<img class="logo">` in
  `render.py` for a one-time download + inline.

## Credits

All credit for the underlying `LidlPlusApi` library goes to
[Andre0512](https://github.com/Andre0512) and contributors to
[Andre0512/lidl-plus](https://github.com/Andre0512/lidl-plus). This fork
only adds the scripts above and the runtime patches needed to keep the
existing API client working against the current Lidl backend.

## Licence

Same as upstream — see [`LICENCE`](LICENCE).
