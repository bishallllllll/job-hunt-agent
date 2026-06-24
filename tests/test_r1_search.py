import pytest
from job_hunt_agent.search import (
    is_scam,
    calculate_fit_score,
    search_jobs,
    BISHAL_PROFILE,
    MockScraper
)

# --- Unit Tests for is_scam ---

def test_is_scam_payment_requests():
    # Job requires a refundable deposit
    job = {
        "position": "Data Entry Typist",
        "company": "Valid Corp",
        "location": "Remote",
        "description": "Please pay a refundable registration fee of 500 INR to start.",
        "salary": "25000 per month",
        "source": "Indeed"
    }
    assert is_scam(job) is True

    # Job requires buying training kit
    job["description"] = "You must buy the training kit for 2000 INR upfront."
    assert is_scam(job) is True


def test_is_scam_mlm_schemes():
    # MLM keywords
    job = {
        "position": "Business Partner",
        "company": "Growth Network",
        "location": "Agartala",
        "description": "Build your network! Recruit friends and family to join your downline. residual income.",
        "salary": "Commission only",
        "source": "Indeed"
    }
    assert is_scam(job) is True

    # MLM regex trigger
    job["description"] = "Join our multi-level marketing program today."
    assert is_scam(job) is True


def test_is_scam_suspicious_salaries():
    # Unrealistic salary for data entry/typing role (>1,00,000 per month)
    job = {
        "position": "Part-time Copy Paste Operator",
        "company": "Valid Corp",
        "location": "Remote",
        "description": "Copy paste work from home.",
        "salary": "₹1,50,000 per month",
        "source": "LinkedIn"
    }
    assert is_scam(job) is True

    # Daily rate exceeding 5,000 INR for basic task
    job = {
        "position": "Data Entry Operator",
        "company": "Valid Corp",
        "location": "Remote",
        "description": "Earn up to ₹5,500 per day doing simple typing tasks.",
        "salary": "₹20,000 per week",
        "source": "Indeed"
    }
    assert is_scam(job) is True


def test_is_scam_vague_or_missing_details():
    # Short description
    job = {
        "position": "Python Developer",
        "company": "Valid Corp",
        "location": "Remote",
        "description": "Short desc under 120 chars.",
        "salary": "₹5,00,000 per annum",
        "source": "LinkedIn"
    }
    assert is_scam(job) is True

    # Vague company
    job["description"] = "Valid description containing more than 120 characters to pass the short description check. We need a developer who can write clean code."
    job["company"] = "Private Employer"
    assert is_scam(job) is True

    # Free email + generic title
    job["company"] = "Valid Corp"
    job["position"] = "Data Entry Clerk"
    job["description"] = "Valid description containing more than 120 characters to pass the short description check. Send resume to jobs@gmail.com for details."
    assert is_scam(job) is True


def test_is_scam_typical_scam_titles():
    job = {
        "position": "Part-Time Typing Job",
        "company": "Valid Corp",
        "location": "Remote",
        "description": "Valid description containing more than 120 characters to pass the short description check. No registration fees.",
        "salary": "₹15,000 per month",
        "source": "Indeed"
    }
    assert is_scam(job) is True


def test_is_scam_legitimate():
    # Legit job
    job = {
        "position": "Junior Python Developer",
        "company": "TechSolutions India",
        "location": "Remote",
        "description": "Looking for a junior developer to write Python scripts for automating Linux server administration. Basic understanding of TCP/IP networking, routing, and DNS is a plus. Perfect for freshers or high school graduates with strong programming logic.",
        "salary": "₹4,00,000 per annum",
        "source": "LinkedIn"
    }
    assert is_scam(job) is False


# --- Unit Tests for calculate_fit_score ---

def test_calculate_fit_score_range():
    # Asserts that the fit score falls within 1 and 10
    job = {
        "position": "Python Linux Networking Engineer",
        "location": "Remote",
        "description": "Seeking Python Linux Networking Engineer. Freshers welcome. No degree required."
    }
    score = calculate_fit_score(job, BISHAL_PROFILE)
    assert 1 <= score <= 10


