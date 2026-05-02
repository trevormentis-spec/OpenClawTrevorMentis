"""Render the TREVOR assessment JSON to PDF with embedded diagrams."""
import json, os, sys
from jinja2 import Template
from weasyprint import HTML

WORKSPACE = "/home/ubuntu/.openclaw/workspace"

with open(f"{WORKSPACE}/exports/full-assessment.json") as f:
    data = json.load(f)

with open(f"{WORKSPACE}/exports/templates/assessment-report.html") as f:
    template_str = f.read()

# Add a |capitalize filter
def capitalize(s):
    return s.replace("_", " ").title()

template = Template(template_str)
template.environment.filters['capitalize'] = capitalize

# Fix image paths to use absolute workspace paths
import re
image_dir = f"{WORKSPACE}/exports/images/"

def fix_img_paths(html):
    return html.replace('src="exports/images/', f'src="file://{WORKSPACE}/exports/images/').replace("src='exports/images/", f"src='file://{WORKSPACE}/exports/images/")

html = template.render(**data)
html = fix_img_paths(html)

html_path = f"{WORKSPACE}/exports/full-assessment-2026-05-01.html"
pdf_path = f"{WORKSPACE}/exports/pdfs/full-assessment-2026-05-01.pdf"

with open(html_path, "w") as f:
    f.write(html)

print("Rendering PDF with WeasyPrint...")
HTML(filename=html_path).write_pdf(pdf_path)

size_kb = os.path.getsize(pdf_path) / 1024
print(f"✅ PDF generated: {pdf_path}")
print(f"   Size: {size_kb:.0f} KB")

# Also check pages
import subprocess
result = subprocess.run(["python3", "-c", f"""
from PyPDF2 import PdfReader
r = PdfReader('{pdf_path}')
print(f'   Pages: {{len(r.pages)}}')
"""], capture_output=True, text=True)
print(result.stdout if result.stdout else f"   Pages: (PyPDF2 not installed)")
