#!/usr/bin/env python3
"""
Daily Job Bot - Main Orchestrator
Runs the full pipeline: scrape -> filter duplicates -> send email
Profiles: Python Developer | Data Analyst | Tech Support | Cloud Computing
"""
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(__file__))

from scrape_jobs import scrape_all_jobs
from job_tracker import filter_new_and_active
from tailor_resume import tailor_all
from send_email import send_digest

if __name__ == "__main__":
    print("=" * 60)
    print("  DAILY JOB BOT v7.0 - FULL PIPELINE")
    print("  Python Dev | Data Analyst | Tech Support | Cloud Computing")
    print("  Bengaluru | Fresher (0-2 YOE) | Startup & Mid-range Companies")
    print("=" * 60)

    # Step 1: Scrape jobs from all 9 platforms
    print("\n[1/4] Scraping jobs from all platforms...")
    jobs_data = scrape_all_jobs()
    total_found = jobs_data.get("total_found", 0)
    print(f"  Found {total_found} total jobs before filtering")

    # Step 2: Filter duplicates (seen in last 7 days) + check active links
    print("\n[2/4] Filtering duplicates and inactive jobs...")
    filtered_data = filter_new_and_active(jobs_data)
    final_count = filtered_data.get("total_found", 0)
    print(f"  {final_count} new active jobs after filtering")

    # Step 3: Generate tailored resumes for top 5 ATS-matched jobs
    print("\n[3/4] Tailoring resumes for top 5 jobs...")
    tailored = tailor_all()
    print(f"  Generated {len(tailored)} tailored resumes")

    # Step 4: Send email digest with all jobs + tailored resumes
    print("\n[4/4] Sending email digest...")
    success = send_digest()

    if success:
        print("\n" + "=" * 60)
        print("  SUCCESS! Email sent with job digest")
        print(f"  Jobs: {final_count} | Tailored CVs: {len(tailored)}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("  Email sending failed - check GMAIL_APP_PASSWORD secret")
        print("=" * 60)
        sys.exit(1)
