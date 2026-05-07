"""
Resume & Cover Letter Tailoring Agent
Uses Qwen (via HuggingFace Inference API) as the free LLM backbone.
Agentic loop: Analyze JD → Gap Analysis → Suggest Projects → Tailor Resume → Write Cover Letter → Review
"""

import os
import json
import re
from huggingface_hub import InferenceClient

# HF_TOKEN = ""
HF_TOKEN = os.environ.get("HF_TOKEN")


MODEL_ID = "Qwen/Qwen2.5-72B-Instruct"


def chat(client: InferenceClient, system: str, user: str, max_tokens: int = 1000, temperature: float = 0.3) -> str:
    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def analyze_job_description(client, jd):
    system = "You are a job analysis expert. Always respond with valid JSON only — no markdown, no extra text."
    user = f"""Analyze this job description and return ONLY a JSON object with this exact structure:
{{
  "job_title": "...",
  "company": "...",
  "required_skills": ["skill1", "skill2"],
  "preferred_skills": ["skill1", "skill2"],
  "key_responsibilities": ["resp1", "resp2"],
  "keywords": ["kw1", "kw2"],
  "tone": "formal/startup/technical/creative",
  "years_experience": "X years or entry-level"
}}

Job Description:
{jd}"""
    raw = chat(client, system, user, max_tokens=800, temperature=0.2)
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return {
        "job_title": "Position", "company": "Company",
        "required_skills": [], "preferred_skills": [],
        "key_responsibilities": [], "keywords": [],
        "tone": "formal", "years_experience": "Not specified"
    }


def gap_analysis(client, resume, jd_analysis):
    system = "You are a career coach. Always respond with valid JSON only — no markdown, no extra text."
    user = f"""Compare this resume against the job requirements and return ONLY a JSON object:
{{
  "matching_skills": ["skills found in both"],
  "missing_skills": ["required skills not in resume"],
  "missing_keywords": ["important JD keywords absent from resume"],
  "transferable_experiences": ["resume experiences that map to JD needs"],
  "strongest_selling_points": ["top 3 reasons this candidate fits"],
  "suggested_emphasis": ["what to highlight more strongly"],
  "needs_projects": true
}}

Set "needs_projects" to true if the resume lacks relevant projects that would strengthen the application.

RESUME:
{resume}

JOB REQUIREMENTS:
- Title: {jd_analysis.get('job_title')}
- Required Skills: {', '.join(jd_analysis.get('required_skills', []))}
- Preferred Skills: {', '.join(jd_analysis.get('preferred_skills', []))}
- Key Responsibilities: {', '.join(jd_analysis.get('key_responsibilities', []))}
- Keywords: {', '.join(jd_analysis.get('keywords', []))}"""

    raw = chat(client, system, user, max_tokens=900, temperature=0.3)
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return {
        "matching_skills": [], "missing_skills": [], "missing_keywords": [],
        "transferable_experiences": [], "strongest_selling_points": [],
        "suggested_emphasis": [], "needs_projects": True
    }


def suggest_projects(client, resume, jd_analysis, gap_data):
    """Suggest 3 portfolio projects tailored to fill skill/keyword gaps."""
    missing = gap_data.get("missing_skills", []) + gap_data.get("missing_keywords", [])
    system = "You are a senior software engineer and career mentor. Always respond with valid JSON only — no markdown, no extra text."
    user = f"""The candidate is applying for {jd_analysis.get('job_title')} at {jd_analysis.get('company')}.
Their resume is missing these key skills/keywords: {', '.join(missing[:10]) if missing else 'some domain-specific experience'}.

Based on their existing skills and the job requirements, suggest 3 portfolio projects they could build to strengthen their application.

Return ONLY a JSON array of exactly 3 project objects:
[
  {{
    "title": "Project Name",
    "description": "1-2 sentence description of what it does",
    "tech_stack": ["tech1", "tech2", "tech3"],
    "skills_demonstrated": ["skill1", "skill2"],
    "why_it_helps": "One sentence on why this impresses hiring managers for this role",
    "estimated_time": "e.g. 1-2 weekends",
    "github_structure": "Brief note on how to structure/present it"
  }}
]

Existing candidate skills: {resume[:500]}
Required skills for role: {', '.join(jd_analysis.get('required_skills', []))}"""

    raw = chat(client, system, user, max_tokens=1200, temperature=0.5)
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return []


def tailor_resume(client, resume, jd_analysis, gap_data):
    keywords_str  = ', '.join(jd_analysis.get('keywords', []))
    strengths_str = '\n'.join(f"- {s}" for s in gap_data.get('strongest_selling_points', []))
    emphasis_str  = '\n'.join(f"- {s}" for s in gap_data.get('suggested_emphasis', []))

    system = "You are an expert resume writer. Return only the tailored resume text — no commentary, no markdown code blocks."
    user = f"""Tailor this resume for the target job. Format it clearly with sections, clean bullet points, and consistent structure.

ORIGINAL RESUME:
{resume}

TARGET JOB: {jd_analysis.get('job_title')} at {jd_analysis.get('company')}
KEYWORDS TO INCLUDE: {keywords_str}
STRONGEST SELLING POINTS:
{strengths_str}
AREAS TO EMPHASIZE:
{emphasis_str}

Rules:
1. Keep ALL facts accurate — do not invent experience
2. Reorder bullets to put most relevant experience first  
3. Naturally weave in keywords from the JD
4. Quantify achievements where possible
5. Match tone: {jd_analysis.get('tone', 'professional')}
6. Use clear section headers: EXPERIENCE, EDUCATION, SKILLS, etc.
7. Use bullet points starting with "•" for experience items

Write the complete tailored resume:"""

    return chat(client, system, user, max_tokens=2000, temperature=0.4)


