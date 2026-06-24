"""Tests for Feature F6: Playwright Auto-Apply Form Filler.
"""

import os
import pytest
from job_hunt_agent.apply import apply_to_job
from job_hunt_agent.mock_env import submitted_applications, MockHTTPRequestHandler


# ==========================================
# Tier 1: Feature Coverage (Happy Paths)
# ==========================================

def test_apply_happy_path(mock_server_url, candidate_profile, tmp_path):
    """Test 1: Standard happy-path application submittal.
    """
    resume_path = os.path.join(tmp_path, "resume.pdf")
    with open(resume_path, "w") as f:
        f.write("Mock Resume Content")

    result = apply_to_job(
        url=f"{mock_server_url}/apply",
        candidate_info=candidate_profile,
        resume_path=resume_path
    )

    assert result["success"] is True
    assert "submitted successfully" in result["message"]
    assert len(submitted_applications) == 1
    assert submitted_applications[0]["name"] == candidate_profile["name"]
    assert submitted_applications[0]["email"] == candidate_profile["email"]


def test_apply_with_screenshot(mock_server_url, candidate_profile, tmp_path):
    """Test 2: Verifies screenshot is captured and saved correctly.
    """
    resume_path = os.path.join(tmp_path, "resume.pdf")
    with open(resume_path, "w") as f:
        f.write("Mock Resume Content")

    screenshot_path = os.path.join(tmp_path, "screenshots", "apply_success.png")

    result = apply_to_job(
        url=f"{mock_server_url}/apply",
        candidate_info=candidate_profile,
        resume_path=resume_path,
        screenshot_path=screenshot_path
    )

    assert result["success"] is True
    assert result["screenshot"] == screenshot_path
    assert os.path.exists(screenshot_path)


def test_apply_qualifications_textarea(mock_server_url, candidate_profile, tmp_path):
    """Test 3: Checks qualifications multi-line details are preserved.
    """
    resume_path = os.path.join(tmp_path, "resume.pdf")
    with open(resume_path, "w") as f:
        f.write("Mock Resume Content")

    profile_with_long_qual = candidate_profile.copy()
    profile_with_long_qual["qualifications"] = "Line 1: Python Developer\nLine 2: CCNA Certified\nLine 3: Linux Administrator"

    result = apply_to_job(
        url=f"{mock_server_url}/apply",
        candidate_info=profile_with_long_qual,
        resume_path=resume_path
    )

    assert result["success"] is True
    assert submitted_applications[-1]["qualifications"] == profile_with_long_qual["qualifications"]


def test_apply_resume_with_spaces_in_filename(mock_server_url, candidate_profile, tmp_path):
    """Test 4: Checks that a resume filename with spaces is handled correctly.
    """
    resume_path = os.path.join(tmp_path, "Bishal Sarkar Resume 2026.pdf")
    with open(resume_path, "w") as f:
        f.write("Mock Resume Content")

    result = apply_to_job(
        url=f"{mock_server_url}/apply",
        candidate_info=candidate_profile,
        resume_path=resume_path
    )

    assert result["success"] is True
    assert submitted_applications[-1]["resume_name"] == "Bishal Sarkar Resume 2026.pdf"


def test_apply_multiple_consecutive_runs(mock_server_url, candidate_profile, tmp_path):
    """Test 5: Checks multiple sequential applications to ensure isolation.
    """
    resume_path = os.path.join(tmp_path, "resume.pdf")
    with open(resume_path, "w") as f:
        f.write("Mock Resume Content")

    result_1 = apply_to_job(
        url=f"{mock_server_url}/apply",
        candidate_info=candidate_profile,
        resume_path=resume_path
    )
    assert result_1["success"] is True

    result_2 = apply_to_job(
        url=f"{mock_server_url}/apply",
        candidate_info=candidate_profile,
        resume_path=resume_path
    )
    assert result_2["success"] is True
    assert len(submitted_applications) >= 2


# ==========================================
# Tier 2: Boundary & Corner Cases (Unhappy Paths)
# ==========================================

def test_apply_resume_missing(mock_server_url, candidate_profile):
    """Test 6: Fails gracefully when resume path does not exist.
    """
    result = apply_to_job(
        url=f"{mock_server_url}/apply",
        candidate_info=candidate_profile,
        resume_path="/invalid/path/to/resume.pdf"
    )
    assert result["success"] is False
    assert "Resume file not found" in result["message"]


def test_apply_missing_name_field(mock_server_url, candidate_profile, tmp_path):
    """Test 7: Fails when required 'name' field is empty/missing.
    """
    resume_path = os.path.join(tmp_path, "resume.pdf")
    with open(resume_path, "w") as f:
        f.write("Mock Resume Content")

    profile_missing_name = candidate_profile.copy()
    profile_missing_name["name"] = ""

    result = apply_to_job(
        url=f"{mock_server_url}/apply",
        candidate_info=profile_missing_name,
        resume_path=resume_path
    )
    assert result["success"] is False
    assert "submission failed" in result["message"].lower() or "error" in result["message"].lower()


def test_apply_invalid_email_format(mock_server_url, candidate_profile, tmp_path):
    """Test 8: Fails when email format is invalid (missing '@').
    """
    resume_path = os.path.join(tmp_path, "resume.pdf")
    with open(resume_path, "w") as f:
        f.write("Mock Resume Content")

    profile_invalid_email = candidate_profile.copy()
    profile_invalid_email["email"] = "invalidemail.com"

    result = apply_to_job(
        url=f"{mock_server_url}/apply",
        candidate_info=profile_invalid_email,
        resume_path=resume_path
    )
    assert result["success"] is False
    assert "submission failed" in result["message"].lower() or "error" in result["message"].lower()


def test_apply_slow_page_load_timeout(candidate_profile, tmp_path, mocker):
    """Test 9: Fails when page navigation times out.
    """
    resume_path = os.path.join(tmp_path, "resume.pdf")
    with open(resume_path, "w") as f:
        f.write("Mock Resume Content")

    # Mock page.goto to raise an exception simulating a timeout
    from playwright.sync_api import Error
    mocker.patch("playwright.sync_api._generated.Page.goto", side_effect=Error("Timeout exceeded."))

    result = apply_to_job(
        url="http://localhost:9999/apply",
        candidate_info=candidate_profile,
        resume_path=resume_path
    )
    assert result["success"] is False
    assert "Playwright automation encountered an error" in result["message"]


def test_apply_server_500_error(mock_server_url, candidate_profile, tmp_path, monkeypatch):
    """Test 10: Fails when the server returns a 500 error on form submittal.
    """
    resume_path = os.path.join(tmp_path, "resume.pdf")
    with open(resume_path, "w") as f:
        f.write("Mock Resume Content")

    def mock_do_POST(handler_instance):
        handler_instance.send_response(500)
        handler_instance.send_header("Content-Type", "text/html")
        handler_instance.end_headers()
        handler_instance.wfile.write(b"<html><body><h1>500 Internal Server Error</h1></body></html>")

    monkeypatch.setattr(MockHTTPRequestHandler, "do_POST", mock_do_POST)

    result = apply_to_job(
        url=f"{mock_server_url}/apply",
        candidate_info=candidate_profile,
        resume_path=resume_path
    )

    assert result["success"] is False
    assert "submission failed" in result["message"].lower() or "500" in result["message"]
