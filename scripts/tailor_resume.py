#!/usr/bin/env python3
"""
Resume Tailor - ATS keyword-based (Multi-Profile Edition)
Picks top 5 ATS-scored jobs and tailors resume + cold email for each.
Profiles: Python Developer | Data Analyst | Tech Support | Cloud Computing
"""

import json, os, re
from datetime import datetime

JOBS_FILE   = "jobs_found.json"
RESUME_FILE = "resume/base_resume.json"
OUTPUT_FILE = "tailored_resumes.json"

# Core resume data - reads from environment variables or uses defaults
_email = os.environ.get("GMAIL_SENDER", "your-email@gmail.com")

CANDIDATE = {
    "name":     os.environ.get("CANDIDATE_NAME", "Your Name"),
    "title":    "Python Developer | Data Analyst | Tech Support | Cloud Computing",
    "email":    _email,
    "phone":    os.environ.get("CANDIDATE_PHONE", "+91 your-phone"),
    "linkedin": os.environ.get("CANDIDATE_LINKEDIN", "linkedin.com/in/your-profile"),
    "github":   os.environ.get("CANDIDATE_GITHUB", "github.com/your-username"),
    "location": "Bengaluru, India",
    "yoe":      os.environ.get("CANDIDATE_YOE", "Fresher / 0-1 year"),
    "summary":  (
        "Versatile IT fresher skilled in Python development, data analysis, "
        "technical support, and cloud computing. Proficient in Python, SQL, AWS, "
        "Power BI, and Linux. Strong problem-solving abilities with hands-on "
        "experience in real-world projects. Seeking fresher opportunities in "
        "Bengaluru."
    ),
    "skills": {
        "python":     ["Python", "Django", "Flask", "FastAPI", "Pandas", "NumPy", "REST APIs"],
        "data":       ["SQL", "MySQL", "PostgreSQL", "Power BI", "Tableau", "Excel", "Data Analysis"],
        "cloud":      ["AWS", "Azure", "Docker", "Linux", "Git", "CI/CD"],
        "support":    ["Technical Support", "IT Support", "Helpdesk", "Troubleshooting", "Networking"],
        "frontend":   ["HTML", "CSS", "JavaScript", "React"],
        "tools":      ["Git", "GitHub", "Jira", "VS Code", "Jupyter"],
    },
    "experience": [
        {
            "company":  os.environ.get("CANDIDATE_EXP_COMPANY", "Project / Training Experience"),
            "role":     os.environ.get("CANDIDATE_EXP_ROLE", "Python & Data Analysis Intern"),
            "period":   os.environ.get("CANDIDATE_EXP_PERIOD", "Recent"),
            "bullets": [
                "Built Python applications using Django/Flask frameworks",
                "Analyzed datasets using Pandas, SQL, and created Power BI dashboards",
                "Deployed applications on AWS cloud with Docker containers",
            ]
        }
    ],
    "projects": [
        {
            "name": "Python Web Application",
            "tech": "Python, Django, PostgreSQL",
            "desc": "Built a full-stack web application with user authentication and CRUD operations",
        },
        {
            "name": "Data Analysis Dashboard",
            "tech": "Python, Pandas, Power BI, SQL",
            "desc": "Analyzed sales data and created interactive dashboards for business insights",
        },
        {
            "name": "Cloud Deployment Project",
            "tech": "AWS, Docker, Linux, GitHub Actions",
            "desc": "Deployed containerized applications on AWS EC2 with CI/CD pipeline",
        },
    ],
    "education": os.environ.get("CANDIDATE_EDUCATION", "B.E./B.Tech - Your College (Year) - CGPA: X.XX/10"),
    "certs": [
        "AWS Cloud Practitioner (or equivalent)",
        "Python/Data Science Certification",
    ],
}

