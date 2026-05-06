"""
Gradio Web UI for Resume & Cover Letter Tailoring Agent
Run: python app.py
"""

import gradio as gr
import json
import os
from agent import run_agent
from pdf_export import generate_resume_pdf, generate_cover_letter_pdf
from dotenv import load_dotenv
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# ─── PDF EXTRACTION ───────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        import fitz
        doc = fitz.open(pdf_path)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text.strip()
    except ImportError:
        return "❌ pymupdf not installed. Run: pip install pymupdf"
    except Exception as e:
        return f"❌ Could not read PDF: {e}"


def handle_pdf_upload(pdf_file):
    if pdf_file is None:
        return gr.update(), "_Upload a PDF to auto-fill the text below, or paste directly._"
    text = extract_text_from_pdf(pdf_file)
    if text.startswith("❌"):
        return gr.update(), text
    return gr.update(value=text), f"✅ PDF extracted — {len(text.split())} words loaded."


# ─── CSS ──────────────────────────────────────────────────────────────────────

custom_css = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg: #f8fafc;
    --surface: #ffffff;
    --border: #e2e8f0;
    --accent: #2563eb;
    --accent-light: #eff6ff;
    --accent2: #7c3aed;
    --success: #059669;
    --warning: #d97706;
    --text: #0f172a;
    --muted: #64748b;
    --card-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
    --card-shadow-hover: 0 4px 12px rgba(37,99,235,0.12), 0 2px 6px rgba(0,0,0,0.08);
}

html, body {
    background: var(--bg) !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text) !important;
}

.gradio-container {
    max-width: 1280px !important;
    margin: 0 auto !important;
    background: var(--bg) !important;
}

/* ── Header ─────────────────────────────────────────────── */
#app-header {
    background: white;
    border-bottom: 1px solid var(--border);
    padding: 28px 40px;
    margin-bottom: 32px;
    display: flex;
    align-items: center;
    gap: 16px;
}
#header-badge {
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: white;
    font-size: 1.5rem;
    width: 52px;
    height: 52px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 4px 12px rgba(37,99,235,0.3);
}
#header-text h1 {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text);
    margin: 0 0 4px;
    letter-spacing: -0.5px;
}
#header-text p {
    color: var(--muted);
    font-size: 0.9rem;
    margin: 0;
    font-weight: 400;
}

/* ── Pipeline Steps ──────────────────────────────────────── */
#pipeline-bar {
    display: flex;
    gap: 0;
    background: white;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 24px;
    margin-bottom: 28px;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    gap: 4px;
}
.pipeline-step {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--muted);
    padding: 6px 12px;
    border-radius: 8px;
}
.pipeline-step .num {
    width: 22px; height: 22px;
    border-radius: 50%;
    background: var(--border);
    color: var(--muted);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.75rem; font-weight: 600;
}
.pipeline-arrow { color: #cbd5e1; font-size: 0.9rem; }

/* ── Section Labels ──────────────────────────────────────── */
.section-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 8px;
    display: block;
}

/* ── Cards ───────────────────────────────────────────────── */
.input-card, .output-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    box-shadow: var(--card-shadow);
    margin-bottom: 16px;
}

/* ── Inputs ──────────────────────────────────────────────── */
textarea, input[type="text"], input[type="password"] {
    background: var(--bg) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.85rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    padding: 12px !important;
}
textarea:focus, input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
    outline: none !important;
}

/* ── Slider ──────────────────────────────────────────────── */
input[type="range"] {
    accent-color: var(--accent);
    height: 4px;
}
.slider-label {
    background: var(--accent-light);
    color: var(--accent);
    font-weight: 600;
    font-size: 0.85rem;
    padding: 4px 12px;
    border-radius: 20px;
    display: inline-block;
    margin-left: 8px;
}

/* ── Run Button ───────────────────────────────────────────── */
button.primary {
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
    border: none !important;
    color: white !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 14px 28px !important;
    border-radius: 12px !important;
    width: 100% !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 14px rgba(37,99,235,0.3) !important;
    letter-spacing: 0.01em !important;
}
button.primary:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(37,99,235,0.4) !important;
}
button.primary:active {
    transform: translateY(0) !important;
}

/* ── Status Bar ───────────────────────────────────────────── */
#status-bar {
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.9rem;
    font-weight: 500;
}

/* ── Tabs ─────────────────────────────────────────────────── */
.tab-nav {
    border-bottom: 2px solid var(--border) !important;
    background: transparent !important;
    padding: 0 !important;
    margin-bottom: 16px !important;
}
.tab-nav button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    padding: 10px 18px !important;
    border: none !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
    transition: all 0.2s !important;
    border-radius: 0 !important;
}
.tab-nav button:hover { color: var(--accent) !important; }
.tab-nav button.selected {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
    font-weight: 600 !important;
}

