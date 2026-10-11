"""
reporter.py - Xuat bao cao loi ra Console, HTML va CSV.
Phu trach chinh: Dao Ngoc Hieu (2A202602081)
"""

from __future__ import annotations
import csv
import datetime
from pathlib import Path

from qc.models import ERROR, QCReport

# ---------------------------------------------------------------------------
# ANSI fallback (luon hoat dong, khong can thu vien ngoai)
# ---------------------------------------------------------------------------
_RESET  = "\033[0m"
_RED    = "\033[1;31m"
_YELLOW = "\033[1;33m"
_GREEN  = "\033[1;32m"
_CYAN   = "\033[1;36m"
_BOLD   = "\033[1m"

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box as rich_box
    from rich.panel import Panel
    _RICH_AVAILABLE = True
    # Force UTF-8 output + safe markup
    _console = Console(highlight=False, force_terminal=True, width=160)
except ImportError:
    _RICH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Console Reporter
# ---------------------------------------------------------------------------

def print_report_console(report: QCReport, show_warnings: bool = True) -> None:
    if _RICH_AVAILABLE:
        try:
            _print_rich(report, show_warnings)
            return
        except Exception:
            pass  # fallback to ANSI
    _print_ansi(report, show_warnings)


def _print_rich(report: QCReport, show_warnings: bool) -> None:
    _console.print()
    _console.print(Panel.fit(
        f"[bold cyan]BDD-QC Tool - Quality Check Report[/bold cyan]\n"
        f"Frames: [bold]{report.total_frames}[/bold]  "
        f"Objects: [bold]{report.total_objects}[/bold]  "
        f"[bold red]ERRORs: {report.error_count()}[/bold red]  "
        f"[bold yellow]WARNINGs: {report.warning_count()}[/bold yellow]",
        border_style="cyan",
    ))

    filtered = [e for e in report.errors if show_warnings or e.is_error()]
    if not filtered:
        _console.print("[bold green]OK - No issues detected![/bold green]\n")
        return

    table = Table(
        show_header=True,
        header_style="bold white on dark_blue",
        box=rich_box.ROUNDED,
        expand=True,
    )
    table.add_column("Frame",    style="cyan",    no_wrap=True, max_width=28)
    table.add_column("ID",       style="white",   max_width=20)
    table.add_column("Class",    style="magenta", max_width=14)
    table.add_column("Rule",     style="blue",    max_width=12)
    table.add_column("Severity", justify="center",max_width=9)
    table.add_column("Detail",   ratio=1)

    for err in filtered:
        sev_fmt = "[bold red]ERROR[/bold red]" if err.severity == ERROR \
            else "[bold yellow]WARN[/bold yellow]"
        short_id = (err.object_id[:17] + "...") if len(err.object_id) > 20 else err.object_id
        # Encode message to ASCII to avoid Windows console issues
        safe_msg = err.message.encode("ascii", "replace").decode("ascii")
        table.add_row(
            err.frame_name, short_id, err.category,
            err.rule_id, sev_fmt, safe_msg,
        )

    _console.print(table)
    _console.print()


def _print_ansi(report: QCReport, show_warnings: bool) -> None:
    print(f"\n{_BOLD}{_CYAN}=== BDD-QC Tool === Quality Check Report{_RESET}")
    print(
        f"Frames: {report.total_frames} | "
        f"Objects: {report.total_objects} | "
        f"{_RED}ERRORs: {report.error_count()}{_RESET} | "
        f"{_YELLOW}WARNINGs: {report.warning_count()}{_RESET}\n"
    )

    filtered = [e for e in report.errors if show_warnings or e.is_error()]
    if not filtered:
        print(f"{_GREEN}OK - No issues detected!{_RESET}\n")
        return

    hdr = f"{'Frame':<30} {'ID':<20} {'Class':<15} {'Rule':<12} {'Sev':<8} Detail"
    print(f"{_BOLD}{hdr}{_RESET}")
    print("-" * 110)
    for err in filtered:
        color = _RED if err.severity == ERROR else _YELLOW
        safe_msg = err.message.encode("ascii", "replace").decode("ascii")
        print(
            f"{err.frame_name:<30} "
            f"{err.object_id[:18]:<20} "
            f"{err.category:<15} "
            f"{err.rule_id:<12} "
            f"{color}{err.severity:<8}{_RESET} "
            f"{safe_msg}"
        )
    print()


# ---------------------------------------------------------------------------
# CSV Reporter
# ---------------------------------------------------------------------------

def generate_csv_str(report: QCReport) -> str:
    """Xuat noi dung bao cao dang CSV string."""
    import io
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "frame_name", "object_id", "category",
        "rule_id", "severity", "message",
    ])
    writer.writeheader()
    for err in report.errors:
        writer.writerow({
            "frame_name": err.frame_name,
            "object_id":  err.object_id,
            "category":   err.category,
            "rule_id":    err.rule_id,
            "severity":   err.severity,
            "message":    err.message,
        })
    return output.getvalue()