def test_calculate_fit_score_high_fit_remote_and_local():
    # Job 1 (Remote High Fit)
    job_1 = {
        "position": "Junior Python Scripting Developer",
        "location": "Remote",
        "description": "Looking for a junior developer to write Python scripts for automating Linux server administration. Basic understanding of TCP/IP networking, routing, and DNS is a plus. Perfect for freshers or high school graduates with strong programming logic."
    }
    assert calculate_fit_score(job_1, BISHAL_PROFILE) == 10

    # Job 2 (Local High Fit)
    job_2 = {
        "position": "Network Assistant & IT Support",
        "location": "Agartala, Tripura",
        "description": "Local telecom services company seeking an IT support assistant. Responsibilities include configuring Linux routers and switches, diagnosing network connectivity issues, and executing basic Python troubleshooting scripts. Candidates who have passed 12th standard with certification in CCNA are encouraged to apply."
    }
    assert calculate_fit_score(job_2, BISHAL_PROFILE) == 10


def test_calculate_fit_score_medium_fit():
    # Job 3 (Medium Fit, Skill Discrepancy)
    job_3 = {
        "position": "Linux System Administrator Trainee",
        "location": "Remote",
        "description": "Entry level position for managing Debian and Ubuntu systems. Must be proficient with command-line interfaces and bash scripting. Python knowledge is preferred but not required. High school graduates with relevant self-taught skills are welcome."
    }
    assert calculate_fit_score(job_3, BISHAL_PROFILE) == 7


def test_calculate_fit_score_strict_location_capping():
    # Job 4 (Strictly on-site Bangalore)
    job_4 = {
        "position": "Python Software Engineer",
        "location": "Bangalore, Karnataka",
        "description": "Seeking a Python Software Engineer to build web applications using Django and React. Must have a Bachelor's degree in Computer Science. This is a strictly on-site role in Bangalore."
    }
    # Expected fit should be capped to 1 because location is non-preferred and strictly onsite
    assert calculate_fit_score(job_4, BISHAL_PROFILE) == 1


def test_calculate_fit_score_senior_architect():
    # Job 8 (Senior Network Architect)
    job_8 = {
        "position": "Senior Network Architect",
        "location": "Remote",
        "description": "Designing large scale enterprise networks. Must have a Master's degree in Telecommunications or Computer Science. Minimum 10 years of experience. Python automation and advanced Linux administration required. Must understand enterprise Kubernetes deployments."
    }
    # Should get capped at 4/10 due to Senior/Architect/10 years experience keywords
    assert calculate_fit_score(job_8, BISHAL_PROFILE) == 4


# --- Integration Tests for search_jobs ---

def test_search_jobs_filtering_and_scoring():
    # By default, search_jobs should filter out scams
    jobs = search_jobs(query="", location="")
    # Check that all returned jobs are not scams
    for job in jobs:
        assert job["is_scam"] is False
        assert "fit_score" in job

    # Count total jobs returned (should exclude job_5, job_6, job_7)
    assert len(jobs) == 5

    # Check that query matches filter correctly
    python_jobs = search_jobs(query="python", location="")
    for job in python_jobs:
        assert "python" in job["position"].lower() or "python" in job["description"].lower()

    # Check location filtering
    agartala_jobs = search_jobs(query="", location="Agartala")
    for job in agartala_jobs:
        assert "agartala" in job["location"].lower()


def test_search_jobs_include_scams():
    # When include_scams is True, all 8 mock jobs should be returned
    jobs = search_jobs(query="", location="", include_scams=True)
    assert len(jobs) == 8
    scam_ids = [j["job_id"] for j in jobs if j["is_scam"]]
    assert "job_5" in scam_ids
    assert "job_6" in scam_ids
    assert "job_7" in scam_ids