/* ── Project Cards ────────────────────────────────────────── */
.project-card {
    background: white;
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 14px;
    box-shadow: var(--card-shadow);
    transition: box-shadow 0.2s;
}
.project-card:hover { box-shadow: var(--card-shadow-hover); }
.project-title { font-weight: 700; font-size: 1rem; color: var(--text); margin-bottom: 6px; }
.project-desc { color: var(--muted); font-size: 0.88rem; line-height: 1.5; margin-bottom: 10px; }
.tech-badge {
    display: inline-block;
    background: var(--accent-light);
    color: var(--accent);
    font-size: 0.75rem;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 20px;
    margin: 2px 3px 2px 0;
}
.project-meta { font-size: 0.82rem; color: var(--success); font-weight: 500; margin-top: 8px; }
.project-why { font-size: 0.83rem; color: var(--accent2); font-style: italic; margin-top: 4px; }

/* ── Score Badges ─────────────────────────────────────────── */
.score-high { color: var(--success); font-weight: 700; }
.score-mid  { color: var(--warning); font-weight: 700; }
.score-low  { color: #dc2626; font-weight: 700; }

/* ── Footer ───────────────────────────────────────────────── */
#app-footer {
    text-align: center;
    padding: 24px;
    color: var(--muted);
    font-size: 0.82rem;
    border-top: 1px solid var(--border);
    margin-top: 40px;
}

/* File upload */
.file-preview {
    border-radius: 10px !important;
    border: 1.5px dashed var(--border) !important;
    background: var(--bg) !important;
}

/* Markdown output */
.prose { line-height: 1.65 !important; }
"""

SAMPLE_RESUME = """Jane Smith
jane@email.com | linkedin.com/in/janesmith | San Francisco, CA | github.com/janesmith

EXPERIENCE

Software Engineer | TechCorp | 2021–Present
• Built and maintained REST APIs using Python/FastAPI serving 100k+ daily active users
• Led migration of monolithic app to microservices, cutting deployment time by 60%
• Implemented Redis caching layer reducing database load by 40%
• Mentored 2 junior engineers; conducted weekly code reviews

Junior Developer | StartupXYZ | 2019–2021
• Developed React dashboard components used by 500+ enterprise clients
• Wrote comprehensive unit and integration tests achieving 80% coverage with pytest
• Integrated third-party payment APIs (Stripe) for subscription billing

SKILLS
Python, FastAPI, React, PostgreSQL, Docker, Redis, AWS (EC2, S3), Git, CI/CD, pytest

EDUCATION
B.S. Computer Science | State University | 2019 | GPA 3.7"""

SAMPLE_JD = """Senior Software Engineer - Backend
Acme Corp | San Francisco, CA | Full-time

We are looking for a Senior Backend Engineer to join our fintech infrastructure team.

Requirements:
• 4+ years Python backend development
• Microservices and distributed systems experience
• Strong PostgreSQL and Redis knowledge
• Docker + Kubernetes in production
• CI/CD experience (GitHub Actions, CircleCI)
• Experience with message queues (Kafka, RabbitMQ)

Nice to Have: Kafka, AWS/GCP, fintech/payments experience, gRPC
Compensation: $160k-$200k + equity + benefits"""


# ─── FORMAT PROJECT SUGGESTIONS ───────────────────────────────────────────────

def format_projects_html(projects: list) -> str:
    if not projects:
        return "<p style='color:#64748b;font-style:italic;'>No project suggestions generated.</p>"

    html = ""
    accent_colors = ["#2563eb", "#7c3aed", "#059669"]
    for idx, p in enumerate(projects):
        color = accent_colors[idx % len(accent_colors)]
        tech_badges = "".join(
            f'<span class="tech-badge">{t}</span>'
            for t in p.get("tech_stack", [])
        )
        skills = ", ".join(p.get("skills_demonstrated", []))
        html += f"""
        <div class="project-card" style="border-left-color:{color}">
            <div class="project-title">🛠 {p.get('title', 'Project')}</div>
            <div class="project-desc">{p.get('description', '')}</div>
            <div style="margin-bottom:8px">{tech_badges}</div>
            <div class="project-meta">⏱ {p.get('estimated_time', '')}  ·  Skills: {skills}</div>
            <div class="project-why">💡 {p.get('why_it_helps', '')}</div>
            {"<div style='margin-top:8px;font-size:0.8rem;color:#94a3b8;'>📁 " + p.get('github_structure','') + "</div>" if p.get('github_structure') else ""}
        </div>
        """
    return html


# ─── PROCESSING ───────────────────────────────────────────────────────────────

def process(resume, job_description, cover_letter_words, progress=gr.Progress()):
    no_files = (None, None)

    if not resume.strip():
        return "❌ Please paste your resume or upload a PDF.", "", "", "", "", "<p>No results yet.</p>", *no_files
    if not job_description.strip():
        return "❌ Please paste the job description.", "", "", "", "", "<p>No results yet.</p>", *no_files

    try:
        progress(0.05, desc="🔍 Analyzing job description...")
        results = run_agent(
            resume, job_description,
            HF_TOKEN,
            cover_letter_words=int(cover_letter_words)
        )
        progress(0.88, desc="📄 Generating PDFs...")

        jd   = results.get("jd_analysis", {})
        gaps = results.get("gap_analysis", {})

        # ── Analysis tab ──────────────────────────────────────────────────────
        match_count   = len(gaps.get("matching_skills", []))
        missing_count = len(gaps.get("missing_skills", []))

        jd_summary = f"""### 🎯 {jd.get('job_title', 'Role')} at {jd.get('company', 'Company')}

