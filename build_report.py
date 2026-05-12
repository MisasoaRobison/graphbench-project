"""Build report.html (and optionally report.pdf) from report.md.

Pure Python — no pandoc required. Produces a print-ready HTML; you can
then save it as PDF via your browser (Ctrl+P → "Save as PDF").

If `weasyprint` is installed (`pip install weasyprint`), this script also
writes ``report.pdf`` directly.

Usage:
    python build_report.py            # writes report.html (+ pdf if possible)
    python build_report.py --md path  # custom input
"""

import argparse
import os
import sys


CSS = """
@page { size: A4; margin: 1.6cm 1.8cm; }
body {
    font-family: "Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.35;
    color: #111;
}
h1 { font-size: 16pt; margin: 0 0 0.4em 0; }
h2 { font-size: 12pt; margin-top: 1.1em; border-bottom: 1px solid #888; padding-bottom: 0.1em; }
h3 { font-size: 11pt; margin-top: 0.7em; }
p, li { margin: 0.3em 0; }
ul { margin: 0.2em 0 0.4em 1.2em; padding: 0; }
table { border-collapse: collapse; margin: 0.4em 0; font-size: 10pt; }
th, td { border: 1px solid #888; padding: 0.18em 0.45em; }
th { background: #eee; }
code { font-family: "Consolas", monospace; background: #f4f4f4; padding: 0 2px; font-size: 9.5pt; }
pre { background: #f4f4f4; padding: 0.4em 0.6em; font-size: 9pt; line-height: 1.25;
      border-left: 3px solid #888; overflow-x: auto; }
hr { border: none; border-top: 1px solid #aaa; margin: 0.8em 0; }
.cover { text-align: center; margin: 0.4em 0 1.0em 0; }
.cover-info table { margin: 0 auto; }
"""


def md_to_html(md_text):
    """Render markdown to HTML using the `markdown` package if available,
    otherwise a minimal hand-written renderer for our report's subset."""
    try:
        import markdown  # noqa: F401
        from markdown import markdown as _render
        return _render(md_text, extensions=["tables", "fenced_code"])
    except ImportError:
        pass

    # Minimal fallback: handle headings, lists, tables, code blocks
    out = []
    in_code = False
    in_list = False
    in_table = False
    table_header_done = False
    for line in md_text.splitlines():
        s = line.rstrip()
        if s.startswith("```"):
            if in_code:
                out.append("</pre>")
                in_code = False
            else:
                out.append("<pre>")
                in_code = True
            continue
        if in_code:
            out.append(_escape(line))
            continue
        if not s.strip():
            if in_list:
                out.append("</ul>")
                in_list = False
            if in_table:
                out.append("</table>")
                in_table = False
                table_header_done = False
            out.append("")
            continue
        if s.startswith("# "):
            out.append(f"<h1>{_escape(s[2:])}</h1>")
            continue
        if s.startswith("## "):
            out.append(f"<h2>{_escape(s[3:])}</h2>")
            continue
        if s.startswith("### "):
            out.append(f"<h3>{_escape(s[4:])}</h3>")
            continue
        if s.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(s[2:])}</li>")
            continue
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not in_table:
                out.append("<table>")
                in_table = True
                table_header_done = False
            if all(set(c) <= set("-: ") and c for c in cells):
                table_header_done = True
                continue
            tag = "th" if not table_header_done else "td"
            row = "".join(f"<{tag}>{_inline(c)}</{tag}>" for c in cells)
            out.append(f"<tr>{row}</tr>")
            continue
        # default: paragraph
        if in_list:
            out.append("</ul>")
            in_list = False
        if in_table:
            out.append("</table>")
            in_table = False
            table_header_done = False
        if s.startswith("---"):
            out.append("<hr/>")
            continue
        out.append(f"<p>{_inline(s)}</p>")
    if in_list:
        out.append("</ul>")
    if in_table:
        out.append("</table>")
    return "\n".join(out)


def _escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(s):
    s = _escape(s)
    # bold **x**
    import re
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    # italic *x*
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    # code `x`
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--md", default="report.md")
    parser.add_argument("--html", default="report.html")
    parser.add_argument("--pdf", default="report.pdf")
    args = parser.parse_args()

    with open(args.md, "r", encoding="utf-8") as f:
        md = f.read()
    body = md_to_html(md)
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>GraphBench Report</title>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )
    with open(args.html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {args.html}  ({os.path.getsize(args.html)} bytes)")

    # Optional PDF via weasyprint
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(args.pdf)
        print(f"Wrote {args.pdf}")
    except ImportError:
        print("(weasyprint not installed; open report.html and print to PDF)")
    except Exception as e:
        print(f"(PDF generation failed: {e}; open report.html and print to PDF)")


if __name__ == "__main__":
    main()