def write_cover_letter(client, resume, jd, jd_analysis, gap_data, word_count=300):
    selling_points = '\n'.join(f"- {s}" for s in gap_data.get('strongest_selling_points', []))

    system = "You are an expert cover letter writer. Return only the cover letter text — no commentary, no markdown."
    user = f"""Write a compelling, personalized cover letter of approximately {word_count} words.

CANDIDATE RESUME:
{resume}

JOB DESCRIPTION:
{jd}

KEY SELLING POINTS:
{selling_points}

Requirements:
- Address hiring team at {jd_analysis.get('company', 'the company')}
- Opening: hook with a specific reason you want THIS role (not generic)
- Middle: connect 2-3 real experiences to their exact needs
- Closing: confident call to action
- Tone: {jd_analysis.get('tone', 'professional')} but warm and human
- TARGET LENGTH: approximately {word_count} words — count carefully
- Do NOT open with "I am writing to express my interest"
- Do NOT use filler phrases like "I am passionate about" or "I am excited to"

Write the complete cover letter (aim for {word_count} words):"""

    return chat(client, system, user, max_tokens=max(800, word_count * 2), temperature=0.6)


def quality_review(client, tailored_resume, cover_letter, jd_analysis):
    system = "You are a senior hiring manager. Always respond with valid JSON only — no markdown, no extra text."
    user = f"""Review this tailored resume and cover letter for the role below and return ONLY a JSON object:
{{
  "resume_score": 85,
  "cover_letter_score": 88,
  "resume_strengths": ["strength1", "strength2"],
  "resume_improvements": ["improvement1"],
  "cover_letter_strengths": ["strength1"],
  "cover_letter_improvements": ["improvement1"],
  "ats_keyword_coverage": "high/medium/low",
  "overall_recommendation": "brief summary"
}}

TARGET ROLE: {jd_analysis.get('job_title')} at {jd_analysis.get('company')}
REQUIRED SKILLS: {', '.join(jd_analysis.get('required_skills', []))}

TAILORED RESUME (first 600 chars):
{tailored_resume[:600]}...

COVER LETTER (first 400 chars):
{cover_letter[:400]}..."""

    raw = chat(client, system, user, max_tokens=600, temperature=0.2)
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return {
        "resume_score": 75, "cover_letter_score": 75,
        "resume_strengths": ["Well-structured"],
        "resume_improvements": ["Add more keywords"],
        "cover_letter_strengths": ["Personalized"],
        "cover_letter_improvements": ["Stronger opening"],
        "ats_keyword_coverage": "medium",
        "overall_recommendation": "Good foundation, minor tweaks needed"
    }


def run_agent(resume: str, job_description: str, hf_token: str = HF_TOKEN, cover_letter_words: int = 300) -> dict:
    print("\n🤖 Resume Tailoring Agent Starting...\n" + "=" * 60)

    if not hf_token:
        raise ValueError("HuggingFace token required.")

    client = InferenceClient(token=hf_token.strip())

    results = {
        "steps": [], "jd_analysis": None, "gap_analysis": None,
        "suggested_projects": [], "tailored_resume": None,
        "cover_letter": None, "review": None
    }

    print("📋 Step 1/6: Analyzing Job Description...")
    jd_analysis = analyze_job_description(client, job_description)
    results["jd_analysis"] = jd_analysis
    results["steps"].append({"step": 1, "name": "JD Analysis", "status": "complete"})
    print(f"   ✅ Role: {jd_analysis.get('job_title')} at {jd_analysis.get('company')}")

    print("\n🔍 Step 2/6: Running Gap Analysis...")
    gaps = gap_analysis(client, resume, jd_analysis)
    results["gap_analysis"] = gaps
    results["steps"].append({"step": 2, "name": "Gap Analysis", "status": "complete"})
    print(f"   ✅ Matching: {len(gaps.get('matching_skills', []))} | Missing: {len(gaps.get('missing_skills', []))}")

    print("\n💡 Step 3/6: Suggesting Portfolio Projects...")
    projects = suggest_projects(client, resume, jd_analysis, gaps)
    results["suggested_projects"] = projects
    results["steps"].append({"step": 3, "name": "Project Suggestions", "status": "complete"})
    print(f"   ✅ {len(projects)} projects suggested")

    print("\n✍️  Step 4/6: Tailoring Resume...")
    tailored_resume = tailor_resume(client, resume, jd_analysis, gaps)
    results["tailored_resume"] = tailored_resume
    results["steps"].append({"step": 4, "name": "Resume Tailoring", "status": "complete"})
    print(f"   ✅ Resume tailored ({len(tailored_resume.split())} words)")

    print(f"\n💌 Step 5/6: Writing Cover Letter (~{cover_letter_words} words)...")
    cover_letter = write_cover_letter(client, resume, job_description, jd_analysis, gaps, cover_letter_words)
    results["cover_letter"] = cover_letter
    results["steps"].append({"step": 5, "name": "Cover Letter", "status": "complete"})
    print(f"   ✅ Cover letter written ({len(cover_letter.split())} words)")

    print("\n🎯 Step 6/6: Quality Review...")
    review = quality_review(client, tailored_resume, cover_letter, jd_analysis)
    results["review"] = review
    results["steps"].append({"step": 6, "name": "Quality Review", "status": "complete"})
    print(f"   ✅ Resume: {review.get('resume_score')}/100 | Cover Letter: {review.get('cover_letter_score')}/100")

    print("\n" + "=" * 60 + "\n🎉 Agent Complete!\n")
    return results