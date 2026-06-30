#!/usr/bin/env python3
"""
Resume Tailor - ATS keyword-based
Picks top 5 ATS-scored jobs and tailors resume + cold email for each.
"""

import json, os, re
from datetime import datetime

JOBS_FILE   = "jobs_found.json"
RESUME_FILE = "resume/base_resume.json"
OUTPUT_FILE = "tailored_resumes.json"

# Core resume data - reads from environment variables or uses defaults
# Set these in GitHub Secrets to customize: CANDIDATE_NAME, CANDIDATE_PHONE,
# CANDIDATE_LINKEDIN, CANDIDATE_GITHUB, CANDIDATE_YOE, CANDIDATE_EDUCATION
_email = os.environ.get("GMAIL_SENDER", "your-email@gmail.com")

CANDIDATE = {
    "name":     os.environ.get("CANDIDATE_NAME", "Your Name"),
    "title":    "Java Full Stack Developer",
    "email":    _email,
    "phone":    os.environ.get("CANDIDATE_PHONE", "+91 your-phone"),
    "linkedin": os.environ.get("CANDIDATE_LINKEDIN", "linkedin.com/in/your-profile"),
    "github":   os.environ.get("CANDIDATE_GITHUB", "github.com/your-username"),
    "location": "Bengaluru, India",
    "yoe":      os.environ.get("CANDIDATE_YOE", "1 year"),
    "summary":  (
        "Java Full Stack Developer with experience building "
        "enterprise-grade Spring Boot microservices and Angular frontends. "
        "Proficient in REST APIs, JWT security, Docker, and Angular."
    ),
    "skills": {
        "backend":  ["Java", "Spring Boot", "Spring Security", "REST APIs", "Microservices", "JPA/Hibernate", "JWT"],
        "frontend": ["Angular", "TypeScript", "RxJS", "HTML5", "CSS3"],
        "data":     ["PostgreSQL", "MySQL", "Redis", "MongoDB"],
        "devops":   ["Docker", "Jenkins", "GitHub Actions", "CI/CD", "Git"],
        "testing":  ["JUnit", "Mockito", "Swagger", "Postman"],
    },
    "experience": [
        {
            "company":  os.environ.get("CANDIDATE_EXP_COMPANY", "Your Company"),
            "role":     os.environ.get("CANDIDATE_EXP_ROLE", "Software Engineer"),
            "period":   os.environ.get("CANDIDATE_EXP_PERIOD", "Start - End"),
            "bullets": [
                "Developed scalable Java Spring Boot applications",
                "Built RESTful APIs and microservices architecture",
                "Implemented CI/CD pipelines using Docker and Jenkins",
            ]
        }
    ],
    "projects": [
        {
            "name": "Your Project 1",
            "tech": "Java, Spring Boot, Angular",
            "desc": "Description of your project",
        },
        {
            "name": "Your Project 2",
            "tech": "Java, Spring Boot, React",
            "desc": "Description of your project",
        },
    ],
    "education": os.environ.get("CANDIDATE_EDUCATION", "B.E. CSE - Your College (Year) - CGPA: X.XX/10"),
    "certs": [
        "Your Certification 1",
        "Your Certification 2",
    ],
}

# Skill keyword -> resume section mapping
SKILL_MAP = {
    "java":            CANDIDATE["skills"]["backend"],
    "spring":          CANDIDATE["skills"]["backend"],
    "spring boot":     CANDIDATE["skills"]["backend"],
    "spring security": CANDIDATE["skills"]["backend"],
    "spring cloud":    CANDIDATE["skills"]["backend"],
    "microservices":   CANDIDATE["skills"]["backend"],
    "rest api":        CANDIDATE["skills"]["backend"],
    "restful":         CANDIDATE["skills"]["backend"],
    "jpa":             CANDIDATE["skills"]["backend"],
    "hibernate":       CANDIDATE["skills"]["backend"],
    "angular":         CANDIDATE["skills"]["frontend"],
    "typescript":      CANDIDATE["skills"]["frontend"],
    "rxjs":            CANDIDATE["skills"]["frontend"],
    "html":            CANDIDATE["skills"]["frontend"],
    "css":             CANDIDATE["skills"]["frontend"],
    "websocket":       CANDIDATE["skills"]["frontend"],
    "kafka":           CANDIDATE["skills"]["data"],
    "redis":           CANDIDATE["skills"]["data"],
    "postgresql":      CANDIDATE["skills"]["data"],
    "sql":             CANDIDATE["skills"]["data"],
    "docker":          CANDIDATE["skills"]["devops"],
    "jenkins":         CANDIDATE["skills"]["devops"],
    "ci/cd":           CANDIDATE["skills"]["devops"],
    "git":             CANDIDATE["skills"]["devops"],
    "github actions":  CANDIDATE["skills"]["devops"],
    "junit":           CANDIDATE["skills"]["testing"],
    "mockito":         CANDIDATE["skills"]["testing"],
    "swagger":         CANDIDATE["skills"]["testing"],
    "postman":         CANDIDATE["skills"]["testing"],
    "jwt":             CANDIDATE["skills"]["backend"],
    "agile":           ["Agile (JIRA, Scrum, Sprint planning)"],
    "jira":            ["JIRA", "Agile", "Sprint planning"],
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
    if not company or company.lower() in ("n/a","na","confidential company",""):
        company = "your company"
    title   = job.get("title", "Software Developer")
    skills_line = ", ".join(matched_skills[:5]) if matched_skills else "Java, Spring Boot, Angular"
    return {
        "email_subject": f"Application: {title} | {CANDIDATE['name']} | Java Full Stack | {CANDIDATE['yoe']} | Bengaluru",
        "email_body": (
            f"Hi Hiring Team,\n\n"
            f"I am excited to apply for the {title} role at {company}.\n\n"
            f"I am a Java Full Stack Developer with {CANDIDATE['yoe']} of experience, "
            f"skilled in building Spring Boot microservices and Angular applications.\n\n"
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
    if company.lower() in ("n/a","na","confidential company",""):
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
      {CANDIDATE['title']} - {CANDIDATE['yoe']} Experience - {CANDIDATE['location']}
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
              f"{job.get('company','Confidential')[:25]} - ATS: {score}% - "
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
