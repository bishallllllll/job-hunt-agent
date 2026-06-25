"""Pytest shared fixtures.
"""

import os
import shutil
import pytest
from job_hunt_agent.mock_env import (
    MockServerThread, 
    MockGmailService, 
    MockCalendarService, 
    reset_mock_state
)

@pytest.fixture(scope="session")
def mock_server_port():
    """Starts the mock HTTP server for the E2E session.
    """
    server_thread = MockServerThread(host="localhost", port=0)
    server_thread.start()
    port = server_thread.port
    yield port
    server_thread.shutdown()

@pytest.fixture(autouse=True)
def clean_mock_state():
    """Resets mock email, calendar, and server submission states before each test.
    """
    reset_mock_state()
    yield

@pytest.fixture(autouse=True)
def mock_input(monkeypatch):
    """Automatically mock builtins.input to return 'yes' to prevent hangs during HITL prompts in tests.
    """
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    yield

@pytest.fixture
def mock_server_url(mock_server_port):
    """Returns the URL of the running mock server.
    """
    return f"http://localhost:{mock_server_port}"

@pytest.fixture
def candidate_profile() -> dict:
    """Mock candidate profile matching requirements for Bishal Sarkar.
    """
    return {
        "name": "Bishal Sarkar",
        "email": "bishal.sarkar@example.com",
        "education": "12th pass",
        "location": "Tripura",
        "skills": ["Python", "Linux", "Networking"],
        "qualifications": "Completed 12th standard. Skilled in Python automation, Linux administration, and network routing."
    }

@pytest.fixture
def mock_job_listings() -> list:
    """Returns standard job listings including high-fit, low-fit, and scams.
    """
    return [
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

@pytest.fixture
def mock_gmail_service() -> MockGmailService:
    """Provides the MockGmailService client instance.
    """
    service = MockGmailService()
    service.reset()
    return service

@pytest.fixture
def mock_calendar_service() -> MockCalendarService:
    """Provides the MockCalendarService client instance.
    """
    service = MockCalendarService()
    service.reset()
    return service

@pytest.fixture
def jobs_dir(tmp_path) -> str:
    """Initializes and cleans up the temporary /Jobs directory before and after each test.
    Using pytest's tmp_path ensures separate test runs are fully isolated.
    """
    # Create the Jobs root path in the isolated tmp_path
    jobs_path = os.path.join(tmp_path, "Jobs")
    os.makedirs(jobs_path, exist_ok=True)
    
    yield jobs_path
    
    # Teardown: Clean up the directory recursively
    if os.path.exists(jobs_path):
        shutil.rmtree(jobs_path)