**Experience Required:** {jd.get('years_experience', 'N/A')}  ·  **Tone:** {jd.get('tone', 'N/A')}

**Required Skills:**
{chr(10).join(f"- {s}" for s in jd.get('required_skills', []))}

**Preferred Skills:**
{chr(10).join(f"- {s}" for s in jd.get('preferred_skills', []))}

**Keywords:** `{'`  `'.join(jd.get('keywords', []))}`

---

### 📊 Gap Analysis

**✅ Matching Skills ({match_count}):** {', '.join(gaps.get('matching_skills', [])) or 'None identified'}

**⚠️ Missing Skills ({missing_count}):** {', '.join(gaps.get('missing_skills', [])) or 'None — excellent match!'}

**💡 Strongest Selling Points:**
{chr(10).join(f"- {s}" for s in gaps.get('strongest_selling_points', []))}

**📌 Suggested Emphasis:**
{chr(10).join(f"- {s}" for s in gaps.get('suggested_emphasis', []))}"""

        # ── Review tab ────────────────────────────────────────────────────────
        review = results.get("review", {})
        rs = review.get("resume_score", 0)
        cs = review.get("cover_letter_score", 0)

        def score_class(n):
            if n >= 80: return "score-high"
            if n >= 60: return "score-mid"
            return "score-low"

        review_md = f"""### Quality Review

| Metric | Score |
|--------|-------|
| Resume Score | **{rs}/100** |
| Cover Letter Score | **{cs}/100** |
| ATS Keyword Coverage | **{str(review.get('ats_keyword_coverage','N/A')).capitalize()}** |

---

**Resume Strengths:** {' · '.join(f"✅ {s}" for s in review.get('resume_strengths', []))}

**Resume Improvements:** {' · '.join(f"⚠️ {s}" for s in review.get('resume_improvements', []))}

**Cover Letter Strengths:** {' · '.join(f"✅ {s}" for s in review.get('cover_letter_strengths', []))}

**Cover Letter Improvements:** {' · '.join(f"⚠️ {s}" for s in review.get('cover_letter_improvements', []))}

