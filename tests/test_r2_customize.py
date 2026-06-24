"""Tests for Resume & Cover Letter Tailoring (Feature F4)
"""

import pytest
from job_hunt_agent.customizer import customize_for_job

# --- Tier 1: Happy-Path Test Cases (Feature Coverage) ---

def test_customize_happy_path_all_skills(candidate_profile):
    """F4 Tier 1: Valid input matching all candidate skills (Python, Linux, Networking).
    """
    job = {
        "job_id": "job_happy_all",
        "company": "Tech Solutions",
        "position": "System & Automation Engineer",
        "description": "We need someone to write Python scripts, manage Linux servers, and configure network routers."
    }
    result = customize_for_job(job, candidate_profile)
    
    assert "resume_bullets" in result
    assert "cover_letter" in result
    
    bullets = result["resume_bullets"]
    assert len(bullets) == 3
    # Verify exact bullet contents matching customizer logic
    assert any("Python automation scripts" in b for b in bullets)
    assert any("Linux server environments" in b for b in bullets)
    assert any("network switch and router configurations" in b for b in bullets)
    
    cl = result["cover_letter"]
    assert "Dear Hiring Manager," in cl
    assert "System & Automation Engineer" in cl
    assert "Tech Solutions" in cl
    assert "Bishal Sarkar" in cl
    assert "Python, Linux, Networking" in cl


def test_customize_happy_path_python_only(candidate_profile):
    """F4 Tier 1: Valid input matching Python only (via 'automation' keyword).
    """
    job = {
        "job_id": "job_happy_py",
        "company": "AutoCorp",
        "position": "Automation Developer",
        "description": "Looking for an engineer to help with task automation and coder tasks."
    }
    result = customize_for_job(job, candidate_profile)
    bullets = result["resume_bullets"]
    
    assert len(bullets) == 1
    assert "Python automation scripts" in bullets[0]
    
    cl = result["cover_letter"]
    assert "Automation Developer" in cl
    assert "AutoCorp" in cl


def test_customize_happy_path_linux_only(candidate_profile):
    """F4 Tier 1: Valid input matching Linux only (via 'unix' keyword).
    """
    job = {
        "job_id": "job_happy_linux",
        "company": "OS Foundation",
        "position": "Unix Administrator",
        "description": "Seeking helper to maintain unix machines and general systems."
    }
    result = customize_for_job(job, candidate_profile)
    bullets = result["resume_bullets"]
    
    assert len(bullets) == 1
    assert "Linux server environments" in bullets[0]


def test_customize_happy_path_network_only(candidate_profile):
    """F4 Tier 1: Valid input matching Networking only (via 'cisco' keyword).
    """
    job = {
        "job_id": "job_happy_net",
        "company": "Cisco Partners",
        "position": "Network Support Associate",
        "description": "Requires basic understanding of cisco configs and ip networks."
    }
    result = customize_for_job(job, candidate_profile)
    bullets = result["resume_bullets"]
    
    assert len(bullets) == 1
    assert "network switch and router configurations" in bullets[0]


def test_customize_happy_path_no_technical_matches_default(candidate_profile):
    """F4 Tier 1: Valid input matching none of the technical keywords. Fallback to default bullets.
    """
    job = {
        "job_id": "job_happy_default",
        "company": "Generic Office",
        "position": "General IT Assistant",
        "description": "We need help with office computers and general troubleshooting. Basic IT knowledge."
    }
    result = customize_for_job(job, candidate_profile)
    bullets = result["resume_bullets"]
    
    assert len(bullets) == 2
    assert "Applied core Python and Linux knowledge" in bullets[0]
    assert "Supported local IT hardware" in bullets[1]


def test_customize_happy_path_alternate_profile():
    """F4 Tier 1: Valid input with custom candidate profile name and skills.
    """
    job = {
        "job_id": "job_custom_profile",
        "company": "Dev Solutions",
        "position": "Software Engineer",
        "description": "Looking for a python developer."
    }
    custom_profile = {
        "name": "Arjun Kumar",
        "skills": ["Python", "Scripting"]
    }
    result = customize_for_job(job, custom_profile)
    bullets = result["resume_bullets"]
    cl = result["cover_letter"]
    
    assert len(bullets) == 1
    assert "Arjun Kumar" in cl
    assert "Python, Scripting" in cl


