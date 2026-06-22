#!/usr/bin/env python3
"""Render saved Lidl Plus receipts to JPG using a headless Chromium.

For each receipt in data/receipts_<CC>.json:
  * wrap htmlPrintedReceipt in a receipt-paper page (white bg, monospaced),
  * inline the logo, QR code and barcode (generated locally),
  * full-page screenshot to data/images_<CC>/<id>.jpg.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import sys
from pathlib import Path

import qrcode
import barcode
from barcode.writer import ImageWriter
from playwright.sync_api import sync_playwright

DATA_DIR = Path(__file__).parent / "data"

PAGE_CSS = """
html, body { margin: 0; padding: 0; background: #ffffff; }
body { width: 420px; padding: 18px 16px 22px; font-family: "Menlo", "Courier New", monospace; }
.logo { display: block; margin: 0 auto 12px; max-width: 180px; height: auto; }
pre { margin: 0; font-family: inherit; font-size: 12px; line-height: 1.25; white-space: pre; }
.codes { margin-top: 14px; text-align: center; }
.codes img { display: block; margin: 8px auto; }
.code-label { font-family: inherit; font-size: 10px; color: #333; margin-top: 4px; word-break: break-all; }
"""


def _png_data_url(png_bytes: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")


def _qr_png(text: str, box_size: int = 4) -> bytes:
    qr = qrcode.QRCode(box_size=box_size, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


_BARCODE_FMTS = {
    "ITF": "itf",
    "CODE128": "code128",
    "EAN13": "ean13",
    "EAN8": "ean8",
    "UPCA": "upca",
}


def _barcode_png(text: str, fmt: str) -> bytes | None:
    name = _BARCODE_FMTS.get(fmt.upper())
    if not name:
        return None
    try:
        cls = barcode.get_barcode_class(name)
        b = cls(text, writer=ImageWriter())
        buf = io.BytesIO()
        b.write(buf, options={"write_text": False, "module_height": 12.0, "quiet_zone": 2.0})
        return buf.getvalue()
    except Exception as e:
        print(f"  barcode {fmt} {text!r}: {e}", file=sys.stderr)
        return None


def _codes_html(codes: list[dict]) -> str:
    parts = ['<div class="codes">']
    for c in codes or []:
        fmt = (c.get("format") or "").upper()
        text = c.get("code") or ""
        if not text:
            continue
        if fmt == "QR_CODE":
            png = _qr_png(text)
        else:
            png = _barcode_png(text, fmt)
        if not png:
            continue
        parts.append(f'<img src="{_png_data_url(png)}" alt="{fmt}"/>')
        if c.get("codeType") != "Fiscal":
            parts.append(f'<div class="code-label">{text}</div>')
    parts.append("</div>")
    return "".join(parts)


def build_page(receipt: dict) -> str:
    html_receipt = receipt.get("htmlPrintedReceipt") or ""
    logo = receipt.get("logoUrl") or ""
    codes_html = _codes_html(receipt.get("codes") or [])
    logo_html = f'<img class="logo" src="{logo}"/>' if logo else ""
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>{PAGE_CSS}</style></head>
<body>{logo_html}{html_receipt}{codes_html}</body></html>"""


def render_country(country: str, fmt: str = "jpg", quality: int = 90, limit: int | None = None) -> None:
    src = DATA_DIR / f"receipts_{country.upper()}.json"
    if not src.exists():
        sys.exit(f"missing {src}")
    out_dir = DATA_DIR / f"images_{country.upper()}"
    out_dir.mkdir(exist_ok=True)
    receipts = json.loads(src.read_text())
    if limit:
        receipts = receipts[:limit]
    total = len(receipts)
    print(f"Rendering {total} {country.upper()} receipts to {out_dir} ({fmt})", file=sys.stderr)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 420, "height": 1200}, device_scale_factor=2)
        page = ctx.new_page()
        for i, r in enumerate(receipts, 1):
            rid = r.get("id") or f"receipt_{i}"
            out = out_dir / f"{rid}.{fmt}"
            page.set_content(build_page(r), wait_until="load")
            if fmt == "pdf":
                page.pdf(path=str(out), print_background=True, width="440px", height="2000px",
                         margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
            else:
                page.screenshot(path=str(out), full_page=True, type="jpeg", quality=quality)
            if i % 10 == 0 or i == total:
                print(f"  {i}/{total}", file=sys.stderr)
        browser.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="Render Lidl Plus receipts to JPG/PDF")
    ap.add_argument("-c", "--country", required=True, help="country code, e.g. HR, SI")
    ap.add_argument("-f", "--format", choices=["jpg", "pdf"], default="jpg")
    ap.add_argument("-q", "--quality", type=int, default=90, help="JPEG quality (1-100)")
    ap.add_argument("-n", "--limit", type=int, default=None, help="only render first N (for testing)")
    args = ap.parse_args()
    render_country(args.country, fmt=args.format, quality=args.quality, limit=args.limit)


if __name__ == "__main__":
    main()
