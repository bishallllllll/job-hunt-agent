"""Tests for Feature F5: Spreadsheet Tracker & Jobs Filesystem.
"""

import os
import csv
import pytest
from job_hunt_agent.tracker import (
    init_tracker,
    add_job_to_tracker,
    update_job_status,
    save_job_file,
    validate_path_in_jobs
)

# ==========================================
# Tier 1: Feature Coverage (Happy Paths)
# ==========================================

def test_init_tracker_happy_path(jobs_dir):
    """Test 1: Initializes the tracker CSV with standard headers.
    """
    tracker_path = os.path.join(jobs_dir, "applications.csv")
    init_tracker(tracker_path, jobs_dir=jobs_dir)
    
    assert os.path.exists(tracker_path)
    
    with open(tracker_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        
    expected_headers = [
        "Job ID", "Company", "Position", "Source", "Location", 
        "Salary", "Date Found", "Date Applied", "Status", "Notes"
    ]
    assert headers == expected_headers


def test_add_job_to_tracker_happy_path(jobs_dir):
    """Test 2: Adds a new job to the tracker successfully.
    """
    tracker_path = os.path.join(jobs_dir, "applications.csv")
    job = {
        "job_id": "job_101",
        "company": "TestCorp",
        "position": "Python Engineer",
        "source": "MockFeed",
        "location": "Remote",
        "salary": "$50,000",
        "date_applied": "",
        "status": "Found",
        "notes": "Looks interesting."
    }
    
    result = add_job_to_tracker(job, tracker_path, jobs_dir=jobs_dir)
    assert result is True
    
    with open(tracker_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        row = next(reader)
        
    assert row[0] == "job_101"
    assert row[1] == "TestCorp"
    assert row[2] == "Python Engineer"
    assert row[3] == "MockFeed"
    assert row[4] == "Remote"
    assert row[5] == "$50,000"
    assert row[8] == "Found"
    assert row[9] == "Looks interesting."


def test_update_job_status_happy_path(jobs_dir):
    """Test 3: Updates an existing job status and notes.
    """
    tracker_path = os.path.join(jobs_dir, "applications.csv")
    job = {
        "job_id": "job_102",
        "company": "CloudSystems",
        "position": "System Administrator",
        "status": "Found"
    }
    add_job_to_tracker(job, tracker_path, jobs_dir=jobs_dir)
    
    update_result = update_job_status(
        job_id="job_102",
        status="Applied",
        tracker_path=tracker_path,
        notes="Applied via form filler.",
        date_applied="2026-06-25",
        jobs_dir=jobs_dir
    )
    assert update_result is True
    
    with open(tracker_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        row = next(reader)
        
    assert row[0] == "job_102"
    assert row[7] == "2026-06-25"
    assert row[8] == "Applied"
    assert row[9] == "Applied via form filler."


def test_save_job_file_happy_path(jobs_dir):
    """Test 4: Saves files in different allowed categories under Jobs directory.
    """
    categories = ["Applications", "Resumes", "CoverLetters", "InterviewPrep"]
    for cat in categories:
        filename = f"doc_{cat}.txt"
        content = f"Content for {cat}"
        saved_path = save_job_file(cat, "job_abc", filename, content, jobs_dir=jobs_dir)
        
        assert os.path.exists(saved_path)
        assert saved_path.startswith(os.path.abspath(jobs_dir))
        
        with open(saved_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        assert file_content == content


def test_tracker_roundtrip_multiple_jobs(jobs_dir):
    """Test 5: Validates round-trip additions and checks row indexing.
    """
    tracker_path = os.path.join(jobs_dir, "applications.csv")
    job_1 = {"job_id": "job_001", "company": "A", "position": "P1", "status": "Found"}
    job_2 = {"job_id": "job_002", "company": "B", "position": "P2", "status": "Found"}
    
    assert add_job_to_tracker(job_1, tracker_path, jobs_dir=jobs_dir) is True
    assert add_job_to_tracker(job_2, tracker_path, jobs_dir=jobs_dir) is True
    
    rows = []
    with open(tracker_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        for r in reader:
            rows.append(r)
            
    assert len(rows) == 2
    assert rows[0][0] == "job_001"
    assert rows[1][0] == "job_002"


# ==========================================
# Tier 2: Boundary & Corner Cases (Unhappy Paths)
# ==========================================

def test_tracker_path_traversal_prevention(jobs_dir):
    """Test 6: Prevents tracker path traversal outside jobs_dir.
    """
    tracker_path = os.path.abspath(os.path.join(jobs_dir, "..", "malicious_tracker.csv"))
    job = {"job_id": "job_bad", "company": "EvilCorp"}
    
    with pytest.raises(ValueError) as excinfo:
        init_tracker(tracker_path, jobs_dir=jobs_dir)
    assert "Path traversal detected" in str(excinfo.value)
    
    with pytest.raises(ValueError) as excinfo:
        add_job_to_tracker(job, tracker_path, jobs_dir=jobs_dir)
    assert "Path traversal detected" in str(excinfo.value)


def test_save_file_path_traversal_prevention(jobs_dir):
    """Test 7: Prevents file path traversal outside jobs_dir.
    """
    with pytest.raises(ValueError) as excinfo:
        save_job_file(
            category="Resumes",
            job_id="job_bad",
            filename="../../malicious_resume.pdf",
            content="Hack",
            jobs_dir=jobs_dir
        )
    assert "Path traversal detected" in str(excinfo.value)


def test_add_duplicate_job_id(jobs_dir):
    """Test 8: Ensures duplicate job additions return False and do not duplicate.
    """
    tracker_path = os.path.join(jobs_dir, "applications.csv")
    job = {"job_id": "job_dup", "company": "Unique", "position": "Dev"}
    
    first_add = add_job_to_tracker(job, tracker_path, jobs_dir=jobs_dir)
    second_add = add_job_to_tracker(job, tracker_path, jobs_dir=jobs_dir)
    
    assert first_add is True
    assert second_add is False
    
    rows = []
    with open(tracker_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader) # skip header
        for r in reader:
            rows.append(r)
            
    assert len(rows) == 1


def test_save_file_invalid_category(jobs_dir):
    """Test 9: Fails when saving a file with an invalid category.
    """
    with pytest.raises(ValueError) as excinfo:
        save_job_file(
            category="InvalidCategory",
            job_id="job_id_1",
            filename="test.txt",
            content="some data",
            jobs_dir=jobs_dir
        )
    assert "Invalid category" in str(excinfo.value)


def test_update_nonexistent_job_or_missing_tracker(jobs_dir):
    """Test 10: Gracefully handles updates to missing jobs/trackers.
    """
    tracker_path = os.path.join(jobs_dir, "applications.csv")
    
    # Update on missing tracker file
    res = update_job_status("job_none", "Applied", tracker_path, jobs_dir=jobs_dir)
    assert res is False
    
    # Initialize tracker, then update non-existent job ID
    init_tracker(tracker_path, jobs_dir=jobs_dir)
    res2 = update_job_status("job_none", "Applied", tracker_path, jobs_dir=jobs_dir)
    assert res2 is False


def test_prefix_path_traversal_prevention(jobs_dir):
    """Test 11: Verifies that a prefix path traversal (e.g., 'Jobs_attacker.csv')
    is correctly rejected by validate_path_in_jobs when jobs_dir is defined.
    """
    parent_dir = os.path.dirname(jobs_dir)
    jobs_dir_name = os.path.basename(jobs_dir)
    attacker_path = os.path.join(parent_dir, f"{jobs_dir_name}_attacker.csv")
    
    with pytest.raises(ValueError) as excinfo:
        validate_path_in_jobs(attacker_path, jobs_dir)
    assert "Path traversal detected" in str(excinfo.value)