# --- Tier 2: Boundary & Corner Cases (Unhappy Paths) ---

def test_customize_empty_job_and_profile():
    """F4 Tier 2: Check robust handling of missing fields or empty dict inputs.
    """
    # Empty job and empty profile dicts
    job = {}
    profile = {}
    result = customize_for_job(job, profile)
    
    assert "resume_bullets" in result
    assert "cover_letter" in result
    
    bullets = result["resume_bullets"]
    # Should get defaults
    assert len(bullets) == 2
    assert "Applied core Python and Linux knowledge" in bullets[0]
    
    cl = result["cover_letter"]
    # Check default fallbacks in customizer
    assert "Bishal Sarkar" in cl
    assert "Python, Linux, Networking" in cl
    assert "at ." in cl  # position/company default to empty strings


def test_customize_very_long_inputs(candidate_profile):
    """F4 Tier 2: Test very long input strings to ensure performance/correct interpolation.
    """
    long_desc = "python " * 5000 + "linux " * 5000
    job = {
        "job_id": "job_long",
        "company": "A" * 1000,
        "position": "B" * 1000,
        "description": long_desc
    }
    
    result = customize_for_job(job, candidate_profile)
    assert len(result["resume_bullets"]) == 2
    assert "A" * 1000 in result["cover_letter"]
    assert "B" * 1000 in result["cover_letter"]


def test_customize_special_characters(candidate_profile):
    """F4 Tier 2: Check company and position with special/weird characters.
    """
    job = {
        "job_id": "job_special",
        "company": "Tech-Corp & Co. / <Systems!>",
        "position": "Junior developer (100% remote) #1",
        "description": "Looking for Python scripting experts."
    }
    result = customize_for_job(job, candidate_profile)
    cl = result["cover_letter"]
    
    assert "Tech-Corp & Co. / <Systems!>" in cl
    assert "Junior developer (100% remote) #1" in cl


def test_customize_empty_job_description(candidate_profile):
    """F4 Tier 2: Empty description should fall back to default bullets cleanly.
    """
    job = {
        "job_id": "job_empty_desc",
        "company": "Innovate",
        "position": "Developer",
        "description": ""
    }
    result = customize_for_job(job, candidate_profile)
    bullets = result["resume_bullets"]
    
    assert len(bullets) == 2
    assert "Applied core Python and Linux knowledge" in bullets[0]


def test_customize_no_matching_qualifications(candidate_profile):
    """F4 Tier 2: Job description contains other technical keywords but no matches for Bishal.
    """
    job = {
        "job_id": "job_no_match",
        "company": "JavaShop",
        "position": "Java Architect",
        "description": "Seeking Java, Spring Boot, AWS, Kubernetes, and Docker specialists."
    }
    result = customize_for_job(job, candidate_profile)
    bullets = result["resume_bullets"]
    
    # Should get defaults
    assert len(bullets) == 2
    assert "Applied core Python and Linux knowledge" in bullets[0]


def test_customize_case_insensitivity(candidate_profile):
    """F4 Tier 2: Ensure keyword matching is case-insensitive (e.g. PyThOn, LINUX, NETwork).
    """
    job = {
        "job_id": "job_case",
        "company": "Case Corp",
        "position": "Engineer",
        "description": "Must know PyThOn scripting, LINUX server configs, and NETwork routing."
    }
    result = customize_for_job(job, candidate_profile)
    bullets = result["resume_bullets"]
    
    assert len(bullets) == 3


def test_customize_invalid_skills_type():
    """F4 Tier 2: Handle malformed skills argument in profile.
    If skills is None, the join call in customizer will raise TypeError.
    This test asserts the expected Python error is raised, documenting boundary limits.
    """
    job = {
        "job_id": "job_err",
        "company": "Err",
        "position": "Developer",
        "description": "Python"
    }
    bad_profile = {
        "name": "Bishal",
        "skills": None
    }
    with pytest.raises(TypeError):
        customize_for_job(job, bad_profile)
