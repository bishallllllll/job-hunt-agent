import argparse
import sys
import os
import csv
from datetime import datetime

from job_hunt_agent.search import search_jobs, BISHAL_PROFILE, MockScraper
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
from job_hunt_agent.mock_env import (
    MockGmailService,
    MockCalendarService
)

def _get_services(live=False):
    """Return Gmail and Calendar service instances based on mode."""
    if live:
        from job_hunt_agent.real_services import RealGmailService, RealCalendarService
        return RealGmailService(), RealCalendarService()
    return MockGmailService(), MockCalendarService()

def _get_sheets_service(live=False, spreadsheet_id=None):
    """Return Sheets service instance based on mode."""
    if live:
        from job_hunt_agent.real_services import RealSheetsService
        return RealSheetsService(spreadsheet_id=spreadsheet_id)
    return None


def get_job_by_id(job_id: str) -> dict:
    """Helper to resolve job details by ID from mock list or feed.
    """
    scraper = MockScraper()
    for job in scraper.jobs:
        if job["job_id"] == job_id:
            return job

    feed_jobs = [
        {
            "job_id": "job_001",
            "company": "TechCorp",
            "position": "Python Developer",
            "location": "Remote",
            "salary": "$60,000",
            "description": "Looking for a junior Python Developer with Linux automation skills. 12th pass okay."
        },
        {
            "job_id": "job_002",
            "company": "MLM Ventures",
            "position": "Marketing Executive",
            "location": "Tripura",
            "salary": "$20,000",
            "description": "Earn money fast by joining our multi-level marketing network! Upfront payment required."
        },
        {
            "job_id": "job_003",
            "company": "NetSystems",
            "position": "Network Associate",
            "location": "Tripura",
            "salary": "$30,000",
            "description": "Need a support technician to manage Linux systems and network routers."
        }
    ]

    for job in feed_jobs:
        if job["job_id"] == job_id:
            return job

    return None

