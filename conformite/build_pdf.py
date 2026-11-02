"""Assemble les documents du dossier en un PDF : ../.venv-cad/bin/python build_pdf.py (depuis conformite/)."""
import markdown, glob, os, re, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
files = sorted(glob.glob(os.path.join(HERE, "[0A-H]*.md")))
parts = []
for f in files:
    html = markdown.markdown(open(f).read(), extensions=["tables", "fenced_code"])
    html = re.sub(r'href="([\w-]+)\.md"', lambda m: 'href="#%s"' % m.group(1), html)
    parts.append(f'<section id="{os.path.basename(f)[:-3]}">{html}</section>')
css = """
@page{size:A4;margin:15mm 14mm 16mm}
body{font-family:"Avenir Next",Avenir,"Helvetica Neue",Arial,sans-serif;font-size:9.6pt;line-height:1.45;color:#1d1b18}
h1{font-family:"Iowan Old Style",Georgia,serif;color:#173a2c;font-size:20pt;border-bottom:2px solid #a97f3c;padding-bottom:4px}
h2{font-family:"Iowan Old Style",Georgia,serif;color:#173a2c;font-size:13.5pt;margin-top:16px}
h3{color:#173a2c;font-size:11pt}
section{break-before:page}
table{width:100%;border-collapse:collapse;margin:6px 0 10px;font-size:8.4pt}
th{background:#173a2c;color:#fff;text-align:left;padding:4px 5px}
td{border-bottom:1px solid #e3dccf;padding:3px 5px;vertical-align:top}
tr{break-inside:avoid}
blockquote{margin:8px 0;padding:6px 10px;background:#f7f3ec;border-left:3px solid #a97f3c}
code,pre{font-family:Menlo,monospace;font-size:8pt;background:#f7f3ec}
pre{padding:8px;white-space:pre-wrap}
hr{border:none;border-top:1px solid #e3dccf;margin:14px 0}
.cover{height:250mm;display:flex;flex-direction:column;justify-content:center}
.cover h1{font-size:34pt;border:none}
.cover p{font-size:12pt;color:#6b645a}
"""
cover = """<div class="cover"><p style="letter-spacing:4px;color:#a97f3c;text-transform:uppercase;font-size:9pt">INOMA</p>
<h1>AYAH AY-R1<br>Dossier de conformité et de commercialisation</h1>
<p>Version de travail 0.1 — 2 novembre 2026</p>
<p><b>Base de travail, pas une attestation de conformité ni un avis juridique.</b><br>
Toutes les mentions [À COMPLÉTER], [À VÉRIFIER] et [PREUVE] doivent être traitées avant signature de la déclaration UE.</p></div>"""
tmp = os.path.join(HERE, "_dossier.html")
open(tmp, "w").write(f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>AYAH — Dossier de conformité</title><style>{css}</style></head><body>{cover}{''.join(parts)}</body></html>")
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={os.path.join(HERE, 'AYAH_Dossier_conformite.pdf')}", f"file://{tmp}"], stderr=subprocess.DEVNULL)
os.remove(tmp)
print("PDF généré")
