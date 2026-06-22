#!/usr/bin/env python3
"""Manual Lidl Plus login — bypasses Selenium/reCAPTCHA.

Lidl's login page now serves reCAPTCHA, which blocks automated browsers.
This script does the OAuth dance manually:

  1. Prints a login URL you open in your normal Chrome.
  2. You log in (password + 2FA, solve reCAPTCHA).
  3. The browser will fail to redirect to ``com.lidlplus.app://callback?code=...``
     because the scheme is not registered. That's expected — copy the failed
     URL from Chrome's address bar.
  4. Paste it back here. The script extracts the ``code`` and exchanges it for
     a refresh token, which is saved to ``data/token_<CC>.txt``.

Subsequent receipt fetches via ``fetch.py`` reuse that token (no browser).
"""
import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from lidlplus import LidlPlusApi

DATA_DIR = Path(__file__).parent / "data"


def token_path(country):
    return DATA_DIR / f"token_{country.upper()}.txt"


def extract_code(pasted):
    pasted = pasted.strip()
    if "code=" not in pasted:
        raise SystemExit("Could not find 'code=' in the pasted URL.")
    qs = parse_qs(urlparse(pasted).query)
    if "code" in qs:
        return qs["code"][0]
    import re
    m = re.search(r"code=([0-9A-Fa-f]+)", pasted)
    if not m:
        raise SystemExit("Could not extract code from pasted URL.")
    return m.group(1)


def main():
    p = argparse.ArgumentParser(description="Manual Lidl Plus OAuth login")
    p.add_argument("-c", "--country", required=True, help="country code, e.g. HR, SI")
    p.add_argument("-l", "--language", required=True, help="language code, e.g. hr, sl")
    args = p.parse_args()

    api = LidlPlusApi(args.language, args.country)
    url = api._register_link  # also initialises api._code_verifier

    print()
    print("=" * 78)
    print("Open this URL in your normal Chrome and log in:")
    print()
    print(url)
    print()
    print("After login, Chrome will say it cannot open 'com.lidlplus.app://callback...'.")
    print("Copy the FULL failed URL from Chrome's address bar and paste it below.")
    print("=" * 78)
    print()

    pasted = input("Paste callback URL (or just the code): ").strip()
    code = extract_code(pasted)

    api._authorization_code(code)
    DATA_DIR.mkdir(exist_ok=True)
    token_path(args.country).write_text(api.refresh_token + "\n")
    print(f"\nSaved refresh token to {token_path(args.country)}", file=sys.stderr)
    print("You can now run: fetch.py -c %s -l %s" % (args.country, args.language))


if __name__ == "__main__":
    main()
