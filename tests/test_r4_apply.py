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


def test_apply_remedy_semantic_matching(mock_server_url, candidate_profile, tmp_path):
    """Test semantic matching improvements:
    - No name collisions on emergency, contact, referrer, relative.
    - Experience numeric/short inputs fill with small number or ignore.
    - Required or agreement checkboxes/radios checked.
    """
    resume_path = os.path.join(tmp_path, "resume.pdf")
    with open(resume_path, "w") as f:
        f.write("Mock Resume Content")

    result = apply_to_job(
        url=f"{mock_server_url}/apply_remedy",
        candidate_info=candidate_profile,
        resume_path=resume_path
    )

    assert result["success"] is True
    assert len(submitted_applications) >= 1
    
    app = submitted_applications[-1]
    assert app.get("is_remedy") is True
    
    # 1. Name collisions prevented
    assert app.get("emergency_contact") == ""
    assert app.get("referrer_name") == ""
    assert app.get("rel_name") == ""
    
    # 2. Experience numeric/short input handling
    assert app.get("experience_num") == "2"
    assert app.get("exp_years") == "2"
    assert app.get("experience_short") == ""
    
    # 3. Required/agreement checkboxes and radios
    assert app.get("agree_req") == "on"
    assert app.get("agree_terms") == "on"
    assert app.get("consent_req") == "yes"


# ==========================================
# SeleniumBase UC Mode (Live Mode) tests
# ==========================================

from unittest.mock import patch, MagicMock

class MockElementLive:
    def __init__(self, tag_name, name_attr, type_attr, label_text=""):
        self.tag_name = tag_name
        self._name = name_attr
        self._type = type_attr
        self._label_text = label_text
        self._selected = False
        self.keys_sent = []

    def get_attribute(self, attr):
        if attr == "name":
            return self._name
        if attr == "type":
            return self._type
        if attr == "id":
            return self._name + "_id"
        return ""

    def send_keys(self, keys):
        self.keys_sent.append(keys)

    def click(self):
        self._selected = True

    def clear(self):
        pass

    def is_selected(self):
        return self._selected

    @property
    def text(self):
        return "yes" if "yes" in self._label_text else "no"

    def find_elements(self, by, selector):
        if selector == "option":
            return [
                MockElementLive("option", "yes_opt", "option", "yes"),
                MockElementLive("option", "no_opt", "option", "no")
            ]
        return []


class MockDriverLive:
    def __init__(self):
        self.elements = [
            MockElementLive("input", "email", "email"),
            MockElementLive("input", "name", "text"),
            MockElementLive("input", "phone", "text"),
            MockElementLive("input", "resume", "file"),
            MockElementLive("textarea", "qualifications", "textarea"),
            MockElementLive("input", "agree", "checkbox", "agree terms"),
            MockElementLive("select", "authorized", "select", "are you authorized to work")
        ]

    def find_elements(self, by, selector):
        return self.elements

    def find_element(self, by, selector):
        return MockElementLive("button", "submit", "submit")


class MockSBLive:
    def __init__(self, uc=True, headless=True):
        self.driver = MockDriverLive()
        self.opened_urls = []
        self.screenshot_saved = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def set_window_size(self, w, h):
        pass

    def open(self, url):
        self.opened_urls.append(url)

    def save_screenshot(self, path):
        self.screenshot_saved = path
        with open(path, "w") as f:
            f.write("mock screenshot")

    def is_element_visible(self, selector):
        return True

    def get_page_source(self):
        return "<html><body><h1>success</h1></body></html>"

    def execute_script(self, script, *args):
        if "getBoundingClientRect" in script:
            return {"x": 100, "y": 200, "left": 50, "top": 150, "width": 100, "height": 100}
        return ""


def test_apply_live_mode_uc(tmp_path, candidate_profile):
    """Test SeleniumBase UC flow when SETTINGS['USE_MOCK'] = False.
    """
    from job_hunt_agent.search import SETTINGS
    original_val = SETTINGS.get("USE_MOCK", True)
    resume_path = os.path.join(tmp_path, "resume.pdf")
    with open(resume_path, "w") as f:
        f.write("Mock Resume Content")

    screenshot_path = os.path.join(tmp_path, "screenshots", "sb_apply_success.png")

    try:
        SETTINGS["USE_MOCK"] = False
        with patch("seleniumbase.SB", new=MockSBLive):
            result = apply_to_job(
                url="https://example.com/apply",
                candidate_info=candidate_profile,
                resume_path=resume_path,
                screenshot_path=screenshot_path
            )
            assert result["success"] is True
            assert "submitted successfully" in result["message"]
            assert result["screenshot"] == screenshot_path
            assert os.path.exists(screenshot_path)
    finally:
        SETTINGS["USE_MOCK"] = original_val