---
**Overall:** {review.get('overall_recommendation', '')}"""

        # ── Projects HTML ─────────────────────────────────────────────────────
        projects_html = format_projects_html(results.get("suggested_projects", []))

        # ── PDFs ─────────────────────────────────────────────────────────────
        resume_pdf_path = generate_resume_pdf(results.get("tailored_resume", ""))
        cl_pdf_path     = generate_cover_letter_pdf(results.get("cover_letter", ""))

        progress(1.0, desc="✅ Done!")

        cl_word_count = len(results.get("cover_letter", "").split())
        status = (
            f"✅ Complete!  Resume: **{rs}/100** · Cover Letter: **{cs}/100** · "
            f"Cover letter: ~{cl_word_count} words · PDFs ready ⬇️"
        )

        return (
            status,
            jd_summary,
            results.get("tailored_resume", ""),
            results.get("cover_letter", ""),
            review_md,
            projects_html,
            resume_pdf_path,
            cl_pdf_path,
        )

    except Exception as e:
        msg = str(e)
        if "401" in msg or "Unauthorized" in msg:
            msg = "❌ Invalid HuggingFace token."
        elif "rate" in msg.lower():
            msg = "❌ Rate limit hit — wait a moment and retry."
        else:
            msg = f"❌ Error: {msg}"
        return msg, "", "", "", "", "<p>Error occurred.</p>", None, None


# ─── UI ───────────────────────────────────────────────────────────────────────

with gr.Blocks(css=custom_css) as demo:

    gr.HTML("""
    <div id="app-header">
        <div id="header-badge">⚡</div>
        <div id="header-text">
            <h1>Resume Tailor Agent</h1>
            <p>AI-powered resume tailoring · Custom cover letter length · Portfolio project suggestions · PDF export</p>
        </div>
    </div>

    <div id="pipeline-bar">
        <div class="pipeline-step"><span class="num">1</span> JD Analysis</div>
        <span class="pipeline-arrow">→</span>
        <div class="pipeline-step"><span class="num">2</span> Gap Analysis</div>
        <span class="pipeline-arrow">→</span>
        <div class="pipeline-step"><span class="num">3</span> Project Ideas</div>
        <span class="pipeline-arrow">→</span>
        <div class="pipeline-step"><span class="num">4</span> Tailor Resume</div>
        <span class="pipeline-arrow">→</span>
        <div class="pipeline-step"><span class="num">5</span> Cover Letter</div>
        <span class="pipeline-arrow">→</span>
        <div class="pipeline-step"><span class="num">6</span> Review</div>
    </div>
    """)

    with gr.Row(equal_height=False):

        # ── LEFT: inputs ──────────────────────────────────────────────────────
        with gr.Column(scale=5):

            with gr.Group():
                gr.Markdown("#### 📄 Resume")
                pdf_upload = gr.File(label="Upload PDF (optional)", file_types=[".pdf"], type="filepath")
                pdf_status = gr.Markdown("_Upload a PDF to auto-fill, or paste directly._")
                resume_input = gr.Textbox(
                    label="Resume Text",
                    lines=14,
                    placeholder="Paste your full resume here...",
                    value=SAMPLE_RESUME,
                    show_label=False
                )
                pdf_upload.change(fn=handle_pdf_upload, inputs=[pdf_upload], outputs=[resume_input, pdf_status])

            with gr.Group():
                gr.Markdown("#### 💼 Job Description")
                jd_input = gr.Textbox(
                    label="Job Description",
                    lines=10,
                    placeholder="Paste the full job posting...",
                    value=SAMPLE_JD,
                    show_label=False
                )

            with gr.Group():
                gr.Markdown("#### ✍️ Cover Letter Length")
                cover_letter_words = gr.Slider(
                    minimum=150,
                    maximum=600,
                    value=300,
                    step=50,
                    label="Target word count",
                    info="150 = concise · 300 = standard · 500+ = detailed"
                )

            run_btn = gr.Button("🚀 Run 6-Step Agent", variant="primary", size="lg")
            status_output = gr.Markdown(elem_id="status-bar")

        # ── RIGHT: results ────────────────────────────────────────────────────
        with gr.Column(scale=7):

            with gr.Tabs():

                with gr.Tab("🔍 Analysis & Gaps"):
                    analysis_output = gr.Markdown(value="_Results will appear here after running the agent._")

                with gr.Tab("💡 Project Suggestions"):
                    gr.Markdown(
                        "**Suggested portfolio projects** to fill skill gaps and make your application stand out. "
                        "Build 1-2 of these before applying!"
                    )
                    projects_output = gr.HTML(
                        value="<p style='color:#94a3b8;font-style:italic;padding:16px 0;'>Run the agent to get personalized project suggestions.</p>"
                    )

                with gr.Tab("📝 Tailored Resume"):
                    resume_output = gr.Textbox(
                        label="Tailored Resume (copy or download PDF below)",
                        lines=24,
                        show_label=True
                    )

                with gr.Tab("💌 Cover Letter"):
                    cover_output = gr.Textbox(
                        label="Cover Letter",
                        lines=18,
                        show_label=True
                    )

                with gr.Tab("⭐ Quality Review"):
                    review_output = gr.Markdown()

            gr.Markdown("#### ⬇️ Download PDFs")
            with gr.Row():
                resume_pdf_out = gr.File(label="📄 Resume PDF", interactive=False)
                cl_pdf_out     = gr.File(label="💌 Cover Letter PDF", interactive=False)

    gr.HTML("""
    <div id="app-footer">
        Model: Qwen/Qwen2.5-72B-Instruct via HuggingFace · PDF export via ReportLab · 6-step agentic pipeline
    </div>
    """)

    run_btn.click(
        fn=process,
        inputs=[resume_input, jd_input, cover_letter_words],
        outputs=[
            status_output,
            analysis_output,
            resume_output,
            cover_output,
            review_output,
            projects_output,
            resume_pdf_out,
            cl_pdf_out,
        ]
    )


if __name__ == "__main__":
    theme = gr.themes.Base(
        primary_hue="blue",
        secondary_hue="violet",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("DM Sans"), "sans-serif"]
    )
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=theme,
        css=custom_css
    )