# Skill keyword -> resume section mapping (Multi-Profile)
SKILL_MAP = {
    # Python Developer
    "python":          CANDIDATE["skills"]["python"],
    "django":          CANDIDATE["skills"]["python"],
    "flask":           CANDIDATE["skills"]["python"],
    "fastapi":         CANDIDATE["skills"]["python"],
    # Data Analyst
    "data analyst":    CANDIDATE["skills"]["data"],
    "data analysis":   CANDIDATE["skills"]["data"],
    "data analytics":  CANDIDATE["skills"]["data"],
    "business analyst":CANDIDATE["skills"]["data"],
    "power bi":        CANDIDATE["skills"]["data"],
    "tableau":         CANDIDATE["skills"]["data"],
    "sql":             CANDIDATE["skills"]["data"],
    "mysql":           CANDIDATE["skills"]["data"],
    "postgresql":      CANDIDATE["skills"]["data"],
    "pandas":          CANDIDATE["skills"]["python"],
    "excel":           CANDIDATE["skills"]["data"],
    # Cloud Computing
    "aws":             CANDIDATE["skills"]["cloud"],
    "azure":           CANDIDATE["skills"]["cloud"],
    "cloud":           CANDIDATE["skills"]["cloud"],
    "devops":          CANDIDATE["skills"]["cloud"],
    "docker":          CANDIDATE["skills"]["cloud"],
    "kubernetes":      CANDIDATE["skills"]["cloud"],
    "linux":           CANDIDATE["skills"]["cloud"],
    "terraform":       CANDIDATE["skills"]["cloud"],
    # Tech Support
    "technical support": CANDIDATE["skills"]["support"],
    "tech support":    CANDIDATE["skills"]["support"],
    "it support":      CANDIDATE["skills"]["support"],
    "helpdesk":        CANDIDATE["skills"]["support"],
    "troubleshooting": CANDIDATE["skills"]["support"],
    "networking":      CANDIDATE["skills"]["support"],
    # Common
    "git":             CANDIDATE["skills"]["tools"],
    "github":          CANDIDATE["skills"]["tools"],
    "api":             CANDIDATE["skills"]["python"],
    "rest api":        CANDIDATE["skills"]["python"],
    "agile":           ["Agile", "JIRA", "Scrum"],
    "jira":            ["JIRA", "Agile", "Scrum"],
    "html":            CANDIDATE["skills"]["frontend"],
    "css":             CANDIDATE["skills"]["frontend"],
    "javascript":      CANDIDATE["skills"]["frontend"],
}


def extract_jd_skills(job):
    """Extract skills from job title + skills field."""
    combined = f"{job.get('title','')} {job.get('skills','')}".lower()
    matched = []
    for kw, skills in SKILL_MAP.items():
        if kw in combined:
            matched.extend(skills)
    return list(dict.fromkeys(matched))[:10]


def cold_email(job, matched_skills):
    company = (job.get("company","") or "").strip()
    if not company or company.lower() in ("n/a","na","company not disclosed","confidential company",""):
        company = "your company"
    title   = job.get("title", "Software Developer")
    skills_line = ", ".join(matched_skills[:5]) if matched_skills else "Python, SQL, AWS, Data Analysis"
    return {
        "email_subject": f"Application: {title} | {CANDIDATE['name']} | Fresher | Bengaluru",
        "email_body": (
            f"Hi Hiring Team,\n\n"
            f"I am excited to apply for the {title} role at {company}.\n\n"
            f"I am a motivated IT fresher with skills in Python development, data analysis, "
            f"technical support, and cloud computing.\n\n"
            f"Key skills matching your requirement: {skills_line}.\n\n"
            f"I would love to discuss how I can contribute to {company}. "
            f"My resume is attached below.\n\n"
            f"Best regards,\n"
            f"{CANDIDATE['name']}\n"
            f"{CANDIDATE['email']} | {CANDIDATE['phone']}\n"
            f"{CANDIDATE['linkedin']} | {CANDIDATE['github']}"
        ),
    }


