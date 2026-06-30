# Daily Job Bot

**Automated Daily Job Digest for Fresher IT Roles in Bengaluru**

**Profiles:** Python Developer | Data Analyst | Technical Support | Cloud Computing

- Scrapes **11 job platforms** daily at **8:00 AM IST**
- Filters for **0-2 YOE**, **Bengaluru only**, **IT roles only**
- **ATS scoring** - ranks jobs by keyword match
- **Auto-tailored resumes + cold emails** for top 5 jobs
- **Duplicate filtering** - same job won't be sent twice in 7 days
- **100% FREE** - no paid APIs needed

---

## What Runs Every Morning

| Step | Action |
|------|--------|
| 1 | Scrape LinkedIn, Naukri, Wellfound, Internshala, Hirist, Cutshort, Foundit, Apna.co, WorkIndia, Naukricity, iimjobs |
| 2 | Remove duplicates (remembered for 7 days via GitHub Gist) |
| 3 | Check job links are still active |
| 4 | Generate tailored resumes + cold emails for top 5 ATS matches |
| 5 | Send beautiful HTML email with all jobs + attachments |

---

## Setup (One-Time)

### Step 1: Set GitHub Secrets

Go to: `Settings > Secrets and variables > Actions > New repository secret`

| Secret Name | Required | Description |
|-------------|----------|-------------|
| `GMAIL_SENDER` | **YES** | Your Gmail address (e.g., `yourname@gmail.com`) |
| `GMAIL_APP_PASSWORD` | **YES** | 16-char Gmail App Password (see below) |
| `CANDIDATE_NAME` | No | Your full name (default: "Your Name") |
| `CANDIDATE_PHONE` | No | Your phone number (default: "+91 your-phone") |
| `CANDIDATE_LINKEDIN` | No | LinkedIn profile URL |
| `CANDIDATE_GITHUB` | No | GitHub profile URL |
| `CANDIDATE_YOE` | No | Years of experience (default: "Fresher / 0-1 year") |
| `CANDIDATE_EDUCATION` | No | Education details |
| `GITHUB_TOKEN` | No | Auto-provided by GitHub Actions for job tracking |

### Step 2: Get Gmail App Password

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (required!)
3. Search "**App passwords**" -> Select app "Mail" -> Select device "Other"
4. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)
5. Add to GitHub Secret: `GMAIL_APP_PASSWORD`

---

## How to Trigger (3 Ways)

### 1. Manual Trigger (Test Now)
```
GitHub Repo > Actions > Daily Job Bot > Run workflow > Run workflow
```

### 2. Automatic (Daily at 8 AM IST)
Already configured! Runs every day at 8:00 AM IST (2:30 AM UTC).

Cron: `30 2 * * *` (2:30 AM UTC = 8:00 AM IST)

### 3. Via GitHub API
```bash
curl -X POST \
  -H "Authorization: token YOUR_PAT" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/sharanus890/daily-job-bot/actions/workflows/daily_jobs.yml/dispatches \
  -d '{"ref":"main"}'
```

---

## Email Preview

The workflow uploads `email_preview.html` as an artifact every run (check Actions > Artifacts).

---

## Job Profiles Covered

The bot searches for fresher (0-2 YOE) roles across these profiles:

| Profile | Keywords Searched |
|---------|-------------------|
| **Python Developer** | python, django, flask, fastapi, backend developer |
| **Data Analyst** | data analyst, data analysis, data analytics, business analyst, data science |
| **Technical Support** | tech support, technical support, it support, helpdesk, desktop support |
| **Cloud Computing** | cloud, aws, azure, devops, cloud engineer, site reliability |

---

## What's Free

| Feature | Cost |
|---------|------|
| GitHub Actions | **FREE** (2,000 min/month) |
| Gmail SMTP | **FREE** (with App Password) |
| Job scraping | **FREE** (direct HTTP requests) |
| Resume tailoring | **FREE** (keyword-based, no AI API) |
| Job tracking Gist | **FREE** (GitHub Gist storage) |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "AUTH FAILED" | Regenerate Gmail App Password, ensure 2FA is ON |
| "No jobs found" | Normal on some days; check artifact for debug info |
| Workflow not running | Check Actions tab > enable workflows if disabled |
| Wrong candidate info | Set `CANDIDATE_*` secrets (see Step 1 table) |
| Company name not showing | Fixed in v6.0 - uses improved extraction + "Company Not Disclosed" fallback |

---

## Project Structure

```
.
|-- .github/workflows/daily_jobs.yml    # CI/CD workflow (8AM IST trigger)
|-- scripts/
|   |-- run_all.py                       # Main orchestrator
|   |-- scrape_jobs.py                   # 11-platform scraper (multi-profile)
|   |-- job_tracker.py                   # Deduplication + active check
|   |-- tailor_resume.py                 # Resume + cold email generator
|   |-- send_email.py                    # HTML email sender
|-- requirements.txt                     # Python dependencies
|-- README.md                            # This file
```
