#!/usr/bin/env python3
"""Search saved Lidl Plus receipts (data/receipts_*.json) for line items.

Usage:
  python search.py "mlijeko"           # case-insensitive regex, all countries
  python search.py -c HR "coca cola"   # restrict to Croatia
  python search.py --json "bread"      # raw JSON output
"""
import argparse
import json
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def iter_receipts(country=None):
    pattern = f"receipts_{country.upper()}.json" if country else "receipts_*.json"
    files = sorted(DATA_DIR.glob(pattern))
    if not files:
        print(f"No receipt files found in {DATA_DIR}/ (pattern {pattern}).", file=sys.stderr)
    for f in files:
        cc = f.stem.split("_", 1)[1]
        for r in json.loads(f.read_text()):
            yield cc, r


def line_items(receipt):
    for key in ("itemsLine", "items"):
        v = receipt.get(key)
        if isinstance(v, list):
            return v
    return []


def receipt_meta(receipt):
    store = receipt.get("store")
    if isinstance(store, dict):
        store_name = store.get("name") or store.get("storeCode")
    else:
        store_name = receipt.get("storeCode") or store
    return {
        "id": receipt.get("id"),
        "date": receipt.get("date") or receipt.get("ticketDate"),
        "store": store_name,
        "total": receipt.get("totalAmount"),
        "currency": receipt.get("currency"),
    }


def main():
    p = argparse.ArgumentParser(description="Search Lidl Plus receipts")
    p.add_argument("query", help="case-insensitive regex matched against item name or barcode")
    p.add_argument("-c", "--country", help="restrict to one country, e.g. HR")
    p.add_argument("--json", action="store_true", help="output matches as JSON")
    args = p.parse_args()

    rx = re.compile(args.query, re.IGNORECASE)
    matches = []
    for cc, r in iter_receipts(args.country):
        for item in line_items(r):
            name = item.get("name", "") or ""
            code = item.get("codeInput", "") or ""
            if rx.search(name) or rx.search(code):
                matches.append({"country": cc, "receipt": receipt_meta(r), "item": item})

    if args.json:
        print(json.dumps(matches, indent=2, ensure_ascii=False))
        return

    if not matches:
        print("No matches.", file=sys.stderr)
        return

    for m in matches:
        meta, it = m["receipt"], m["item"]
        cur = meta.get("currency") or ""
        print(
            f"[{m['country']}] {meta.get('date','?')}  "
            f"{it.get('quantity','?')} x {(it.get('name') or '?')[:40]:40s} "
            f"@ {it.get('currentUnitPrice','?')}  "
            f"(receipt {meta.get('total','?')} {cur}, id {meta.get('id','?')})"
        )


if __name__ == "__main__":
    main()
