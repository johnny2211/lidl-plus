**This python package is unofficial and is not related in any way to Lidl. It was developed by reversed engineered requests and can stop working at anytime!**

> **Fork notice.** This is a fork of [Andre0512/lidl-plus](https://github.com/Andre0512/lidl-plus) with fixes for the current Lidl Plus API and added scripts to bulk-download every receipt on your account and render them as JPG/PDF invoices that look like the ones the app shows. See [Fork additions](#fork-additions) below.

# Python Lidl Plus API
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/Andre0512/lidl-plus/python-check.yml?branch=main&label=checks)](https://github.com/Andre0512/lidl-plus/actions/workflows/python-check.yml)
[![PyPI - Status](https://img.shields.io/pypi/status/lidl-plus)](https://pypi.org/project/lidl-plus)
[![PyPI](https://img.shields.io/pypi/v/lidl-plus?color=blue)](https://pypi.org/project/lidl-plus)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/lidl-plus)](https://www.python.org/)
[![PyPI - License](https://img.shields.io/pypi/l/lidl-plus)](https://github.com/Andre0512/lidl-plus/blob/main/LICENCE)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/lidl-plus)](https://pypistats.org/packages/lidl-plus)
[![Buy Me a Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-orange.svg)](https://www.buymeacoffee.com/andre0512)  


Fetch receipts and more from Lidl Plus.
## Installation
```bash
pip install lidl-plus
```

## Authentication
To login in Lidl Plus we need to simulate the app login.
This is a bit complicated, we need a web browser and some additional python packages.
After we have received the token once, we can use it for further requestes and we don't need a browser anymore.

#### Prerequisites
* Check you have installed one of the supported web browser
  - Chromium
  - Google Chrome
  - Mozilla Firefox
  - Microsoft Edge
* Install additional python packages
  ```bash
  pip install "lidl-plus[auth]"
  ```
#### Commandline-Tool
```bash
$ lidl-plus auth
Enter your language (de, en, ...): de
Enter your country (DE, AT, ...): AT
Enter your lidl plus username (phone number): +4915784632296
Enter your lidl plus password:
Enter the verify code you received via phone: 590287
------------------------- refresh token ------------------------
2D4FC2A699AC703CAB8D017012658234917651203746021A4AA3F735C8A53B7F
----------------------------------------------------------------
```

#### Python
```python
from lidlplus import LidlPlusApi

lidl = LidlPlusApi(language="de", country="AT")
lidl.login(phone="+4915784632296", password="password", verify_token_func=lambda: input("Insert code: "))
print(lidl.refresh_token)
```
## Usage
Currently, the only features are fetching receipts and activating coupons
### Receipts

Get your receipts as json and receive a list of bought items like:
```json
{
    "currentUnitPrice": "2,19",
    "quantity": "1",
    "isWeight": false,
    "originalAmount": "2,19",
    "name": "Vegane Frikadellen",
    "taxGroup": "1",
    "taxGroupName": "A",
    "codeInput": "4023456245134",
    "discounts": [
        {
            "description": "5€ Coupon",
            "amount": "0,21"
        }
    ],
    "deposit": null,
    "giftSerialNumber": null
},
```

#### Commandline-Tool
```bash
$ lidl-plus --language=de --country=AT --refresh-token=XXXXX receipt --all > data.json
```

#### Python
```python
from lidlplus import LidlPlusApi

lidl = LidlPlusApi("de", "AT", refresh_token="XXXXXXXXXX")
for receipt in lidl.tickets():
    pprint(lidl.ticket(receipt["id"]))
```

### Coupons

You can list all coupons and activate/deactivate them by id
```json
{
    "sections": [
        {
            "name": "FavoriteStore",
            "coupons": []
        },
        {
            "name": "AllStores",
            "coupons": [
                {
                    "id": "2c9b3554-a09c-412c-8be4-d41cbff13572",
                    "image": "https://lidlplusprod.blob.core.windows.net/images/coupons/LT/IDISC0000254911.png?t=1695452076",
                    "type": "Standard",
                    "offerTitle": "1 + 1",
                    "title": "👨🏻‍🍳 Frozen 👨🏻‍🍳",
                    "offerDescriptionShort": "FREE",
                    "isSegmented": false,
                    "startValidityDate": "2023-09-24T21:00:00Z",
                    "endValidityDate": "2023-10-01T20:59:59Z",
                    "isActivated": false,
                    "apologizeText": "Xxxxxxxxxxxxxxxxx",
                    "apologizeStatus": false,
                    "apologizeTitle": "Xxxxxxxxxxxxxxxxxxx",
                    "promotionId": "DISC0000254911",
                    "tagSpecial": "",
                    "firstColor": "#ffc700",
                    "secondaryColor": null,
                    "firstFontColor": "#4a4a4a",
                    "secondaryFontColor": null,
                    "isSpecial": false,
                    "hasAsterisk": false,
                    "isHappyHour": false,
                    "stores": []
                },
                .......
            ]
        },
        {
            "name": "OtherStores",
            "coupons": []
        }
    ]
}
```

#### Commandline-Tool

Activate all available coupons

```bash
$ lidl-plus --language=de --country=AT --refresh-token=XXXXX coupon --all
```

#### Python
```python
from lidlplus import LidlPlusApi

lidl = LidlPlusApi("de", "AT", refresh_token="XXXXXXXXXX")
for section in lidl.coupons()["sections"]:
  for coupon in section["coupons"]:
    print("found coupon: ", coupon["title"], coupon["id"])
```

## Help
#### Commandline-Tool
```commandline
Lidl Plus API

options:
  -h, --help                show this help message and exit
  -c CC, --country CC       country (DE, BE, NL, AT, ...)
  -l LANG, --language LANG  language (de, en, fr, it, ...)
  -u USER, --user USER      Lidl Plus login username
  -p XXX, --password XXX    Lidl Plus login password
  --2fa {phone,email}       choose two factor auth method
  -r TOKEN, --refresh-token TOKEN
                            refresh token to authenticate
  --skip-verify             skip ssl verification
  --not-accept-legal-terms  not auto accept legal terms updates
  -d, --debug               debug mode

commands:
  auth                      authenticate and get token
  receipt                   output last receipts as json
  coupon                    activate coupons
```

## Support
If you find this project helpful and would like to support its development, you can buy me a coffee! ☕

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/andre0512)

Don't forget to star the repository if you found it useful! ⭐

---

## Fork additions

This fork adds a small toolchain on top of the library for the common case of
"give me every receipt my Lidl Plus account has, as a folder of invoice
images". It also patches a few things in the upstream library that broke
against the current Lidl backend.

### What was fixed

The upstream package (v0.3.x) currently fails against the live API for two
reasons. Both are worked around in `fetch.py` via runtime monkey-patches, so
no fork of the library code itself is needed:

* **`App-Version` header.** The library sends `App-Version: 999.99.9`, which
  the server now rejects with HTTP 426 / empty body. A realistic value
  (e.g. `15.30.0`) is accepted. `fetch.py` overrides the header before any
  request is made.
* **Single-ticket endpoint.** `LidlPlusApi.ticket(id)` calls `/api/v2/<CC>/tickets/<id>`,
  which now returns `405 Method Not Allowed`. The working endpoint is
  `/api/v3/<CC>/tickets/<id>`. `fetch.py` calls v3 directly.
* **Read timeouts.** The default 10 s timeout is too short for the tickets
  list on large accounts. `fetch.py` bumps it to 60 s and wraps every call in
  an exponential-backoff retry (2 s → 32 s, up to 5 attempts).

Authentication is also handled outside the library, because Lidl's login page
now serves reCAPTCHA and the bundled Selenium flow no longer completes.

### What it does

Four standalone scripts at the repo root:

| Script | What it does |
|---|---|
| `auth_manual.py` | One-time OAuth login per country. Prints a URL you open in your normal browser; you log in (solve reCAPTCHA there), copy the failed `com.lidlplus.app://callback?...` URL back, and the script exchanges the `code` for a refresh token saved to `data/token_<CC>.txt`. |
| `fetch.py` | Uses the saved refresh token to list every ticket on the account and download its full detail JSON. Writes `data/receipts_<CC>.json`. |
| `render.py` | Renders each saved receipt to a JPG (or PDF) using headless Chromium (Playwright). Inlines the Lidl logo and regenerates the fiscal QR code and ITF return-info barcode locally, so the output looks like the in-app receipt. Writes `data/images_<CC>/<ticket_id>.jpg`. There is **no** Lidl endpoint that returns receipt images — the app itself renders the `htmlPrintedReceipt` field client-side, and this script does the same thing offline. |
| `search.py` | Regex search across all saved receipts by line-item description. |

Each Lidl Plus account is bound to one country, so you run the auth + fetch
flow once per country (e.g. `HR` and `SI`).

### Usage

```bash
# 1. clone + venv
git clone https://github.com/johnny2211/lidl-plus.git
cd lidl-plus
python3 -m venv .venv
source .venv/bin/activate

# 2. install the library and the extras the fork scripts need
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

Everything under `data/` is gitignored — tokens, JSONs, and rendered invoices
stay on your machine.

### Caveats

* The login URL produced by `auth_manual.py` is single-use; if you don't
  finish the paste-back step you need to re-run it.
* Refresh tokens rotate. If `fetch.py` starts returning 401, just run
  `auth_manual.py` again for that country.
* Rendered receipts pull the Lidl logo from the Lidl CDN at render time. If
  you want fully offline images, swap the `<img class="logo">` in
  `render.py` for a one-time download + inline.
