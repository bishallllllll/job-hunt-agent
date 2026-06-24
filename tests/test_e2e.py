"""Tier 4 E2E Real-World Scenario Test.
"""

import os
import csv
import pytest
from job_hunt_agent.search import search_jobs
from job_hunt_agent.customizer import customize_for_job
from job_hunt_agent.tracker import (
    add_job_to_tracker,
    update_job_status,
    save_job_file
)
from job_hunt_agent.apply import apply_to_job
from job_hunt_agent.integrations import (
    poll_gmail,
    schedule_calendar_event
)
from job_hunt_agent.mock_env import submitted_applications

def test_full_job_hunt_lifecycle_e2e(
    mock_server_url,
    candidate_profile,
    mock_gmail_service,
    mock_calendar_service,
    jobs_dir
):
    """Tier 4 E2E Test:
    Runs the full lifecycle of a job hunt from searching and filtering
    to document tailoring, form application, status tracking, email
    monitoring, and calendar event scheduling.
    """
    tracker_path = os.path.join(jobs_dir, "job_tracker.csv")

    # Step 1: Run Job Search & Listing Extraction (excluding scams)
    # Search for Remote/Tripura Python/Linux/Networking jobs by calling CLI subcommand 'search' programmatically
    from job_hunt_agent.cli import main
    from unittest.mock import patch
    import io

    with patch("sys.argv", ["cli.py", "search"]):
        f = io.StringIO()
        with patch("sys.stdout", f):
            main()
        output = f.getvalue()
        assert "Found 5 jobs" in output

    jobs = search_jobs(query="", location="", include_scams=False)
    
    # We expect 5 non-scam jobs from our MockScraper (job_1, job_2, job_3, job_4, job_8)
    assert len(jobs) == 5
    
    # Step 2: Fit Score Filtering (Fit Score >= 6)
    high_fit_jobs = [j for j in jobs if j["fit_score"] >= 6]
    # Expecting job_1, job_2, job_3 to be high fit (scores 10, 10, 9)
    assert len(high_fit_jobs) == 3
    assert {j["job_id"] for j in high_fit_jobs} == {"job_1", "job_2", "job_3"}

    # Step 3: Customized Documents Saving to /Jobs & Auto-Apply & Tracking
    for job in high_fit_jobs:
        job_id = job["job_id"]
        
        # Add to tracker first
        added = add_job_to_tracker(job, tracker_path, jobs_dir=jobs_dir)
        assert added is True
        
        # Tailor resume and cover letter
        tailored = customize_for_job(job, candidate_profile)
        
        # Save resume bullet points and cover letter in the Jobs filesystem
        resume_content = "\n".join(tailored["resume_bullets"])
        resume_file = save_job_file(
            category="Resumes",
            job_id=job_id,
            filename=f"{job_id}_resume.txt",
            content=resume_content,
            jobs_dir=jobs_dir
        )
        
        cover_letter_file = save_job_file(
            category="CoverLetters",
            job_id=job_id,
            filename=f"{job_id}_cover_letter.txt",
            content=tailored["cover_letter"],
            jobs_dir=jobs_dir
        )
        
        assert os.path.exists(resume_file)
        assert os.path.exists(cover_letter_file)
        
        # Auto-apply via Playwright Form Filler to mock server
        # (Pass the candidate profile copy with tailored qualifications)
        candidate_info = candidate_profile.copy()
        candidate_info["qualifications"] = "Tailored qualifications: " + resume_content
        
        apply_res = apply_to_job(
            url=f"{mock_server_url}/apply",
            candidate_info=candidate_info,
            resume_path=resume_file
        )
        
        assert apply_res["success"] is True
        
        # Update tracker status to Applied
        updated = update_job_status(
            job_id=job_id,
            status="Applied",
            tracker_path=tracker_path,
            notes="Applied successfully via E2E auto-apply.",
            date_applied="2026-06-24",
            jobs_dir=jobs_dir
        )
        assert updated is True

    # Check mock server submission count
    assert len(submitted_applications) == 3

    # Step 4: Email Monitoring (Interview invitation received)
    # Add a mock email corresponding to job_1 interview invite
    mock_gmail_service.add_mock_email(
        msg_id="email_invite_01",
        subject="Interview schedule for Scripting Developer at TechSolutions India",
        body="Dear Bishal, we are pleased to invite you for an interview on 2026-06-28 at 10:00 for job_1.",
        date="2026-06-24"
    )

    # Add a mock email corresponding to job_2 rejection
    mock_gmail_service.add_mock_email(
        msg_id="email_rej_01",
        subject="Tripura Telecoms Update",
        body="Dear applicant, unfortunately we are not moving forward with your application.",
        date="2026-06-24"
    )

    # Poll email monitor
    parsed_emails = poll_gmail(mock_gmail_service)
    assert len(parsed_emails) == 2

    # Step 5: Calendar Sync & Tracker Status Update
    # Read tracker CSV to match emails with jobs dynamically
    current_tracked_jobs = []
    with open(tracker_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        for row in reader:
            if row:
                current_tracked_jobs.append({
                    "job_id": row[0],
                    "company": row[1],
                    "position": row[2]
                })

    for mail in parsed_emails:
        # Dynamic email-to-job matching: do NOT hardcode job IDs.
        email_text = (mail["subject"] + " " + mail["body"]).lower()
        matched_job = None
        for tj in current_tracked_jobs:
            if (tj["job_id"].lower() in email_text or 
                (tj["company"] and tj["company"].lower() in email_text) or
                (tj["position"] and tj["position"].lower() in email_text)):
                matched_job = tj
                break
        
        assert matched_job is not None, f"Could not match email to any tracked job. Email subject: {mail['subject']}"
        matched_job_id = matched_job["job_id"]
        matched_company = matched_job["company"]

        if mail["category"] == "Interview Invitation":
            # Extract date & time
            interview_date = mail["details"].get("date")
            interview_time = mail["details"].get("time", "10:00")
            
            # Construct start & end ISO strings
            start_iso = f"{interview_date}T{interview_time}:00"
            end_iso = f"{interview_date}T11:00:00"
            
            event_details = {
                "summary": f"Technical Interview - {matched_job_id} {matched_company}",
                "start_time": start_iso,
                "end_time": end_iso,
                "description": f"Interview details from email {mail['message_id']}."
            }
            
            # Schedule event
            cal_res = schedule_calendar_event(event_details, mock_calendar_service)
            assert cal_res["success"] is True
            
            # Update tracker status to Interview Scheduled
            updated_tracker = update_job_status(
                job_id=matched_job_id,
                status="Interview Scheduled",
                tracker_path=tracker_path,
                notes=f"Interview scheduled on {interview_date} at {interview_time}.",
                jobs_dir=jobs_dir
            )
            assert updated_tracker is True

        elif mail["category"] == "Rejection":
            # Update tracker status to Rejected
            updated_tracker = update_job_status(
                job_id=matched_job_id,
                status="Rejected",
                tracker_path=tracker_path,
                notes="Received rejection email.",
                jobs_dir=jobs_dir
            )
            assert updated_tracker is True

    # Step 6: Verify Final Tracker State & Filesystem State
    # Read tracker CSV content
    tracked_jobs = []
    with open(tracker_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        for row in reader:
            tracked_jobs.append(row)
            
    # Verify we tracked exactly 3 jobs
    assert len(tracked_jobs) == 3
    
    # Check status of jobs dynamically based on their company name
    job_1_row = [r for r in tracked_jobs if "techsolutions" in r[1].lower()][0]
    assert job_1_row[8] == "Interview Scheduled"
    assert "Interview scheduled" in job_1_row[9]
    
    job_2_row = [r for r in tracked_jobs if "tripura" in r[1].lower()][0]
    assert job_2_row[8] == "Rejected"
    
    job_3_row = [r for r in tracked_jobs if "global hosters" in r[1].lower()][0]
    assert job_3_row[8] == "Applied"

    # Check Google Calendar scheduled event
    calendar_events = mock_calendar_service.list_events()
    assert len(calendar_events) == 1
    assert job_1_row[0] in calendar_events[0]["summary"]
    assert job_1_row[1] in calendar_events[0]["summary"]
    assert calendar_events[0]["start_time"] == "2026-06-28T10:00:00"
