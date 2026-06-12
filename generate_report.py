#!/usr/bin/env python3
import os
import sys
import glob
import json
import html
import argparse
import subprocess
import tempfile
from datetime import datetime


def load_results(results_dir, suites_filter=None):
    items = []
    for path in sorted(glob.glob(os.path.join(results_dir, "*.json"))):
        try:
            with open(path, encoding="utf-8") as f:
                rec = json.load(f)
            if suites_filter:
                if rec.get("suite") not in suites_filter:
                    continue
            items.append(rec)
        except Exception as e:
            print(f"WARN: gagal baca {path}: {e}", file=sys.stderr)
    return items


def fmt_duration(seconds):
    seconds = int(round(seconds or 0))
    m, s = divmod(seconds, 60)
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def donut_svg(pass_rate):
    r = 54
    circ = 2 * 3.14159265 * r
    passed_len = circ * (pass_rate / 100.0)
    rest_len = circ - passed_len
    return f"""
    <svg width="150" height="150" viewBox="0 0 150 150">
      <circle cx="75" cy="75" r="{r}" fill="none" stroke="#e9edf3" stroke-width="16"/>
      <circle cx="75" cy="75" r="{r}" fill="none" stroke="#1f9d57" stroke-width="16"
              stroke-dasharray="{passed_len:.2f} {rest_len:.2f}"
              stroke-dashoffset="{circ/4:.2f}" stroke-linecap="round"
              transform="rotate(-90 75 75)"/>
      <text x="75" y="70" text-anchor="middle" font-size="26" font-weight="700"
            fill="#1d2733">{pass_rate:.0f}%</text>
      <text x="75" y="92" text-anchor="middle" font-size="11" fill="#6b7785">pass rate</text>
    </svg>
    """


def status_badge(status):
    if status == "passed":
        return '<span class="badge badge-pass">PASSED</span>'
    return '<span class="badge badge-fail">FAILED</span>'