def export_csv(report: QCReport, output_path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    csv_content = generate_csv_str(report)
    path.write_text(csv_content, encoding="utf-8-sig")
    print(f"[OK] CSV saved: {path}")


# ---------------------------------------------------------------------------
# HTML Reporter
# ---------------------------------------------------------------------------

def generate_html_str(report: QCReport) -> str:
    """Xuat noi dung bao cao dang HTML string."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows_html = ""
    for err in report.errors:
        row_cls = "row-error" if err.severity == ERROR else "row-warning"
        badge   = ('<span class="badge-error">ERROR</span>' if err.severity == ERROR
                   else '<span class="badge-warning">WARN</span>')
        rows_html += (
            f'<tr class="{row_cls}">'
            f"<td>{_esc(err.frame_name)}</td>"
            f"<td>{_esc(err.object_id)}</td>"
            f"<td>{_esc(err.category)}</td>"
            f"<td><code>{_esc(err.rule_id)}</code></td>"
            f"<td>{badge}</td>"
            f"<td>{_esc(err.message)}</td>"
            f"</tr>\n"
        )

    empty_row = (
        '<tr><td colspan="6" class="empty">No issues detected!</td></tr>'
        if not rows_html else ""
    )

    stat_class = "value-ok" if not report.has_issues() else "value-error"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>BDD-QC Report - {now}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:#0f1117;color:#e2e8f0;padding:24px}}
h1{{font-size:1.5rem;color:#7dd3fc;margin-bottom:4px}}
.sub{{color:#94a3b8;font-size:.82rem;margin-bottom:20px}}
.stats{{display:flex;gap:14px;margin-bottom:22px;flex-wrap:wrap}}
.card{{background:#1e2535;border-radius:10px;padding:12px 18px;min-width:120px}}
.card .lbl{{font-size:.68rem;color:#64748b;text-transform:uppercase;letter-spacing:.06em}}
.card .val{{font-size:1.7rem;font-weight:700}}
.value-error{{color:#f87171}}.value-warn{{color:#fbbf24}}
.value-ok{{color:#34d399}}.value-neutral{{color:#7dd3fc}}
table{{width:100%;border-collapse:collapse;font-size:.82rem}}
thead{{background:#1e3a5f}}
th{{padding:9px 12px;text-align:left;color:#bae6fd;border-bottom:2px solid #2d4a7a}}
td{{padding:7px 12px;border-bottom:1px solid #1e293b;vertical-align:top}}
tr:hover td{{background:#1a2640}}
.row-error td{{border-left:3px solid #f87171}}
.row-warning td{{border-left:3px solid #fbbf24}}
.badge-error{{background:#7f1d1d;color:#fca5a5;padding:2px 7px;border-radius:4px;font-size:.73rem;font-weight:600}}
.badge-warning{{background:#78350f;color:#fde68a;padding:2px 7px;border-radius:4px;font-size:.73rem;font-weight:600}}
code{{background:#1e293b;padding:1px 5px;border-radius:3px;font-size:.78rem;color:#93c5fd}}
.empty{{text-align:center;padding:36px;color:#34d399;font-size:1.05rem}}
#search{{background:#1e2535;border:1px solid #334155;color:#e2e8f0;padding:7px 13px;
  border-radius:8px;font-size:.84rem;width:300px;margin-bottom:14px}}
</style>
</head>
<body>
<h1>BDD-QC Tool - Annotation Quality Report</h1>
<p class="sub">Generated: {now}</p>
<div class="stats">
  <div class="card"><div class="lbl">Frames</div><div class="val value-neutral">{report.total_frames}</div></div>
  <div class="card"><div class="lbl">Objects</div><div class="val value-neutral">{report.total_objects}</div></div>
  <div class="card"><div class="lbl">ERRORs</div><div class="val value-error">{report.error_count()}</div></div>
  <div class="card"><div class="lbl">WARNINGs</div><div class="val value-warn">{report.warning_count()}</div></div>
  <div class="card"><div class="lbl">Total Issues</div><div class="val {stat_class}">{len(report.errors)}</div></div>
</div>
<input id="search" type="text" placeholder="Filter by frame / ID / class / rule...">
<table id="tbl">
<thead><tr><th>Frame</th><th>Object ID</th><th>Class</th><th>Rule</th><th>Severity</th><th>Detail</th></tr></thead>
<tbody>
{empty_row}
{rows_html}
</tbody>
</table>
<script>
document.getElementById('search').addEventListener('input',function(){{
  const q=this.value.toLowerCase();
  document.querySelectorAll('#tbl tbody tr').forEach(r=>{{
    r.style.display=r.textContent.toLowerCase().includes(q)?'':'none';
  }});
}});
</script>
</body></html>"""


def export_html(report: QCReport, output_path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    html = generate_html_str(report)
    path.write_text(html, encoding="utf-8")
    print(f"[OK] HTML report saved: {path}")


def _esc(s: str) -> str:
    return (s.replace("&","&amp;").replace("<","&lt;")
             .replace(">","&gt;").replace('"',"&quot;"))
