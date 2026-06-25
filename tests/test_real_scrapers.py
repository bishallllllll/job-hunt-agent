import os
import json
import pytest
from unittest.mock import patch, MagicMock
from job_hunt_agent.search import PlaywrightScraper

# HTML templates for mocking target portal search results
LINKEDIN_HTML = """
<div class="base-card">
  <h3 class="base-search-card__title">Software Engineer</h3>
  <h4 class="base-search-card__subtitle">Tech Co</h4>
  <span class="job-search-card__location">Agartala, Tripura</span>
  <span class="job-search-card__salary-info">₹5,00,000 per annum</span>
  <a href="https://www.linkedin.com/jobs/view/12345">View Job</a>
</div>
"""

INDEED_HTML = """
<div class="job_seen_beacon">
  <h2 class="jobTitle"><a class="jcs-JobTitle" href="/rc/clk?jk=indeed123">Python Developer</a></h2>
  <span class="companyName">Indeed Co</span>
  <div class="companyLocation">Remote</div>
  <div class="job-snippet">Write awesome Python scripts.</div>
  <div class="salary-snippet-container">₹6,00,000 per annum</div>
</div>
"""

NAUKRI_HTML = """
<article class="jobTuple" data-jobid="naukri123">
  <a class="title" href="https://www.naukri.com/job-naukri123">Network Engineer</a>
  <a class="subTitle">Naukri Co</a>
  <span class="loc-wrap">Tripura, India</span>
  <span class="sal-wrap">Not Disclosed</span>
  <span class="job-desc">Manage routers and switches.</span>
</article>
"""

class MockSB:
    def __init__(self, uc=True, headless=True):
        self.uc = uc
        self.headless = headless
        self.opened_urls = []
        self.set_size = None
        self.cookies = [{"name": "mock_cookie", "value": "123"}]
        self.keys_sent = []
        self.clicked = []
        self.scripts_executed = []
        self.source = ""
        self.cleared = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def set_window_size(self, w, h):
        self.set_size = (w, h)

    def open(self, url):
        self.opened_urls.append(url)
        # Simulate loading page content based on target URL
        if "linkedin.com/jobs" in url:
            self.source = LINKEDIN_HTML
        elif "indeed.com/jobs" in url:
            self.source = INDEED_HTML
        elif "naukri.com/search" in url:
            self.source = NAUKRI_HTML
        else:
            self.source = "<html>Base Domain</html>"

    def get_cookies(self):
        return self.cookies

    def add_cookie(self, cookie):
        self.cookies.append(cookie)

    def click(self, selector):
        self.clicked.append(selector)

    def send_keys(self, selector, text):
        self.keys_sent.append((selector, text))

    def execute_script(self, script):
        self.scripts_executed.append(script)

    def get_page_source(self):
        return self.source

    def clear(self, selector):
        self.cleared.append(selector)


@pytest.fixture(autouse=True)
def mock_sleep(monkeypatch):
    """Automatically mock time.sleep to run scraper tests instantly."""
    monkeypatch.setattr("time.sleep", lambda _: None)
    yield


@patch("seleniumbase.SB", new=MockSB)
def test_unauthenticated_scraping(monkeypatch):
    # Ensure environment variables for credentials do not exist
    monkeypatch.delenv("LINKEDIN_USER", raising=False)
    monkeypatch.delenv("INDEED_USER", raising=False)
    monkeypatch.delenv("NAUKRI_USER", raising=False)

    scraper = PlaywrightScraper()
    jobs = scraper.scrape("python", "Agartala")

    # Verify that jobs were parsed correctly from each portal
    assert len(jobs) == 3

    li_job = next(j for j in jobs if j["source"] == "LinkedIn")
    assert li_job["company"] == "Tech Co"
    assert li_job["position"] == "Software Engineer"
    assert li_job["location"] == "Agartala, Tripura"
    assert li_job["salary"] == "₹5,00,000 per annum"
    assert li_job["job_id"] == "li_12345"

    in_job = next(j for j in jobs if j["source"] == "Indeed")
    assert in_job["company"] == "Indeed Co"
    assert in_job["position"] == "Python Developer"
    assert in_job["location"] == "Remote"
    assert in_job["salary"] == "₹6,00,000 per annum"
    assert in_job["job_id"] == "in_indeed123"

    nk_job = next(j for j in jobs if j["source"] == "Naukri")
    assert nk_job["company"] == "Naukri Co"
    assert nk_job["position"] == "Network Engineer"
    assert nk_job["location"] == "Tripura, India"
    assert nk_job["salary"] == "Not Disclosed"
    assert nk_job["job_id"] == "nk_naukri123"


@patch("seleniumbase.SB", new=MockSB)
def test_authenticated_scraping_saves_cookies(monkeypatch):
    # Mock credentials env vars
    monkeypatch.setenv("LINKEDIN_USER", "test_user")
    monkeypatch.setenv("LINKEDIN_PASS", "test_pass")

    session_file = "/home/monarch/teamwork_projects/job_hunt_agent/.session_state/linkedin_session.json"
    if os.path.exists(session_file):
        os.remove(session_file)

    try:
        scraper = PlaywrightScraper()
        jobs = scraper.scrape_portal("linkedin", "python", "Agartala")

        assert len(jobs) == 1
        # Cookie file should be saved successfully after authentication
        assert os.path.exists(session_file)
        with open(session_file, "r") as f:
            saved_cookies = json.load(f)
        assert len(saved_cookies) > 0
        assert saved_cookies[0]["name"] == "mock_cookie"
    finally:
        if os.path.exists(session_file):
            os.remove(session_file)


@patch("seleniumbase.SB", new=MockSB)
def test_authenticated_scraping_loads_cookies(monkeypatch):
    monkeypatch.setenv("LINKEDIN_USER", "test_user")
    monkeypatch.setenv("LINKEDIN_PASS", "test_pass")

    session_file = "/home/monarch/teamwork_projects/job_hunt_agent/.session_state/linkedin_session.json"
    os.makedirs(os.path.dirname(session_file), exist_ok=True)
    
    mock_cookie_data = [{"name": "session_id", "value": "abc-xyz-999"}]
    with open(session_file, "w") as f:
        json.dump(mock_cookie_data, f)

    try:
        scraper = PlaywrightScraper()
        jobs = scraper.scrape_portal("linkedin", "python", "Agartala")
        assert len(jobs) == 1
    finally:
        if os.path.exists(session_file):
            os.remove(session_file)
