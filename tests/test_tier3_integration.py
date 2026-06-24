"""Tier 3 Integration Tests.
"""

import os
import csv
import pytest
from job_hunt_agent.search import search_jobs, calculate_fit_score
from job_hunt_agent.customizer import customize_for_job
from job_hunt_agent.tracker import (
    init_tracker,
    add_job_to_tracker,
    update_job_status,
    save_job_file
)
from job_hunt_agent.apply import apply_to_job
from job_hunt_agent.integrations import (
    poll_gmail,
    schedule_calendar_event
)

def test_integration_search_to_customize(jobs_dir, candidate_profile):
    """Test 1: Job Search (F1) -> Fit Scoring (F3) -> Resume Customization (F4).
    """
    # 1. Search jobs
    jobs = search_jobs(query="Python", location="Remote", include_scams=False)
    assert len(jobs) > 0
    
    # 2. Select high fit job
    high_fit_jobs = [j for j in jobs if j["fit_score"] >= 8]
    assert len(high_fit_jobs) > 0
    selected_job = high_fit_jobs[0]
    
    # 3. Tailor resume and cover letter
    tailored = customize_for_job(selected_job, candidate_profile)
    resume_content = "\n".join(tailored["resume_bullets"])
    cover_content = tailored["cover_letter"]
    
    # 4. Save job files
    resume_file = save_job_file(
        category="Resumes",
        job_id=selected_job["job_id"],
        filename=f"{selected_job['job_id']}_resume.txt",
        content=resume_content,
        jobs_dir=jobs_dir
    )
    cover_file = save_job_file(
        category="CoverLetters",
        job_id=selected_job["job_id"],
        filename=f"{selected_job['job_id']}_cover.txt",
        content=cover_content,
        jobs_dir=jobs_dir
    )
    
    # 5. Verify files exist
    assert os.path.exists(resume_file)
    assert os.path.exists(cover_file)
    with open(resume_file, "r") as f:
        assert f.read() == resume_content
    with open(cover_file, "r") as f:
        assert f.read() == cover_content