def build_resume_html(job, matched_skills):
    """Generate a clean HTML resume tailored for this job."""
    company = (job.get("company","") or "Hiring Company").strip()
    if company.lower() in ("n/a","na","company not disclosed","confidential company",""):
        company = "Hiring Company"
    title = job.get("title","Software Developer")

    # Highlight matched skills at top
    skill_pills = "".join(
        f'<span style="background:#e8f0fe;color:#1565c0;padding:4px 12px;border-radius:20px;'
        f'font-size:12px;font-weight:700;margin:3px;display:inline-block">{s}</span>'
        for s in matched_skills[:8]
    )

    exp_bullets = "".join(
        f"<li style='margin-bottom:6px;font-size:13px'>{b}</li>"
        for b in CANDIDATE["experience"][0]["bullets"]
    )

    projects_html = ""
    for p in CANDIDATE["projects"][:3]:
        projects_html += f"""
<div style="margin-bottom:12px">
  <div style="font-weight:700;color:#1a237e;font-size:13px">{p["name"]}</div>
  <div style="font-size:11px;color:#546e7a;margin:2px 0">{p["tech"]}</div>
  <div style="font-size:12px;color:#37474f">{p["desc"]}</div>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>{CANDIDATE['name']} - Resume for {company}</title></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;max-width:800px;margin:0 auto;
             padding:30px;color:#222;background:#fff">
  <div style="border-bottom:3px solid #1565c0;padding-bottom:16px;margin-bottom:20px">
    <h1 style="margin:0;color:#1565c0;font-size:26px">{CANDIDATE['name'].upper()}</h1>
    <div style="color:#546e7a;font-size:14px;margin-top:4px">
      {CANDIDATE['title']} - {CANDIDATE['yoe']} - {CANDIDATE['location']}
    </div>
    <div style="font-size:12px;margin-top:6px;color:#37474f">
      {CANDIDATE['email']} | {CANDIDATE['phone']} |
      {CANDIDATE['linkedin']} | {CANDIDATE['github']}
    </div>
  </div>

  <div style="background:#e8f0fe;border-radius:10px;padding:12px 16px;margin-bottom:18px">
    <div style="font-size:11px;color:#1565c0;font-weight:800;margin-bottom:6px">
      SKILLS MATCHING: {title} @ {company}
    </div>
    <div>{skill_pills}</div>
  </div>

  <h2 style="color:#1565c0;font-size:15px;border-bottom:1px solid #e0e0e0;
             padding-bottom:4px">PROFESSIONAL SUMMARY</h2>
  <p style="font-size:13px;line-height:1.6;margin-top:8px">{CANDIDATE['summary']}</p>

  <h2 style="color:#1565c0;font-size:15px;border-bottom:1px solid #e0e0e0;
             padding-bottom:4px">EXPERIENCE</h2>
  <div style="margin-top:8px">
    <div style="display:flex;justify-content:space-between">
      <strong style="font-size:14px">{CANDIDATE['experience'][0]['company']}</strong>
      <span style="font-size:12px;color:#546e7a">{CANDIDATE['experience'][0]['period']}</span>
    </div>
    <div style="color:#546e7a;font-size:13px;margin:3px 0">{CANDIDATE['experience'][0]['role']}</div>
    <ul style="margin:8px 0;padding-left:20px">{exp_bullets}</ul>
  </div>

  <h2 style="color:#1565c0;font-size:15px;border-bottom:1px solid #e0e0e0;
             padding-bottom:4px">PROJECTS</h2>
  <div style="margin-top:8px">{projects_html}</div>

  <h2 style="color:#1565c0;font-size:15px;border-bottom:1px solid #e0e0e0;
             padding-bottom:4px">EDUCATION</h2>
  <p style="font-size:13px;margin-top:8px">{CANDIDATE['education']}</p>

  <h2 style="color:#1565c0;font-size:15px;border-bottom:1px solid #e0e0e0;
             padding-bottom:4px">CERTIFICATIONS</h2>
  <ul style="margin-top:8px;padding-left:20px">
    {"".join(f"<li style='font-size:13px;margin-bottom:4px'>{c}</li>" for c in CANDIDATE['certs'])}
  </ul>
</body></html>"""


def tailor_all():
    print(f"\n{'='*55}")
    print(f"  RESUME TAILOR - {datetime.now().strftime('%d %b %Y %I:%M %p')}")
    print(f"  Multi-Profile: Python | Data Analyst | Tech Support | Cloud")
    print(f"{'='*55}\n")

    if not os.path.exists(JOBS_FILE):
        print("  No jobs_found.json found")
        return []

    with open(JOBS_FILE) as f:
        jobs_data = json.load(f)

    all_jobs = jobs_data.get("all_jobs", [])

    # Pick top 5 by ATS score (already sorted)
    top_jobs = all_jobs[:5]
    print(f"  Tailoring for top {len(top_jobs)} ATS-matched jobs...")

    results = []
    for i, job in enumerate(top_jobs):
        matched = extract_jd_skills(job)
        email   = cold_email(job, matched)
        rhtml   = build_resume_html(job, matched)
        score   = job.get("ats_score", 0)
        print(f"  [{i+1}] {job.get('title','')} @ "
              f"{job.get('company','Company Not Disclosed')[:25]} - ATS: {score}% - "
              f"{len(matched)} skills matched")
        results.append({
            "job":         job,
            "tailored": {
                "top_skills":    matched,
                "email_subject": email["email_subject"],
                "email_body":    email["email_body"],
            },
            "resume_html": rhtml,
        })

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n  {len(results)} tailored resumes saved to {OUTPUT_FILE}")
    return results

if __name__ == "__main__":
    tailor_all()
