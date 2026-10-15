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
    """Xuat noi dung bao cao dang HTML string (Giao dien Dashboard Dark Glassmorphism hien dai)."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_issues = len(report.errors)
    pass_rate = 100.0 if report.total_objects == 0 else max(0.0, 100.0 - (total_issues / report.total_objects * 100))

    rows_html = ""
    for err in report.errors:
        row_cls = "row-error" if err.severity == ERROR else "row-warning"
        badge = (
            '<span class="badge badge-error">🔴 ERROR</span>'
            if err.severity == ERROR
            else '<span class="badge badge-warning">🟡 WARNING</span>'
        )
        rows_html += (
            f'<tr class="{row_cls}" data-severity="{err.severity}" data-rule="{_esc(err.rule_id)}">'
            f'<td class="cell-frame"><code>{_esc(err.frame_name)}</code></td>'
            f'<td class="cell-id"><strong>{_esc(err.object_id)}</strong></td>'
            f'<td><span class="chip-class">{_esc(err.category)}</span></td>'
            f'<td><span class="chip-rule">{_esc(err.rule_id)}</span></td>'
            f'<td class="text-center">{badge}</td>'
            f'<td class="cell-detail">{_esc(err.message)}</td>'
            f'</tr>\n'
        )

    empty_row = (
        '<tr><td colspan="6" class="empty">🎉 Chúc mừng! Dữ liệu nhãn hoàn toàn sạch sẽ, không có lỗi nào.</td></tr>'
        if not rows_html
        else ""
    )

    stat_class = "value-ok" if not report.has_issues() else "value-error"
    pass_badge = "badge-emerald" if pass_rate >= 90 else "badge-warning"

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BDD-QC Tool - Báo Cáo Chất Lượng Gán Nhãn ({now})</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
    --bg-dark: #0b0f19;
    --card-bg: rgba(26, 34, 52, 0.65);
    --card-border: rgba(255, 255, 255, 0.08);
    --text-primary: #f8fafc;
    --text-muted: #94a3b8;
    --cyan: #38bdf8;
    --indigo: #818cf8;
    --rose: #f43f5e;
    --amber: #fbbf24;
    --emerald: #34d399;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    background: radial-gradient(circle at 15% 15%, #131c31 0%, #0b0f19 75%);
    color: var(--text-primary);
    padding: 30px 40px;
    min-height: 100vh;
}}
code, pre {{ font-family: 'JetBrains Mono', monospace; }}

/* Header */
.header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--card-border);
    margin-bottom: 24px;
}}
.header-title {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.header-icon {{
    font-size: 2.2rem;
    background: rgba(56, 189, 248, 0.1);
    padding: 8px 12px;
    border-radius: 12px;
    border: 1px solid rgba(56, 189, 248, 0.25);
}}
h1 {{
    font-size: 1.65rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.sub {{ color: var(--text-muted); font-size: 0.85rem; margin-top: 4px; }}
.header-meta {{
    display: flex;
    gap: 10px;
    align-items: center;
}}
.btn-print {{
    background: linear-gradient(135deg, #0284c7, #4f46e5);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
    transition: all 0.2s;
}}
.btn-print:hover {{ transform: translateY(-1px); box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4); }}

/* KPI Cards */
.stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-bottom: 26px;
}}
.card {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    backdrop-filter: blur(12px);
    border-radius: 14px;
    padding: 16px 20px;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.3);
    transition: transform 0.2s, border-color 0.2s;
}}
.card:hover {{ transform: translateY(-2px); border-color: rgba(255, 255, 255, 0.15); }}
.card .lbl {{
    font-size: 0.72rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 700;
    margin-bottom: 6px;
}}
.card .val {{ font-size: 1.85rem; font-weight: 800; line-height: 1.1; }}
.value-error {{ color: var(--rose); }}
.value-warn {{ color: var(--amber); }}
.value-ok {{ color: var(--emerald); }}
.value-neutral {{ color: var(--cyan); }}
.value-indigo {{ color: var(--indigo); }}

/* Filter Bar */
.filter-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 14px;
    margin-bottom: 18px;
}}
.search-box {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    color: var(--text-primary);
    padding: 10px 16px;
    border-radius: 10px;
    font-size: 0.88rem;
    width: 340px;
    max-width: 100%;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
}}
.search-box:focus {{
    border-color: var(--cyan);
    box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
}}
.filter-chips {{
    display: flex;
    gap: 8px;
}}
.chip-btn {{
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid var(--card-border);
    color: var(--text-muted);
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}}
.chip-btn:hover, .chip-btn.active {{
    background: rgba(56, 189, 248, 0.15);
    color: var(--cyan);
    border-color: rgba(56, 189, 248, 0.4);
}}

/* Table */
.table-container {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    overflow: hidden;
    backdrop-filter: blur(12px);
    box-shadow: 0 6px 25px -4px rgba(0, 0, 0, 0.35);
}}
table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}}
thead {{
    background: rgba(30, 41, 59, 0.8);
    border-bottom: 1px solid var(--card-border);
}}
th {{
    padding: 12px 16px;
    text-align: left;
    color: #bae6fd;
    font-weight: 700;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
td {{
    padding: 11px 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    vertical-align: middle;
}}
tr:hover td {{ background: rgba(56, 189, 248, 0.04); }}
.row-error td:first-child {{ border-left: 4px solid var(--rose); }}
.row-warning td:first-child {{ border-left: 4px solid var(--amber); }}

.badge {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
}}
.badge-error {{ background: rgba(239, 68, 68, 0.18); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); }}
.badge-warning {{ background: rgba(245, 158, 11, 0.18); color: #fde68a; border: 1px solid rgba(245, 158, 11, 0.4); }}
.chip-class {{
    background: rgba(168, 85, 247, 0.15);
    color: #d8b4fe;
    border: 1px solid rgba(168, 85, 247, 0.3);
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.76rem;
    font-weight: 600;
}}
.chip-rule {{
    background: rgba(56, 189, 248, 0.12);
    color: #7dd3fc;
    border: 1px solid rgba(56, 189, 248, 0.3);
    padding: 2px 8px;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    font-weight: 600;
}}
.cell-frame code {{ color: #e2e8f0; font-size: 0.8rem; }}
.cell-id {{ color: #f1f5f9; }}
.cell-detail {{ color: #cbd5e1; line-height: 1.45; }}
.text-center {{ text-align: center; }}
.empty {{ text-align: center; padding: 48px; color: var(--emerald); font-size: 1.1rem; font-weight: 600; }}

/* Footer */
.footer {{
    margin-top: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #64748b;
    font-size: 0.78rem;
    border-top: 1px solid var(--card-border);
    padding-top: 16px;
}}
</style>
</head>
<body>

<div class="header">
    <div class="header-title">
        <div class="header-icon">🛡️</div>
        <div>
            <h1>BDD-QC Tool — Quality Control Report</h1>
            <p class="sub">Hệ thống Linter & Kiểm tra chất lượng gán nhãn BDD100K & YOLO (Mã đề: N2-04A)</p>
        </div>
    </div>
    <div class="header-meta">
        <button class="btn-print" onclick="window.print()">🖨️ In / Lưu PDF</button>
    </div>
</div>

<div class="stats">
    <div class="card">
        <div class="lbl">🖼️ Tổng Frames</div>
        <div class="val value-neutral">{report.total_frames:,}</div>
    </div>
    <div class="card">
        <div class="lbl">🎯 Tổng Objects</div>
        <div class="val value-indigo">{report.total_objects:,}</div>
    </div>
    <div class="card">
        <div class="lbl">🔴 Lỗi Nghiêm Trọng</div>
        <div class="val value-error">{report.error_count():,}</div>
    </div>
    <div class="card">
        <div class="lbl">🟡 Cảnh Báo</div>
        <div class="val value-warn">{report.warning_count():,}</div>
    </div>
    <div class="card">
        <div class="lbl">🛡️ Tỷ Lệ Đạt Chuẩn</div>
        <div class="val value-ok">{pass_rate:.1f}%</div>
    </div>
</div>

<div class="filter-bar">
    <input id="search" class="search-box" type="text" placeholder="🔍 Tìm theo Frame, Object ID, Class, Rule...">
    <div class="filter-chips">
        <button class="chip-btn active" data-filter="all">Tất cả ({total_issues})</button>
        <button class="chip-btn" data-filter="ERROR">🔴 ERROR ({report.error_count()})</button>
        <button class="chip-btn" data-filter="WARNING">🟡 WARNING ({report.warning_count()})</button>
    </div>
</div>

<div class="table-container">
<table id="tbl">
<thead>
    <tr>
        <th>Frame</th>
        <th>Object ID</th>
        <th>Class</th>
        <th>Rule</th>
        <th class="text-center">Mức độ</th>
        <th>Chi tiết lỗi vi phạm</th>
    </tr>
</thead>
<tbody>
{empty_row}
{rows_html}
</tbody>
</table>
</div>

<div class="footer">
    <div>🕒 Xuất báo cáo lúc: <code>{now}</code> · Nhóm thực hiện: <strong>N2-04A</strong> (Đào Ngọc Hiếu, Đoàn Văn Thắng, Nguyễn Thanh Đức, Hoàng Công Chứ, Trần Thị Thủy Tiên)</div>
    <div>BDD-QC Suite v2.5 · VinUni AI Workshop</div>
</div>

<script>
const searchInput = document.getElementById('search');
const filterBtns = document.querySelectorAll('.chip-btn');
let currentFilter = 'all';

function filterTable() {{
    const query = searchInput.value.toLowerCase();
    const rows = document.querySelectorAll('#tbl tbody tr');
    rows.forEach(r => {{
        if (r.classList.contains('empty')) return;
        const sev = r.getAttribute('data-severity');
        const matchesSev = (currentFilter === 'all') || (sev === currentFilter);
        const matchesQuery = !query || r.textContent.toLowerCase().includes(query);
        r.style.display = (matchesSev && matchesQuery) ? '' : 'none';
    }});
}}

searchInput.addEventListener('input', filterTable);

filterBtns.forEach(btn => {{
    btn.addEventListener('click', () => {{
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.getAttribute('data-filter');
        filterTable();
    }});
}});
</script>
</body>
</html>"""


def export_html(report: QCReport, output_path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    html = generate_html_str(report)
    path.write_text(html, encoding="utf-8")
    print(f"[OK] HTML report saved: {path}")


def _esc(s: str) -> str:
    return (s.replace("&","&amp;").replace("<","&lt;")
             .replace(">","&gt;").replace('"',"&quot;"))