def test_integration_apply_to_tracker_success(mock_server_url, jobs_dir, candidate_profile):
    """Test 2: Auto-Apply (F6) -> Tracker Update (F5) (on successful submit).
    """
    tracker_path = os.path.join(jobs_dir, "tracker.csv")
    init_tracker(tracker_path, jobs_dir=jobs_dir)
    
    job = {
        "job_id": "job_success_test",
        "company": "Success Corp",
        "position": "Developer",
        "source": "MockFeed",
        "location": "Remote",
        "salary": "$80,000"
    }
    
    # Track the job
    added = add_job_to_tracker(job, tracker_path, jobs_dir=jobs_dir)
    assert added is True
    
    # Save a temporary resume
    resume_path = save_job_file(
        category="Resumes",
        job_id=job["job_id"],
        filename="resume_success.txt",
        content="Proficient in Python and Linux automation.",
        jobs_dir=jobs_dir
    )
    
    # Perform auto-apply
    res = apply_to_job(
        url=f"{mock_server_url}/apply",
        candidate_info=candidate_profile,
        resume_path=resume_path
    )
    assert res["success"] is True
    
    # Update tracker
    updated = update_job_status(
        job_id=job["job_id"],
        status="Applied",
        tracker_path=tracker_path,
        notes="Applied successfully.",
        date_applied="2026-06-24",
        jobs_dir=jobs_dir
    )
    assert updated is True
    
    # Verify CSV status
    rows = []
    with open(tracker_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        for r in reader:
            rows.append(r)
            
    assert len(rows) == 1
    assert rows[0][0] == job["job_id"]
    assert rows[0][8] == "Applied"


def test_integration_apply_to_tracker_failure(mock_server_url, jobs_dir, candidate_profile):
    """Test 3: Auto-Apply (F6) -> Tracker Update (F5) (on failed submit).
    """
    tracker_path = os.path.join(jobs_dir, "tracker.csv")
    init_tracker(tracker_path, jobs_dir=jobs_dir)
    
    job = {
        "job_id": "job_fail_test",
        "company": "Fail Corp",
        "position": "Developer",
        "source": "MockFeed",
        "location": "Remote",
        "salary": "$50,000"
    }
    
    added = add_job_to_tracker(job, tracker_path, jobs_dir=jobs_dir)
    assert added is True
    
    resume_path = save_job_file(
        category="Resumes",
        job_id=job["job_id"],
        filename="resume_fail.txt",
        content="My resume content.",
        jobs_dir=jobs_dir
    )
    
    # Trigger a form validation failure by removing name from candidate_info
    invalid_profile = candidate_profile.copy()
    invalid_profile["name"] = ""  # Server expects non-empty name
    
    res = apply_to_job(
        url=f"{mock_server_url}/apply",
        candidate_info=invalid_profile,
        resume_path=resume_path
    )
    assert res["success"] is False
    assert "submission failed" in res["message"].lower() or "error" in res["message"].lower()
    
    # Update tracker to Failed Application
    updated = update_job_status(
        job_id=job["job_id"],
        status="Application Failed",
        tracker_path=tracker_path,
        notes=f"Failed application: {res['message'][:50]}",
        jobs_dir=jobs_dir
    )
    assert updated is True
    
    # Verify CSV status
    rows = []
    with open(tracker_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        for r in reader:
            rows.append(r)
            
    assert len(rows) == 1
    assert rows[0][0] == job["job_id"]
    assert rows[0][8] == "Application Failed"


def test_integration_tracker_to_calendar_success(jobs_dir, mock_calendar_service):
    """Test 4: Tracker Update (F5) -> Calendar Scheduling (F7).
    """
    tracker_path = os.path.join(jobs_dir, "tracker.csv")
    init_tracker(tracker_path, jobs_dir=jobs_dir)
    
    job = {
        "job_id": "job_cal_test",
        "company": "CalCorp",
        "position": "Manager",
        "status": "Applied"
    }
    add_job_to_tracker(job, tracker_path, jobs_dir=jobs_dir)
    
    # Update job in tracker to indicate interview scheduled
    updated = update_job_status(
        job_id=job["job_id"],
        status="Interview Scheduled",
        tracker_path=tracker_path,
        notes="Interview confirmed on 2026-06-28 at 14:00",
        jobs_dir=jobs_dir
    )
    assert updated is True
    
    # Read tracker to find scheduled interviews
    interview_jobs = []
    with open(tracker_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        for row in reader:
            if row and row[8] == "Interview Scheduled":
                interview_jobs.append(row)
                
    assert len(interview_jobs) == 1
    target_job = interview_jobs[0]
    
    # Parse date/time from notes (e.g. 2026-06-28 and 14:00)
    event_details = {
        "summary": f"Interview with {target_job[1]}",
        "start_time": "2026-06-28T14:00:00",
        "end_time": "2026-06-28T15:00:00",
        "description": f"Details: {target_job[9]}"
    }
    
    res = schedule_calendar_event(event_details, mock_calendar_service)
    assert res["success"] is True
    
    # Check that it exists in the calendar
    events = mock_calendar_service.list_events()
    assert len(events) == 1
    assert events[0]["id"] == res["event_id"]
    assert events[0]["summary"] == "Interview with CalCorp"


def test_integration_email_to_calendar_to_tracker(jobs_dir, mock_gmail_service, mock_calendar_service):
    """Test 5: Email Poll (F7) -> Calendar Scheduling (F7) -> Tracker Update (F5) (interview scheduled).
    """
    tracker_path = os.path.join(jobs_dir, "tracker.csv")
    init_tracker(tracker_path, jobs_dir=jobs_dir)
    
    job = {
        "job_id": "job_email_sync",
        "company": "EmailCorp",
        "position": "QA Engineer",
        "status": "Applied"
    }
    add_job_to_tracker(job, tracker_path, jobs_dir=jobs_dir)
    
    # Add email invite
    mock_gmail_service.add_mock_email(
        msg_id="sync_msg_01",
        subject="Interview invitation at EmailCorp",
        body="Hi applicant, please schedule your call on 2026-06-28 at 16:00.",
        date="2026-06-24"
    )
    
    # Poll gmail
    emails = poll_gmail(mock_gmail_service)
    assert len(emails) == 1
    mail = emails[0]
    assert mail["category"] == "Interview Invitation"
    
    # Schedule event
    date = mail["details"].get("date")
    time = mail["details"].get("time", "16:00")
    event_details = {
        "summary": f"Interview - {job['company']}",
        "start_time": f"{date}T{time}:00",
        "end_time": f"{date}T17:00:00",
        "description": f"Email message ID: {mail['message_id']}"
    }
    cal_res = schedule_calendar_event(event_details, mock_calendar_service)
    assert cal_res["success"] is True
    
    # Update tracker status
    updated = update_job_status(
        job_id=job["job_id"],
        status="Interview Scheduled",
        tracker_path=tracker_path,
        notes=f"Interview scheduled via email on {date} at {time}.",
        jobs_dir=jobs_dir
    )
    assert updated is True
    
    # Verify tracker
    rows = []
    with open(tracker_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        for r in reader:
            rows.append(r)
    assert rows[0][8] == "Interview Scheduled"
    assert "Interview scheduled via email" in rows[0][9]
    
    # Verify calendar
    events = mock_calendar_service.list_events()
    assert len(events) == 1
    assert events[0]["summary"] == "Interview - EmailCorp"
    assert events[0]["start_time"] == "2026-06-28T16:00:00"


def test_integration_email_rejection_to_tracker(jobs_dir, mock_gmail_service, mock_calendar_service):
    """Test 6: Email Poll (F7) -> Tracker Update (F5) (rejection received, ensuring no calendar event scheduled).
    """
    tracker_path = os.path.join(jobs_dir, "tracker.csv")
    init_tracker(tracker_path, jobs_dir=jobs_dir)
    
    job = {
        "job_id": "job_rej_sync",
        "company": "RejCorp",
        "position": "Developer",
        "status": "Applied"
    }
    add_job_to_tracker(job, tracker_path, jobs_dir=jobs_dir)
    
    # Add rejection email
    mock_gmail_service.add_mock_email(
        msg_id="rej_msg_01",
        subject="Application Status Update",
        body="Unfortunately, we are not moving forward with your application.",
        date="2026-06-24"
    )
    
    # Poll gmail
    emails = poll_gmail(mock_gmail_service)
    assert len(emails) == 1
    mail = emails[0]
    assert mail["category"] == "Rejection"
    
    # For rejection, do NOT schedule calendar event, only update tracker
    updated = update_job_status(
        job_id=job["job_id"],
        status="Rejected",
        tracker_path=tracker_path,
        notes="Received rejection email.",
        jobs_dir=jobs_dir
    )
    assert updated is True
    
    # Verify tracker
    rows = []
    with open(tracker_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        for r in reader:
            rows.append(r)
    assert rows[0][8] == "Rejected"
    
    # Ensure calendar remains empty
    events = mock_calendar_service.list_events()
    assert len(events) == 0
