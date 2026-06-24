"""Spreadsheet Tracker and File Organization.
"""

import os
import csv
from datetime import datetime

def validate_path_in_jobs(path: str, jobs_dir: str) -> str:
    """Enforces that a path resolves strictly within the jobs_dir directory
    to prevent writing outside the designated area.
    """
    abs_jobs_dir = os.path.abspath(jobs_dir)
    abs_path = os.path.abspath(path)
    try:
        if os.path.commonpath([abs_jobs_dir, abs_path]) != abs_jobs_dir:
            raise ValueError(f"Path traversal detected! Path '{path}' is outside Jobs directory '{jobs_dir}'")
    except Exception:
        raise ValueError(f"Path traversal detected! Path '{path}' is outside Jobs directory '{jobs_dir}'")
    return abs_path

def init_tracker(tracker_path: str, jobs_dir: str = "/Jobs") -> None:
    """Initializes the CSV tracker with headers if it does not exist.
    """
    validate_path_in_jobs(tracker_path, jobs_dir)
    
    os.makedirs(os.path.dirname(tracker_path), exist_ok=True)
    if not os.path.exists(tracker_path):
        with open(tracker_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Job ID", "Company", "Position", "Source", "Location", 
                "Salary", "Date Found", "Date Applied", "Status", "Notes"
            ])

def add_job_to_tracker(job: dict, tracker_path: str, jobs_dir: str = "/Jobs") -> bool:
    """Appends a new job to the tracker if it doesn't already exist.
    """
    validate_path_in_jobs(tracker_path, jobs_dir)
    init_tracker(tracker_path, jobs_dir)
    
    job_id = job.get("job_id", "")
    
    # Check if job_id already exists in tracker
    exists = False
    with open(tracker_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        if headers:
            for row in reader:
                if row and row[0] == job_id:
                    exists = True
                    break
                    
    if exists:
        return False
        
    # Append new row
    with open(tracker_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            job_id,
            job.get("company", ""),
            job.get("position", ""),
            job.get("source", "MockFeed"),
            job.get("location", ""),
            job.get("salary", ""),
            datetime.now().strftime("%Y-%m-%d"),
            job.get("date_applied", ""),
            job.get("status", "Found"),
            job.get("notes", "")
        ])
    return True

def update_job_status(job_id: str, status: str, tracker_path: str, notes: str = None, date_applied: str = None, jobs_dir: str = "/Jobs") -> bool:
    """Updates the status and other fields for a job in the tracker.
    """
    validate_path_in_jobs(tracker_path, jobs_dir)
    if not os.path.exists(tracker_path):
        return False
        
    rows = []
    updated = False
    with open(tracker_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        if headers:
            rows.append(headers)
            for row in reader:
                if row and row[0] == job_id:
                    if len(row) < 10:
                        row.extend([""] * (10 - len(row)))
                    # Update status
                    row[8] = status
                    if notes is not None:
                        row[9] = notes
                    if date_applied is not None:
                        row[7] = date_applied
                    updated = True
                rows.append(row)
                
    if updated:
        with open(tracker_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
            
    return updated

def save_job_file(category: str, job_id: str, filename: str, content: str, jobs_dir: str = "/Jobs") -> str:
    """Saves a job-related file (e.g. customized resume, cover letter, interview prep notes)
    strictly within the Jobs directory sub-folders.
    """
    allowed_categories = ["Applications", "Resumes", "CoverLetters", "InterviewPrep"]
    if category not in allowed_categories:
        raise ValueError(f"Invalid category '{category}'. Must be one of {allowed_categories}")
        
    target_dir = os.path.join(jobs_dir, category)
    target_file = os.path.join(target_dir, filename)
    
    # Enforce directory constraints
    validate_path_in_jobs(target_file, jobs_dir)
    
    os.makedirs(target_dir, exist_ok=True)
    with open(target_file, mode="w", encoding="utf-8") as f:
        f.write(content)
        
    return target_file
