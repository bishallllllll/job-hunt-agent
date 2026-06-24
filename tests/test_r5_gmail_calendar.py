"""Tests for Feature F7: Gmail Monitor & Calendar Scheduler.
"""

import pytest
from datetime import datetime, timedelta
from job_hunt_agent.integrations import (
    poll_gmail,
    schedule_calendar_event
)

# ==========================================
# Tier 1: Feature Coverage (Happy Paths)
# ==========================================

def test_poll_gmail_interview_invitation_happy_path(mock_gmail_service):
    """Test 1: Verifies parsing and extraction of an interview invitation email.
    """
    mock_gmail_service.add_mock_email(
        msg_id="msg_001",
        subject="Interview invitation for Python role",
        body="Hi Bishal, please schedule your call on 2026-06-28 at 15:30.",
        date="2026-06-24"
    )
    
    results = poll_gmail(mock_gmail_service)
    assert len(results) == 1
    email_data = results[0]
    assert email_data["category"] == "Interview Invitation"
    assert email_data["details"]["date"] == "2026-06-28"
    assert email_data["details"]["time"] == "15:30"


def test_poll_gmail_assessment_happy_path(mock_gmail_service):
    """Test 2: Verifies parsing of a coding assessment test email.
    """
    mock_gmail_service.add_mock_email(
        msg_id="msg_002",
        subject="Coding Test Link",
        body="Complete this test by 2026-06-30.",
        date="2026-06-24"
    )
    
    results = poll_gmail(mock_gmail_service)
    assert len(results) == 1
    email_data = results[0]
    assert email_data["category"] == "Assessment"
    assert email_data["details"]["deadline"] == "2026-06-30"


def test_poll_gmail_rejection_happy_path(mock_gmail_service):
    """Test 3: Verifies parsing of a rejection email.
    """
    mock_gmail_service.add_mock_email(
        msg_id="msg_003",
        subject="Application Status update",
        body="Thank you for your interest. Unfortunately, we are not moving forward with your application.",
        date="2026-06-24"
    )
    
    results = poll_gmail(mock_gmail_service)
    assert len(results) == 1
    assert results[0]["category"] == "Rejection"


def test_poll_gmail_offer_happy_path(mock_gmail_service):
    """Test 4: Verifies parsing of a job offer email.
    """
    mock_gmail_service.add_mock_email(
        msg_id="msg_004",
        subject="Job Offer!",
        body="We are pleased to offer you the position of Junior Network Engineer.",
        date="2026-06-24"
    )
    
    results = poll_gmail(mock_gmail_service)
    assert len(results) == 1
    assert results[0]["category"] == "Offer"


def test_schedule_calendar_event_happy_path(mock_calendar_service):
    """Test 5: Schedules a calendar event with all correct parameters.
    """
    event_details = {
        "summary": "Technical Interview with TechCorp",
        "start_time": "2026-06-28T15:30:00",
        "end_time": "2026-06-28T16:30:00",
        "description": "Discuss Python and Linux skills."
    }
    
    res = schedule_calendar_event(event_details, mock_calendar_service)
    assert res["success"] is True
    assert res["event_id"] is not None
    
    events = mock_calendar_service.list_events()
    assert len(events) == 1
    assert events[0]["id"] == res["event_id"]
    assert events[0]["summary"] == event_details["summary"]


# ==========================================
# Tier 2: Boundary & Corner Cases (Unhappy Paths)
# ==========================================

def test_poll_gmail_without_service():
    """Test 6: poll_gmail raises ValueError when no service is passed.
    """
    with pytest.raises(ValueError) as excinfo:
        poll_gmail(service=None)
    assert "Real Google API clients not configured" in str(excinfo.value)


def test_schedule_calendar_event_without_service():
    """Test 7: schedule_calendar_event raises ValueError when no service is passed.
    """
    event_details = {
        "summary": "Test Interview",
        "start_time": "2026-06-28T15:30:00",
        "end_time": "2026-06-28T16:30:00"
    }
    with pytest.raises(ValueError) as excinfo:
        schedule_calendar_event(event_details, service=None)
    assert "Real Google Calendar API client not configured" in str(excinfo.value)


def test_schedule_calendar_event_missing_fields(mock_calendar_service):
    """Test 8: Gracefully returns success=False when required event fields are missing.
    """
    # Missing end_time
    event_details = {
        "summary": "Test Interview",
        "start_time": "2026-06-28T15:30:00"
    }
    res = schedule_calendar_event(event_details, mock_calendar_service)
    assert res["success"] is False
    assert "Missing required event field: end_time" in res["error"]


def test_schedule_calendar_event_invalid_date_format(mock_calendar_service):
    """Test 9: Catches ValueError from mock_calendar_service due to invalid date formats.
    """
    event_details = {
        "summary": "Interview",
        "start_time": "2026-06-28 15:30:00",  # Invalid non-ISO format
        "end_time": "2026/06/28 16:30:00"
    }
    res = schedule_calendar_event(event_details, mock_calendar_service)
    assert res["success"] is False
    assert "Invalid date-time format" in res["error"]


def test_poll_gmail_empty_inbox(mock_gmail_service):
    """Test 10: Returns empty list when inbox is empty.
    """
    results = poll_gmail(mock_gmail_service)
    assert results == []


def test_poll_gmail_fallback_dates(mock_gmail_service, mocker):
    """Test 11: Verifies parsing and extraction when email body lacks date,
    checking correct fallback date (system clock + 2 days for interview, + 3 days for assessment).
    """
    from datetime import datetime
    class MockDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 6, 24, 12, 0, 0)

    mocker.patch("job_hunt_agent.integrations.datetime", MockDateTime)

    mock_gmail_service.add_mock_email(
        msg_id="msg_fallback_01",
        subject="Interview invitation",
        body="Please schedule your call at 15:30. No date mentioned.",
        date="2026-06-24"
    )
    mock_gmail_service.add_mock_email(
        msg_id="msg_fallback_02",
        subject="Assessment link",
        body="Complete this test. No date mentioned.",
        date="2026-06-24"
    )

    results = poll_gmail(mock_gmail_service)
    assert len(results) == 2
    
    interview = [r for r in results if r["category"] == "Interview Invitation"][0]
    assert interview["details"]["date"] == "2026-06-26"  # 2026-06-24 + 2 days
    assert interview["details"]["time"] == "15:30"

    assessment = [r for r in results if r["category"] == "Assessment"][0]
    assert assessment["details"]["deadline"] == "2026-06-27"  # 2026-06-24 + 3 days
