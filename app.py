# streamlit_app.py
# Streamlit Resume (ATS Optimized) & Portfolio Builder using Gemini

import os
import io
import zipfile
import textwrap
from jinja2 import Template

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm

# ------------------ Gemini Optional ------------------
try:
    from google import genai
    GENAI_AVAILABLE = True
except Exception:
    GENAI_AVAILABLE = False

# ------------------ ATS-Friendly Resume HTML (Preview Only) ------------------
RESUME_HTML = """
<div style="font-family:Arial,Helvetica,sans-serif;background:#ffffff;padding:20px;color:#000;">
<h1>{{name}}</h1>
<h3>{{title}}</h3>
<p>{{email}} | {{phone}} | {{address}}</p>
<hr>

<h2>PROFESSIONAL SUMMARY</h2>
<p>{{summary}}</p>

<h2>SKILLS</h2>
<p>{{skills | join(', ')}}</p>

<h2>EXPERIENCE</h2>
<ul>{% for e in experience %}<li>{{e}}</li>{% endfor %}</ul>

<h2>PROJECTS</h2>
<ul>{% for p in projects %}<li>{{p}}</li>{% endfor %}</ul>

<h2>EDUCATION</h2>
<ul>{% for e in education %}<li>{{e}}</li>{% endfor %}</ul>

<h2>ACHIEVEMENTS</h2>
<ul>{% for a in awards %}<li>{{a}}</li>{% endfor %}</ul>
</div>
"""

# ------------------ ATS Resume PDF ------------------
def generate_resume_pdf_bytes(data):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    x = 25 * mm
    y = height - 25 * mm

    def heading(text):
        nonlocal y
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, text.upper())
        y -= 6 * mm

    def paragraph(text):
        nonlocal y
        c.setFont("Helvetica", 10)
        for line in textwrap.wrap(text, 95):
            c.drawString(x, y, line)
            y -= 5 * mm
        y -= 2 * mm

    def bullets(items):
        nonlocal y
        c.setFont("Helvetica", 10)
        for item in items:
            for line in textwrap.wrap(item, 90):
                c.drawString(x, y, "- " + line)
                y -= 5 * mm
        y -= 2 * mm

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(x, y, data["name"])
    y -= 7 * mm
    c.setFont("Helvetica", 11)
    c.drawString(x, y, data["title"])
    y -= 6 * mm
    c.setFont("Helvetica", 10)
    c.drawString(x, y, f"{data['email']} | {data['phone']} | {data['address']}")
    y -= 10 * mm

    heading("Professional Summary")
    paragraph(data["summary"])

    heading("Skills")
    paragraph(", ".join(data["skills"]))

    heading("Experience")
    bullets(data["experience"])

    heading("Projects")
    bullets(data["projects"])

    heading("Education")
    bullets(data["education"])

    heading("Achievements")
    bullets(data["awards"])

    c.save()
    buf.seek(0)
    return buf.read()

# ------------------ Beautiful Portfolio ------------------
def generate_portfolio_zip_bytes(data):
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{data['name']} | Portfolio</title>
<style>
body {{
    font-family: 'Segoe UI', sans-serif;
    background: linear-gradient(120deg,#f0f4ff,#ffffff);
    padding:40px;
}}
.container {{
    max-width:900px;
    margin:auto;
    background:#ffffff;
    padding:40px;
    border-radius:16px;
    box-shadow:0 10px 30px rgba(0,0,0,0.1);
}}
h1 {{ color:#1a73e8; }}
.card {{
    background:#f5f8ff;
    padding:20px;
    border-radius:12px;
    margin:20px 0;
}}
ul {{ padding-left:20px; }}
</style>
</head>
<body>
<div class="container">
<h1>{data['name']}</h1>
<h3>{data['title']}</h3>
<p>{data['email']} | {data['phone']} | {data['address']}</p>

<div class="card"><h2>About Me</h2><p>{data['summary']}</p></div>
<div class="card"><h2>Skills</h2><p>{', '.join(data['skills'])}</p></div>
<div class="card"><h2>Experience</h2><ul>{''.join(f'<li>{e}</li>' for e in data['experience'])}</ul></div>
<div class="card"><h2>Projects</h2><ul>{''.join(f'<li>{p}</li>' for p in data['projects'])}</ul></div>
<div class="card"><h2>Education</h2><ul>{''.join(f'<li>{e}</li>' for e in data['education'])}</ul></div>
<div class="card"><h2>Achievements</h2><ul>{''.join(f'<li>{a}</li>' for a in data['awards'])}</ul></div>
</div>
</body>
</html>
"""
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w") as z:
        z.writestr("index.html", html)
    mem.seek(0)
    return mem.read()

# ------------------ Gemini ATS Summary ------------------
def generate_ai_summary(skills, experience, fallback):
    if not GENAI_AVAILABLE:
        return fallback
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        return fallback
    try:
        client = genai.Client(api_key=key)
        prompt = f"""
Create an ATS-optimized professional resume summary.
Use strong action verbs and keywords.
Skills: {skills}
Experience: {experience}
Limit to 3 sentences.
"""
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return resp.text.strip()
    except Exception:
        return fallback

# ------------------ Streamlit UI ------------------
st.set_page_config("ATS Resume & Portfolio Builder", layout="wide")
st.title("ATS Resume & Professional Portfolio Builder")

col1, col2 = st.columns([2, 1])

with col1:
    name = st.text_input("Full Name")
    title = st.text_input("Professional Title")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    address = st.text_input("Location")

    summary = st.text_area("Professional Summary")
    skills = st.text_input("Skills (comma separated)")
    experience = st.text_area("Experience (one per line)")
    projects = st.text_area("Projects (one per line)")
    education = st.text_area("Education (one per line)")
    awards = st.text_area("Achievements (one per line)")

    use_ai = st.checkbox("Use Gemini AI (ATS Optimized Summary)")
    generate = st.button("Generate Resume & Portfolio")

with col2:
    preview = st.empty()

if generate:
    data = {
        "name": name,
        "title": title,
        "email": email,
        "phone": phone,
        "address": address,
        "summary": summary,
        "skills": [s.strip() for s in skills.split(",") if s.strip()],
        "experience": experience.splitlines(),
        "projects": projects.splitlines(),
        "education": education.splitlines(),
        "awards": awards.splitlines(),
    }

    if use_ai:
        data["summary"] = generate_ai_summary(skills, experience, summary)

    preview.markdown(
        Template(RESUME_HTML).render(**data),
        unsafe_allow_html=True
    )

    st.download_button(
        "Download ATS Resume (PDF)",
        generate_resume_pdf_bytes(data),
        file_name="ATS_Resume.pdf",
        mime="application/pdf",
    )

    st.download_button(
        "Download Portfolio (ZIP)",
        generate_portfolio_zip_bytes(data),
        file_name="Portfolio.zip",
        mime="application/zip",
    )
