# ⚡ Resume Tailor Agent

> AI-powered resume tailoring, cover letter generation, and portfolio project suggestions — powered by **Qwen-72B** on HuggingFace.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)
![Gradio](https://img.shields.io/badge/Gradio-UI-orange?style=flat-square&logo=gradio)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Qwen--72B-yellow?style=flat-square&logo=huggingface)
![ReportLab](https://img.shields.io/badge/PDF-ReportLab-red?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📸 Preview

| Input Panel | Results & Project Suggestions |
|---|---|
| Paste resume + job description, set cover letter length | Get tailored resume, cover letter, and portfolio ideas |

---

## 🚀 Features

- **6-step agentic pipeline** — each step builds on the last for coherent, high-quality output
- **Resume tailoring** — rewrites your resume with the right keywords and emphasis for the target role
- **Cover letter generation** — personalized, non-generic letters at your chosen word count (150–600 words)
- **Gap analysis** — identifies matching skills, missing skills, and what to emphasize
- **Portfolio project suggestions** — if your resume lacks relevant experience, the agent suggests 3 buildable projects with tech stack, time estimate, and why they impress hiring managers
- **Quality review** — self-critiques both documents and scores them out of 100
- **PDF export** — cleanly formatted, download-ready PDFs for both resume and cover letter
- **PDF upload** — upload your existing resume as a PDF to auto-extract text

---

## 🧠 Pipeline

```
JD Analysis → Gap Analysis → Project Suggestions → Tailor Resume → Cover Letter → Quality Review
    (1)             (2)               (3)                (4)              (5)             (6)
```

| Step | What it does |
|------|-------------|
| 1. JD Analysis | Extracts job title, company, required/preferred skills, keywords, tone |
| 2. Gap Analysis | Compares your resume against requirements; finds matches and gaps |
| 3. Project Suggestions | Suggests 3 portfolio projects to fill skill/keyword gaps |
| 4. Resume Tailoring | Rewrites resume with relevant keywords, reordered bullets, quantified impact |
| 5. Cover Letter | Writes a personalized cover letter at your target word count |
| 6. Quality Review | Scores both documents (0–100) and gives ATS keyword coverage rating |

---

## 🗂 Project Structure

```
resume-tailor-agent/
├── app.py          # Gradio web UI
├── agent.py        # 6-step agentic pipeline (LLM calls)
├── pdf_export.py   # ReportLab PDF generation
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/resume-tailor-agent.git
cd resume-tailor-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your HuggingFace token

Open `agent.py` and `app.py` and update the token constant at the top of each file:

```python
HF_TOKEN = "hf_your_token_here"
```

> Get a free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).  
> The model used is `Qwen/Qwen2.5-72B-Instruct` — make sure your token has Inference API access.

### 4. Run

```bash
python app.py
```

Then open [http://localhost:7860](http://localhost:7860) in your browser.

---

## 📦 Requirements

```
gradio
huggingface_hub
reportlab
pymupdf        # for PDF resume upload/extraction
```

Or install all at once:

```bash
pip install gradio huggingface_hub reportlab pymupdf
```

---

## 🖥 Usage

1. **Paste your resume** in the text box, or upload a PDF to auto-extract it
2. **Paste the job description** you're applying to
3. **Set cover letter length** using the slider (150 = concise, 300 = standard, 500+ = detailed)
4. Click **🚀 Run 6-Step Agent**
5. Review results across five tabs:
   - 🔍 Analysis & Gaps
   - 💡 Project Suggestions
   - 📝 Tailored Resume
   - 💌 Cover Letter
   - ⭐ Quality Review
6. Download your **Resume PDF** and **Cover Letter PDF**

---

## 💡 Project Suggestions Feature

If your resume is missing key skills or keywords required by the job, the agent automatically suggests **3 portfolio projects** you can build to strengthen your application. Each suggestion includes:

- Project title and description
- Recommended tech stack (as badges)
- Skills demonstrated
- Estimated build time (e.g. "1–2 weekends")
- Why it impresses hiring managers for that specific role
- GitHub structure tips

---

## 🔧 Configuration

| Setting | Location | Default |
|---------|----------|---------|
| HuggingFace token | `agent.py` / `app.py` — `HF_TOKEN` | — |
| Model | `agent.py` — `MODEL_ID` | `Qwen/Qwen2.5-72B-Instruct` |
| Server port | `app.py` — `demo.launch()` | `7860` |
| Cover letter length | UI slider | `300` words |

To swap to a different HuggingFace model, change `MODEL_ID` in `agent.py`:

```python
MODEL_ID = "mistralai/Mixtral-8x7B-Instruct-v0.1"
```

---

## 📄 License

MIT — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [Qwen2.5-72B-Instruct](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct) by Alibaba Cloud
- [Gradio](https://gradio.app/) for the web UI
- [ReportLab](https://www.reportlab.com/) for PDF generation
- [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF text extraction
