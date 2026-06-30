# Daily Job Bot v7.0

**Automated Daily Job Digest for Fresher IT Roles in Bengaluru**

**Profiles:** Python Developer | Data Analyst | Technical Support | Cloud Computing
**Target Companies:** Startups & Mid-range Companies (MNCs also included)

- Scrapes **9 job platforms** daily at **8:00 AM IST**
- Filters for **0-2 YOE**, **Bengaluru only**, **IT roles only**
- **ATS scoring** - ranks jobs by keyword match
- **Auto-tailored resumes + cold emails** for top 5 jobs
- **Duplicate filtering** - same job won't be sent twice in 7 days
- **Fixed company name extraction** - now shows actual company names properly
- **100% FREE** - no paid APIs needed

---

## Platforms Covered (v7.0)

| # | Platform | Status |
|---|----------|--------|
| 1 | **LinkedIn** | Active |
| 2 | **Naukri.com** | Active |
| 3 | **Indeed** | **NEW - Added in v7.0** |
| 4 | **Internshala** | Active |
| 5 | **Wellfound** (formerly AngelList) | Active |
| 6 | **Cutshort** | Active |
| 7 | **Foundit** (formerly Monster India) | Active |
| 8 | **WorkIndia** | Active |
| 9 | **Freshersworld** | **NEW - Added in v7.0** |

---

## What Runs Every Morning

| Step | Action |
|------|--------|
| 1 | Scrape 9 platforms: LinkedIn, Naukri, Indeed, Internshala, Wellfound, Cutshort, Foundit, WorkIndia, Freshersworld |
| 2 | Extract company names (fixed in v7.0 with robust multi-strategy extraction) |
| 3 | Remove duplicates (remembered for 7 days via GitHub Gist) |
| 4 | Check job links are still active |
| 5 | Generate tailored resumes + cold emails for top 5 ATS matches |
| 6 | Send beautiful HTML email with all jobs + attachments |

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
GitHub Repo > Actions > Daily Job Bot v7.0 > Run workflow > Run workflow
```

### 2. Automatic (Daily at 8 AM IST)
Already configured! Runs every day at 8:00 AM IST (2:30 AM UTC).

Cron: `30 2 * * *` (2:30 AM UTC = 8:00 AM IST)

> **Note:** GitHub Actions disables scheduled workflows after **60 days of repository inactivity**. If the bot stops running, go to `Actions` tab and re-enable workflows, or push any commit to reactivate.

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

## Company Name Extraction (Fixed in v7.0)

The bot now uses a **5-strategy approach** to extract company names:

1. **JSON-LD Schema** (`hiringOrganization.name`)
2. **Data attributes** (`data-company`, `data-employer`, `data-organization`)
3. **CSS selectors** (20+ company-specific class patterns)
4. **ARIA labels** (`aria-label` with "at CompanyName")
5. **Text pattern matching** ("at CompanyName Pvt Ltd" patterns)

If no company is found, it shows "Company Not Disclosed" instead of blank.

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
| **Workflow not running at 8AM** | GitHub disables schedules after 60 days inactivity. Go to Actions tab > re-enable workflows, or push any commit |
| Wrong candidate info | Set `CANDIDATE_*` secrets (see Step 1 table) |
| Company name shows "Not Disclosed" | Some sites hide company names until login - this is expected behavior |

---

## Project Structure

```
.
|-- .github/workflows/daily_jobs.yml    # CI/CD workflow (8AM IST trigger)
|-- scripts/
|   |-- run_all.py                       # Main orchestrator
|   |-- scrape_jobs.py                   # 9-platform scraper (multi-profile)
|   |-- job_tracker.py                   # Deduplication + active check
|   |-- tailor_resume.py                 # Resume + cold email generator
|   |-- send_email.py                    # HTML email sender
|-- requirements.txt                     # Python dependencies
|-- README.md                            # This file
```

---

## Changelog

### v7.0 (Current)
- **Fixed company name extraction** - Rewrote with 5-strategy robust extraction
- **Added Indeed scraper** - Now covers in.indeed.com
- **Added Freshersworld scraper** - Now covers freshersworld.com
- **Removed outdated platforms** - Instahire, Hirist, Naukricity/iimjobs, Apna.co (unreliable)
- **Updated to 9 platforms** matching user's requested list
- **Improved workflow reliability** - Added additional artifact uploads

### v6.0
- Initial multi-profile edition
