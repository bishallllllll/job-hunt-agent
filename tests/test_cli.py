import os
import pytest
from job_hunt_agent.cli import main
from job_hunt_agent.mock_env import mock_emails, mock_calendar_events, submitted_applications

def test_cli_search(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["cli.py", "search", "-q", "Python", "-l", "Remote"])
    main()
    captured = capsys.readouterr()
    assert "Found" in captured.out
    assert "job_1" in captured.out

def test_cli_customize(monkeypatch, capsys, jobs_dir):
    monkeypatch.setattr("sys.argv", ["cli.py", "customize", "--job-id", "job_1", "--jobs-dir", jobs_dir])
    main()
    captured = capsys.readouterr()
    assert "Saved customized resume" in captured.out
    assert os.path.exists(os.path.join(jobs_dir, "Resumes", "job_1_resume.txt"))
    assert os.path.exists(os.path.join(jobs_dir, "CoverLetters", "job_1_cover_letter.txt"))

def test_cli_track_add_and_update(monkeypatch, capsys, jobs_dir):
    tracker_path = os.path.join(jobs_dir, "job_tracker.csv")
    
    # 1. Add
    monkeypatch.setattr("sys.argv", [
        "cli.py", "track", "job_1", "--action", "add", "--status", "Found", 
        "--notes", "Found online", "--jobs-dir", jobs_dir, "--tracker-path", tracker_path
    ])
    main()
    captured = capsys.readouterr()
    assert "Successfully added job job_1" in captured.out
    
    # Verify file
    assert os.path.exists(tracker_path)
    
    # 2. Update
    monkeypatch.setattr("sys.argv", [
        "cli.py", "track", "job_1", "--action", "update", "--status", "Applied", 
        "--notes", "Applied via site", "--jobs-dir", jobs_dir, "--tracker-path", tracker_path
    ])
    main()
    captured = capsys.readouterr()
    assert "Successfully updated job job_1" in captured.out

def test_cli_apply(monkeypatch, capsys, mock_server_url, jobs_dir):
    tracker_path = os.path.join(jobs_dir, "job_tracker.csv")
    
    # Create a resume file to pass
    resume_path = os.path.join(jobs_dir, "resume.txt")
    with open(resume_path, "w") as f:
        f.write("Candidate resume content.")
        
    # First, track the job
    monkeypatch.setattr("sys.argv", [
        "cli.py", "track", "job_1", "--action", "add", "--jobs-dir", jobs_dir, "--tracker-path", tracker_path
    ])
    main()
    
    # Apply
    monkeypatch.setattr("sys.argv", [
        "cli.py", "apply", "job_1", "--url", f"{mock_server_url}/apply", 
        "--resume-path", resume_path, "--jobs-dir", jobs_dir, "--tracker-path", tracker_path
    ])
    main()
    captured = capsys.readouterr()
    assert "Successfully applied to job job_1" in captured.out

def test_cli_sync_emails(monkeypatch, capsys, jobs_dir, mock_gmail_service):
    tracker_path = os.path.join(jobs_dir, "job_tracker.csv")
    
    # Track the job first so it matches the email company name
    monkeypatch.setattr("sys.argv", [
        "cli.py", "track", "job_1", "--action", "add", "--jobs-dir", jobs_dir, "--tracker-path", tracker_path
    ])
    main()
    
    # Add a mock email matching TechSolutions India (company name for job_1)
    mock_gmail_service.add_mock_email(
        msg_id="email_invite_01",
        subject="Interview schedule for Scripting Developer at TechSolutions India",
        body="Dear Bishal, we invite you for an interview on 2026-06-28 at 10:00 for job_1.",
        date="2026-06-24"
    )
    
    monkeypatch.setattr("sys.argv", [
        "cli.py", "sync-emails", "--jobs-dir", jobs_dir, "--tracker-path", tracker_path
    ])
    main()
    captured = capsys.readouterr()
    assert "Updated job job_1" in captured.out

def test_cli_sync_calendar(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", [
        "cli.py", "sync-calendar", "--summary", "Technical Interview",
        "--start-time", "2026-06-28T10:00:00", "--end-time", "2026-06-28T11:00:00",
        "--description", "Interview prep description"
    ])
    main()
    captured = capsys.readouterr()
    assert "Successfully scheduled calendar event" in captured.out

def test_cli_run_all(monkeypatch, capsys, mock_server_url, jobs_dir, mock_gmail_service):
    tracker_path = os.path.join(jobs_dir, "job_tracker.csv")
    
    # Add mock emails to poll
    mock_gmail_service.add_mock_email(
        msg_id="email_invite_01",
        subject="Interview schedule for TechSolutions India",
        body="Interview details on 2026-06-28 at 10:00 for job_1.",
        date="2026-06-24"
    )
    
    monkeypatch.setattr("sys.argv", [
        "cli.py", "run-all", "--query", "Python", "--location", "Remote",
        "--jobs-dir", jobs_dir, "--tracker-path", tracker_path, "--url", f"{mock_server_url}/apply"
    ])
    main()
    captured = capsys.readouterr()
    assert "Found" in captured.out
    assert "Applied to job_1" in captured.out
    assert "Scheduled interview for job_1" in captured.out


def test_cli_track_live_sheets(monkeypatch, capsys, jobs_dir, mocker):
    tracker_path = os.path.join(jobs_dir, "job_tracker.csv")
    
    # Mock RealSheetsService
    mock_sheets_cls = mocker.patch("job_hunt_agent.real_services.RealSheetsService")
    mock_instance = mock_sheets_cls.return_value
    mock_instance.spreadsheet_id = "test-spreadsheet-id"
    mock_instance.add_job.return_value = True
    mock_instance.update_job.return_value = True
    
    # 1. Track Add in live mode
    monkeypatch.setattr("sys.argv", [
        "cli.py", "track", "job_1", "--action", "add", "--status", "Found", 
        "--jobs-dir", jobs_dir, "--tracker-path", tracker_path,
        "--live", "--spreadsheet-id", "test-spreadsheet-id"
    ])
    main()
    captured = capsys.readouterr()
    assert "Successfully added job job_1" in captured.out
    assert "Synced job job_1 addition to Google Sheets" in captured.out
    mock_instance.add_job.assert_called_once()
    
    # 2. Track Update in live mode
    monkeypatch.setattr("sys.argv", [
        "cli.py", "track", "job_1", "--action", "update", "--status", "Applied",
        "--jobs-dir", jobs_dir, "--tracker-path", tracker_path,
        "--live", "--spreadsheet-id", "test-spreadsheet-id"
    ])
    main()
    captured = capsys.readouterr()
    assert "Successfully updated job job_1" in captured.out
    assert "Synced job job_1 update to Google Sheets" in captured.out
    mock_instance.update_job.assert_called_once()

