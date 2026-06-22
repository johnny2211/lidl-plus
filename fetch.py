#!/usr/bin/env python3
"""Fetch all Lidl Plus receipts for one country and save them to data/.

First run for a country: performs an interactive login (Chrome) and stores the
resulting refresh token under data/token_<CC>.txt. Subsequent runs reuse it.
"""
import argparse
import json
import sys
import time
from getpass import getpass
from pathlib import Path

import requests

from lidlplus import LidlPlusApi

DATA_DIR = Path(__file__).parent / "data"

# Bump library default (10s) — tickets.lidlplus.com is frequently slow.
LidlPlusApi._TIMEOUT = 60

# The library hardcodes App-Version "999.99.9" which the tickets API now rejects
# (server hangs / closes the HTTP/2 stream with INTERNAL_ERROR). Override with a
# realistic version so requests are accepted.
_orig_default_headers = LidlPlusApi._default_headers

def _patched_default_headers(self):
    h = _orig_default_headers(self)
    h["App-Version"] = "15.30.0"
    return h

LidlPlusApi._default_headers = _patched_default_headers


# Single-ticket detail moved from /api/v2 to /api/v3 (v2 returns 405 now).
def _patched_ticket(self, ticket_id):
    kwargs = {"headers": self._default_headers(), "timeout": self._TIMEOUT}
    url = f"https://tickets.lidlplus.com/api/v3/{self._country}/tickets/{ticket_id}"
    r = requests.get(url, **kwargs)
    r.raise_for_status()
    return r.json()

LidlPlusApi.ticket = _patched_ticket


def _retry(fn, *, tries=5, base_delay=2.0, label=""):
    last = None
    for attempt in range(1, tries + 1):
        try:
            return fn()
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            last = e
            delay = base_delay * (2 ** (attempt - 1))
            print(f"  {label}: {type(e).__name__}, retry {attempt}/{tries} in {delay:.0f}s", file=sys.stderr)
            time.sleep(delay)
    raise last


def token_path(country):
    return DATA_DIR / f"token_{country.upper()}.txt"


def load_token(country):
    p = token_path(country)
    return p.read_text().strip() if p.exists() else None


def save_token(country, token):
    DATA_DIR.mkdir(exist_ok=True)
    token_path(country).write_text(token + "\n")


def authenticate(language, country, username, password, verify_mode, headless=True):
    api = LidlPlusApi(language, country)
    api.login(
        username,
        password,
        verify_token_func=lambda: input(f"Enter the {verify_mode} verification code: "),
        verify_mode=verify_mode,
        headless=headless,
    )
    save_token(country, api.refresh_token)
    return api


def fetch_all(api):
    tickets = _retry(lambda: api.tickets(), label="list")
    print(f"Found {len(tickets)} receipts; fetching full details...", file=sys.stderr)
    out = []
    for i, t in enumerate(tickets, 1):
        out.append(_retry(lambda t=t: api.ticket(t["id"]), label=f"ticket {t['id']}"))
        if i % 10 == 0 or i == len(tickets):
            print(f"  {i}/{len(tickets)}", file=sys.stderr)
    return out


def main():
    p = argparse.ArgumentParser(description="Fetch Lidl Plus receipts for one country")
    p.add_argument("-c", "--country", required=True, help="country code, e.g. HR, SI")
    p.add_argument("-l", "--language", required=True, help="language code, e.g. hr, sl")
    p.add_argument("-u", "--user", help="phone or email (only needed on first login)")
    p.add_argument("--2fa", dest="twofa", choices=["phone", "email"], default="phone")
    p.add_argument("--reauth", action="store_true", help="force a fresh interactive login")
    p.add_argument("--show", action="store_true", help="show the Chrome window during login (debug)")
    args = p.parse_args()

    token = None if args.reauth else load_token(args.country)
    if token:
        print(f"Using saved token for {args.country.upper()}", file=sys.stderr)
        api = LidlPlusApi(args.language, args.country, refresh_token=token)
    else:
        user = args.user or input("Lidl Plus username (phone or email): ")
        pw = getpass("Lidl Plus password: ")
        api = authenticate(args.language, args.country, user, pw, args.twofa, headless=not args.show)
        print("Saved refresh token.", file=sys.stderr)

    receipts = fetch_all(api)
    DATA_DIR.mkdir(exist_ok=True)
    out_path = DATA_DIR / f"receipts_{args.country.upper()}.json"
    out_path.write_text(json.dumps(receipts, indent=2, ensure_ascii=False))
    print(f"Wrote {len(receipts)} receipts to {out_path}", file=sys.stderr)
    save_token(args.country, api.refresh_token)


if __name__ == "__main__":
    main()