def build_html(items, build_name, suites_label):
    total = len(items)
    passed = sum(1 for i in items if i.get("status") == "passed")
    failed = total - passed
    pass_rate = (passed / total * 100) if total else 0
    total_duration = sum(i.get("duration_seconds", 0) or 0 for i in items)
    generated = datetime.now().strftime("%d %B %Y, %H:%M:%S")

    suites = {}
    for i in items:
        suites.setdefault(i.get("suite", "Unknown"), []).append(i)

    suite_blocks = []
    for suite_name in sorted(suites):
        rows = sorted(suites[suite_name],
                      key=lambda x: float(x.get("platform_version") or 0))
        s_total = len(rows)
        s_pass = sum(1 for r in rows if r.get("status") == "passed")
        app_id = rows[0].get("app_id", "-") if rows else "-"

        tr = []
        for idx, r in enumerate(rows, 1):
            error = r.get("error")
            link = r.get("public_url")
            session_cell = (
                f'<a href="{html.escape(link)}">Lihat di BrowserStack</a>'
                if link else "-"
            )
            err_cell = (
                f'<div class="err">{html.escape(error)}</div>' if error else "—"
            )
            tr.append(f"""
              <tr>
                <td class="c-num">{idx}</td>
                <td>{html.escape(r.get("device_name", "-"))}</td>
                <td class="c-mid">Android {html.escape(str(r.get("platform_version", "-")))}</td>
                <td class="c-mid">{status_badge(r.get("status"))}</td>
                <td class="c-mid">{fmt_duration(r.get("duration_seconds"))}</td>
                <td class="c-mid">{session_cell}</td>
                <td>{err_cell}</td>
              </tr>""")

        suite_blocks.append(f"""
        <div class="suite">
          <div class="suite-head">
            <div class="suite-title">{html.escape(suite_name)}</div>
            <div class="suite-meta">
              <span class="pill">{s_pass}/{s_total} passed</span>
              <span class="app-id">{html.escape(app_id)}</span>
            </div>
          </div>
          <table class="grid">
            <thead>
              <tr>
                <th class="c-num">#</th><th>Device</th><th class="c-mid">OS</th>
                <th class="c-mid">Status</th><th class="c-mid">Durasi</th>
                <th class="c-mid">Session</th><th>Catatan Error</th>
              </tr>
            </thead>
            <tbody>{''.join(tr)}</tbody>
          </table>
        </div>""")

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: "Helvetica Neue", Arial, sans-serif;
    color: #1d2733; margin: 0; font-size: 12px; line-height: 1.45;
  }}
  .header {{ background: #0f2747; color: #fff; padding: 26px 32px; }}
  .header h1 {{ margin: 0; font-size: 22px; letter-spacing: .2px; }}
  .header .sub {{ margin-top: 6px; font-size: 12px; color: #b9c6da; }}
  .header .build {{ margin-top: 10px; font-size: 12px; }}
  .header .build b {{ color: #fff; }}
  .wrap {{ padding: 24px 32px; }}
  .summary {{ width: 100%; border-collapse: collapse; margin-bottom: 8px; }}
  .summary td {{ vertical-align: middle; }}
  .cards td {{ padding: 0 6px; }}
  .card {{
    border: 1px solid #e4e9f0; border-radius: 8px; padding: 14px 16px;
    text-align: center; background: #fbfcfe;
  }}
  .card .num {{ font-size: 26px; font-weight: 700; }}
  .card .lbl {{ font-size: 10.5px; color: #6b7785; text-transform: uppercase;
               letter-spacing: .6px; margin-top: 2px; }}
  .num-pass {{ color: #1f9d57; }}
  .num-fail {{ color: #d23a3a; }}
  .num-total {{ color: #0f2747; }}
  .suite {{ margin-top: 22px; page-break-inside: avoid; }}
  .suite-head {{
    display: table; width: 100%; border-bottom: 2px solid #0f2747;
    padding-bottom: 6px; margin-bottom: 8px;
  }}
  .suite-title {{ display: table-cell; font-size: 15px; font-weight: 700; }}
  .suite-meta {{ display: table-cell; text-align: right; vertical-align: bottom; }}
  .pill {{
    background: #eaf6ef; color: #1f7a47; border-radius: 20px;
    padding: 3px 10px; font-size: 11px; font-weight: 600;
  }}
  .app-id {{ display: block; font-size: 9.5px; color: #9aa6b4; margin-top: 4px;
            font-family: monospace; }}
  table.grid {{ width: 100%; border-collapse: collapse; }}
  table.grid th {{
    background: #f2f5f9; text-align: left; padding: 8px 10px;
    font-size: 10.5px; text-transform: uppercase; letter-spacing: .4px;
    color: #5a6776; border-bottom: 1px solid #e4e9f0;
  }}
  table.grid td {{
    padding: 8px 10px; border-bottom: 1px solid #eef1f5; vertical-align: top;
  }}
  table.grid tr:nth-child(even) td {{ background: #fbfcfe; }}
  .c-num {{ width: 26px; color: #9aa6b4; }}
  .c-mid {{ text-align: center; white-space: nowrap; }}
  .badge {{
    display: inline-block; padding: 2px 9px; border-radius: 20px;
    font-size: 10px; font-weight: 700; letter-spacing: .3px;
  }}
  .badge-pass {{ background: #e6f6ec; color: #1f9d57; }}
  .badge-fail {{ background: #fdeaea; color: #d23a3a; }}
  .err {{ color: #b23636; font-family: monospace; font-size: 10px; word-break: break-word; }}
  a {{ color: #1565c0; text-decoration: none; }}
  .footer {{ margin-top: 28px; padding-top: 10px; border-top: 1px solid #e4e9f0;
            font-size: 10px; color: #9aa6b4; text-align: center; }}
</style>
</head>
<body>
  <div class="header">
    <h1>Laporan Compatibility Testing &mdash; Appium &times; BrowserStack</h1>
    <div class="sub">Suite: {html.escape(suites_label)}</div>
    <div class="build">Build: <b>{html.escape(build_name)}</b> &nbsp;|&nbsp; Dibuat: {generated}</div>
  </div>
  <div class="wrap">
    <table class="summary">
      <tr>
        <td style="width:170px; text-align:center;">{donut_svg(pass_rate)}</td>
        <td>
          <table class="cards" width="100%"><tr>
            <td style="width:25%"><div class="card"><div class="num num-total">{total}</div><div class="lbl">Total Device</div></div></td>
            <td style="width:25%"><div class="card"><div class="num num-pass">{passed}</div><div class="lbl">Passed</div></div></td>
            <td style="width:25%"><div class="card"><div class="num num-fail">{failed}</div><div class="lbl">Failed</div></div></td>
            <td style="width:25%"><div class="card"><div class="num num-total">{fmt_duration(total_duration)}</div><div class="lbl">Total Durasi</div></div></td>
          </tr></table>
        </td>
      </tr>
    </table>

    {''.join(suite_blocks)}

    <div class="footer">
      Laporan dibuat otomatis oleh pipeline Jenkins &bull; Appium Compatibility Testing
    </div>
  </div>
</body>
</html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="results")
    ap.add_argument("--out", default="report.pdf")
    ap.add_argument("--build-name", default=os.getenv("BUILD_NAME", "Local Run"))
    ap.add_argument(
        "--suites", nargs="*", default=None,
        help="Nama suite yang dimasukkan ke PDF. Kosong = semua suite."
    )
    args = ap.parse_args()

    suites_filter = set(args.suites) if args.suites else None
    suites_label  = " & ".join(sorted(args.suites)) if args.suites else "All Suites"

    items = load_results(args.results_dir, suites_filter)
    if not items:
        print(
            f"ERROR: tidak ada hasil untuk suite {args.suites} di '{args.results_dir}'.",
            file=sys.stderr
        )
        sys.exit(1)

    html_str = build_html(items, args.build_name, suites_label)

    # Tulis HTML ke file temp, langsung dihapus setelah PDF jadi
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", encoding="utf-8", delete=False
    ) as tmp:
        tmp.write(html_str)
        tmp_path = tmp.name

    try:
        cmd = [
            "wkhtmltopdf",
            "--enable-local-file-access",
            "--page-size", "A4",
            "--margin-top", "12mm", "--margin-bottom", "14mm",
            "--margin-left", "10mm", "--margin-right", "10mm",
            "--footer-right", "Halaman [page] dari [topage]",
            "--footer-font-size", "8",
            "--footer-spacing", "4",
            tmp_path, args.out,
        ]
        print("Convert ke PDF:", " ".join(cmd))
        try:
            subprocess.run(cmd, check=True)
        except FileNotFoundError:
            print("ERROR: wkhtmltopdf tidak ditemukan di PATH.", file=sys.stderr)
            sys.exit(2)
        print(f"PDF report: {args.out}")
    finally:
        # Hapus file HTML temp tanpa gagal meski PDF-nya error
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