def main():
    parser = argparse.ArgumentParser(description="Job Hunt Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Search subcommand
    search_parser = subparsers.add_parser("search", help="Search jobs and calculate fit scores")
    search_parser.add_argument("-q", "--query", default="", help="Search query")
    search_parser.add_argument("-l", "--location", default="", help="Location filter")
    search_parser.add_argument("--include-scams", action="store_true", help="Include flagged scams in results")

    # Customize subcommand
    customize_parser = subparsers.add_parser("customize", help="Customize resume and cover letter for a job")
    customize_parser.add_argument("--job-id", required=True, help="Job ID to customize documents for")
    customize_parser.add_argument("--jobs-dir", default="/Jobs", help="Jobs directory path")

    # Track subcommand
    track_parser = subparsers.add_parser("track", help="Add or update a job in the tracker")
    track_parser.add_argument("job_id", help="Job ID")
    track_parser.add_argument("--action", choices=["add", "update"], default="add", help="Tracker action")
    track_parser.add_argument("--status", default="Found", help="Job status")
    track_parser.add_argument("--notes", default=None, help="Notes for the job")
    track_parser.add_argument("--date-applied", default=None, help="Date applied (YYYY-MM-DD)")
    track_parser.add_argument("--jobs-dir", default="/Jobs", help="Jobs directory path")
    track_parser.add_argument("--tracker-path", default=None, help="Path to tracker CSV file")
    track_parser.add_argument("--live", action="store_true", help="Use real APIs (Google Sheets) instead of mock")
    track_parser.add_argument("--spreadsheet-id", default=None, help="Google Sheets Spreadsheet ID")

    # Apply subcommand
    apply_parser = subparsers.add_parser("apply", help="Automatically apply to a job using Playwright")
    apply_parser.add_argument("job_id", help="Job ID to apply to")
    apply_parser.add_argument("--url", default="http://localhost:5000/apply", help="Application form URL")
    apply_parser.add_argument("--resume-path", required=True, help="Path to resume file")
    apply_parser.add_argument("--screenshot-path", default=None, help="Path to save application screenshot")
    apply_parser.add_argument("--jobs-dir", default="/Jobs", help="Jobs directory path")
    apply_parser.add_argument("--tracker-path", default=None, help="Path to tracker CSV file")
    apply_parser.add_argument("--live", action="store_true", help="Use real APIs (Google Sheets) instead of mock")
    apply_parser.add_argument("--spreadsheet-id", default=None, help="Google Sheets Spreadsheet ID")

    # Sync-emails subcommand
    sync_emails_parser = subparsers.add_parser("sync-emails", help="Poll emails and update tracker status")
    sync_emails_parser.add_argument("--jobs-dir", default="/Jobs", help="Jobs directory path")
    sync_emails_parser.add_argument("--tracker-path", default=None, help="Path to tracker CSV file")
    sync_emails_parser.add_argument("--live", action="store_true", help="Use real Gmail API instead of mock")
    sync_emails_parser.add_argument("--spreadsheet-id", default=None, help="Google Sheets Spreadsheet ID")

    # Sync-calendar subcommand
    sync_calendar_parser = subparsers.add_parser("sync-calendar", help="Schedule a calendar event")
    sync_calendar_parser.add_argument("--summary", required=True, help="Event summary")
    sync_calendar_parser.add_argument("--start-time", required=True, help="Event start time (ISO)")
    sync_calendar_parser.add_argument("--end-time", required=True, help="Event end time (ISO)")
    sync_calendar_parser.add_argument("--description", default="", help="Event description")
    sync_calendar_parser.add_argument("--live", action="store_true", help="Use real Google Calendar API instead of mock")

    # Run-all subcommand
    run_all_parser = subparsers.add_parser("run-all", help="Run the entire job search, customization, apply, and sync pipeline")
    run_all_parser.add_argument("-q", "--query", default="", help="Search query")
    run_all_parser.add_argument("-l", "--location", default="", help="Location filter")
    run_all_parser.add_argument("--jobs-dir", default="/Jobs", help="Jobs directory path")
    run_all_parser.add_argument("--tracker-path", default=None, help="Path to tracker CSV file")
    run_all_parser.add_argument("--url", default="http://localhost:5000/apply", help="Application form URL")
    run_all_parser.add_argument("--live", action="store_true", help="Use real Gmail/Calendar APIs instead of mocks")
    run_all_parser.add_argument("--spreadsheet-id", default=None, help="Google Sheets Spreadsheet ID")


    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.command == "search":
        jobs = search_jobs(args.query, args.location, include_scams=args.include_scams)
        if not jobs:
            print("No jobs found matching the criteria.")
            return

        print(f"\nFound {len(jobs)} jobs:")
        print("-" * 80)
        for job in jobs:
            scam_str = " [SCAM]" if job.get("is_scam") else ""
            print(f"ID: {job.get('job_id')} | {job.get('position')} | {job.get('company')} | {job.get('location')}{scam_str}")
            print(f"Salary: {job.get('salary')} | Source: {job.get('source')} | Fit Score: {job.get('fit_score')}/10")
            print(f"Description: {job.get('description')[:120]}...")
            print("-" * 80)

    elif args.command == "customize":
        job = get_job_by_id(args.job_id)
        if not job:
            print(f"Job with ID {args.job_id} not found.")
            sys.exit(1)

        tailored = customize_for_job(job, BISHAL_PROFILE)
        resume_content = "\n".join(tailored["resume_bullets"])
        resume_file = save_job_file(
            category="Resumes",
            job_id=args.job_id,
            filename=f"{args.job_id}_resume.txt",
            content=resume_content,
            jobs_dir=args.jobs_dir
        )
        cover_letter_file = save_job_file(
            category="CoverLetters",
            job_id=args.job_id,
            filename=f"{args.job_id}_cover_letter.txt",
            content=tailored["cover_letter"],
            jobs_dir=args.jobs_dir
        )
        print(f"Saved customized resume: {resume_file}")
        print(f"Saved customized cover letter: {cover_letter_file}")

    elif args.command == "track":
        tracker_path = args.tracker_path or os.path.join(args.jobs_dir, "job_tracker.csv")
        if args.action == "add":
            job = get_job_by_id(args.job_id)
            if not job:
                job = {
                    "job_id": args.job_id,
                    "company": "Unknown",
                    "position": "Unknown",
                    "source": "CLI",
                    "location": "Unknown",
                    "salary": "Unknown"
                }
            job_copy = job.copy()
            job_copy["status"] = args.status
            if args.notes is not None:
                job_copy["notes"] = args.notes
            if args.date_applied is not None:
                job_copy["date_applied"] = args.date_applied

            success = add_job_to_tracker(job_copy, tracker_path, jobs_dir=args.jobs_dir)
            if success:
                print(f"Successfully added job {args.job_id} to tracker.")
            else:
                print(f"Job {args.job_id} already exists in tracker.")

            if getattr(args, "live", False):
                sheets_service = _get_sheets_service(live=True, spreadsheet_id=args.spreadsheet_id)
                if sheets_service and sheets_service.spreadsheet_id:
                    sheets_service.add_job(job_copy)
                    print(f"Synced job {args.job_id} addition to Google Sheets.")
        else:
            success = update_job_status(
                job_id=args.job_id,
                status=args.status,
                tracker_path=tracker_path,
                notes=args.notes,
                date_applied=args.date_applied,
                jobs_dir=args.jobs_dir
            )
            if success:
                print(f"Successfully updated job {args.job_id} in tracker.")
            else:
                print(f"Job {args.job_id} not found in tracker to update.")
                sys.exit(1)

            if getattr(args, "live", False):
                sheets_service = _get_sheets_service(live=True, spreadsheet_id=args.spreadsheet_id)
                if sheets_service and sheets_service.spreadsheet_id:
                    sheets_service.update_job(
                        job_id=args.job_id,
                        status=args.status,
                        notes=args.notes,
                        date_applied=args.date_applied
                    )
                    print(f"Synced job {args.job_id} update to Google Sheets.")

    elif args.command == "apply":
        tracker_path = args.tracker_path or os.path.join(args.jobs_dir, "job_tracker.csv")
        candidate_info = BISHAL_PROFILE.copy()
        if os.path.exists(args.resume_path):
            try:
                with open(args.resume_path, "r", encoding="utf-8") as f:
                    resume_content = f.read().strip()
                candidate_info["qualifications"] = "Tailored qualifications: " + resume_content
            except Exception:
                pass

        res = apply_to_job(
            url=args.url,
            candidate_info=candidate_info,
            resume_path=args.resume_path,
            screenshot_path=args.screenshot_path
        )
        if res["success"]:
            print(f"Successfully applied to job {args.job_id}.")
            update_job_status(
                job_id=args.job_id,
                status="Applied",
                tracker_path=tracker_path,
                notes="Applied successfully via CLI.",
                date_applied=datetime.now().strftime("%Y-%m-%d"),
                jobs_dir=args.jobs_dir
            )
            if getattr(args, "live", False):
                sheets_service = _get_sheets_service(live=True, spreadsheet_id=args.spreadsheet_id)
                if sheets_service and sheets_service.spreadsheet_id:
                    sheets_service.update_job(
                        job_id=args.job_id,
                        status="Applied",
                        notes="Applied successfully via CLI.",
                        date_applied=datetime.now().strftime("%Y-%m-%d")
                    )
                    print(f"Synced application for job {args.job_id} to Google Sheets.")
        else:
            print(f"Failed to apply to job {args.job_id}: {res.get('message')}")
            sys.exit(1)

    elif args.command == "sync-emails":
        tracker_path = args.tracker_path or os.path.join(args.jobs_dir, "job_tracker.csv")
        gmail_service, _ = _get_services(getattr(args, 'live', False))
        sheets_service = _get_sheets_service(getattr(args, 'live', False), getattr(args, 'spreadsheet_id', None))
        service = gmail_service
        emails = poll_gmail(service)

        tracked_jobs = []
        if os.path.exists(tracker_path):
            with open(tracker_path, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if headers:
                    for row in reader:
                        if row:
                            tracked_jobs.append(row)

        for email_data in emails:
            combined_text = (email_data["subject"] + " " + email_data["body"]).lower()
            matched_job_id = None
            matched_company = None
            for row in tracked_jobs:
                jid, company = row[0], row[1]
                if jid.lower() in combined_text or (company and company.lower() in combined_text):
                    matched_job_id = jid
                    matched_company = company
                    break

            if matched_job_id:
                category = email_data["category"]
                status = None
                notes = None
                if category == "Interview Invitation":
                    status = "Interview Scheduled"
                    date = email_data["details"].get("date", "")
                    time = email_data["details"].get("time", "")
                    notes = f"Interview scheduled on {date} at {time}."
                elif category == "Assessment":
                    status = "Assessment"
                    deadline = email_data["details"].get("deadline", "")
                    notes = f"Assessment deadline: {deadline}."
                elif category == "Rejection":
                    status = "Rejected"
                    notes = "Received rejection email."
                elif category == "Offer":
                    status = "Offer Received"
                    notes = "Received job offer!"

                if status:
                    update_job_status(
                        job_id=matched_job_id,
                        status=status,
                        tracker_path=tracker_path,
                        notes=notes,
                        jobs_dir=args.jobs_dir
                    )
                    print(f"Updated job {matched_job_id} ({matched_company}) to '{status}' based on email.")
                    if sheets_service and sheets_service.spreadsheet_id:
                        sheets_service.update_job(
                            job_id=matched_job_id,
                            status=status,
                            notes=notes
                        )
                        print(f"Synced update for job {matched_job_id} to Google Sheets.")

    elif args.command == "sync-calendar":
        _, calendar_service = _get_services(getattr(args, 'live', False))
        service = calendar_service
        event_details = {
            "summary": args.summary,
            "start_time": args.start_time,
            "end_time": args.end_time,
            "description": args.description
        }
        res = schedule_calendar_event(event_details, service)
        if res["success"]:
            print(f"Successfully scheduled calendar event: {res['event_id']}")
        else:
            print(f"Failed to schedule event: {res.get('error')}")
            sys.exit(1)

    elif args.command == "run-all":
        tracker_path = args.tracker_path or os.path.join(args.jobs_dir, "job_tracker.csv")
        # Step 1: Search
        jobs = search_jobs(args.query, args.location, include_scams=False)
        # Step 2: Filter high fit
        high_fit_jobs = [j for j in jobs if j.get("fit_score", 0) >= 6]
        print(f"Found {len(high_fit_jobs)} high-fit jobs to apply to.")

        # Initialize services
        gmail_service, calendar_service = _get_services(getattr(args, 'live', False))
        sheets_service = _get_sheets_service(getattr(args, 'live', False), getattr(args, 'spreadsheet_id', None))

        for job in high_fit_jobs:
            job_id = job["job_id"]

            # Add to tracker
            add_job_to_tracker(job, tracker_path, jobs_dir=args.jobs_dir)
            if sheets_service and sheets_service.spreadsheet_id:
                sheets_service.add_job(job)
                print(f"Synced job {job_id} addition to Google Sheets.")

            # Tailor
            tailored = customize_for_job(job, BISHAL_PROFILE)
            resume_content = "\n".join(tailored["resume_bullets"])
            resume_file = save_job_file(
                category="Resumes",
                job_id=job_id,
                filename=f"{job_id}_resume.txt",
                content=resume_content,
                jobs_dir=args.jobs_dir
            )
            save_job_file(
                category="CoverLetters",
                job_id=job_id,
                filename=f"{job_id}_cover_letter.txt",
                content=tailored["cover_letter"],
                jobs_dir=args.jobs_dir
            )

            # Apply
            candidate_info = BISHAL_PROFILE.copy()
            candidate_info["qualifications"] = "Tailored qualifications: " + resume_content
            screenshot_path = os.path.join(args.jobs_dir, "Screenshots", f"{job_id}_screenshot.png")

            apply_res = apply_to_job(
                url=args.url,
                candidate_info=candidate_info,
                resume_path=resume_file,
                screenshot_path=screenshot_path
            )

            if apply_res["success"]:
                update_job_status(
                    job_id=job_id,
                    status="Applied",
                    tracker_path=tracker_path,
                    notes="Applied successfully via run-all pipeline.",
                    date_applied=datetime.now().strftime("%Y-%m-%d"),
                    jobs_dir=args.jobs_dir
                )
                print(f"Applied to {job_id} and updated tracker.")
                if sheets_service and sheets_service.spreadsheet_id:
                    sheets_service.update_job(
                        job_id=job_id,
                        status="Applied",
                        notes="Applied successfully via run-all pipeline.",
                        date_applied=datetime.now().strftime("%Y-%m-%d")
                    )
                    print(f"Synced application update for job {job_id} to Google Sheets.")
            else:
                print(f"Failed applying to {job_id}: {apply_res.get('message')}")

        # Poll emails
        emails = poll_gmail(gmail_service)

        tracked_jobs = []
        if os.path.exists(tracker_path):
            with open(tracker_path, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if headers:
                    for row in reader:
                        if row:
                            tracked_jobs.append(row)

        for email_data in emails:
            combined_text = (email_data["subject"] + " " + email_data["body"]).lower()
            matched_job_id = None
            matched_company = None
            for row in tracked_jobs:
                jid, company = row[0], row[1]
                if jid.lower() in combined_text or (company and company.lower() in combined_text):
                    matched_job_id = jid
                    matched_company = company
                    break

            if matched_job_id:
                category = email_data["category"]
                status = None
                notes = None
                if category == "Interview Invitation":
                    status = "Interview Scheduled"
                    date = email_data["details"].get("date")
                    time = email_data["details"].get("time", "10:00")
                    notes = f"Interview scheduled on {date} at {time}."

                    # Schedule calendar event
                    start_iso = f"{date}T{time}:00"
                    try:
                        t_parts = time.split(":")
                        hr = int(t_parts[0])
                        mn = int(t_parts[1])
                        end_hr = (hr + 1) % 24
                        end_iso = f"{date}T{end_hr:02d}:{mn:02d}:00"
                    except Exception:
                        end_iso = f"{date}T11:00:00"

                    event_details = {
                        "summary": f"Technical Interview - {matched_job_id} {matched_company}",
                        "start_time": start_iso,
                        "end_time": end_iso,
                        "description": f"Interview details from email {email_data['message_id']}."
                    }
                    schedule_calendar_event(event_details, calendar_service)
                    print(f"Scheduled interview for {matched_job_id} on {date} at {time}.")

                elif category == "Assessment":
                    status = "Assessment"
                    deadline = email_data["details"].get("deadline", "")
                    notes = f"Assessment deadline: {deadline}."
                elif category == "Rejection":
                    status = "Rejected"
                    notes = "Received rejection email."
                elif category == "Offer":
                    status = "Offer Received"
                    notes = "Received job offer!"

                if status:
                    update_job_status(
                        job_id=matched_job_id,
                        status=status,
                        tracker_path=tracker_path,
                        notes=notes,
                        jobs_dir=args.jobs_dir
                    )
                    print(f"Updated job {matched_job_id} to {status} based on email.")
                    if sheets_service and sheets_service.spreadsheet_id:
                        sheets_service.update_job(
                            job_id=matched_job_id,
                            status=status,
                            notes=notes
                        )
                        print(f"Synced update for job {matched_job_id} to Google Sheets.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

