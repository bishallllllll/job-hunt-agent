"""Gmail and Google Calendar Integrations.
"""

import re
from datetime import datetime, timedelta

def poll_gmail(service=None) -> list:
    """Polls Gmail inbox (or mock email service) for messages.
    Categorizes messages into: 'Interview Invitation', 'Assessment', 'Rejection', 'Offer', 'Unknown'.
    """
    # If no service is provided, we would normally initialize the real Google API client.
    # For now, we raise an error if no service is passed (as E2E tests run in mock mode).
    if service is None:
        raise ValueError("Real Google API clients not configured. Please supply a mock service client.")
        
    messages = service.list_messages()
    parsed_emails = []
    
    for msg in messages:
        subject = msg.get("subject", "")
        body = msg.get("body", "")
        msg_id = msg.get("id", "")
        date_str = msg.get("date", "")
        
        # Categorization logic
        combined_text = (subject + " " + body).lower()
        
        category = "Unknown"
        details = {}
        
        if "interview" in combined_text or "schedule your call" in combined_text:
            category = "Interview Invitation"
            # Extract potential date/time from body
            # Simple regex search for date patterns like YYYY-MM-DD or MM/DD/YYYY
            date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', body)
            if date_match:
                details["date"] = date_match.group(0)
            else:
                details["date"] = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            
            time_match = re.search(r'\b\d{2}:\d{2}\b', body)
            if time_match:
                details["time"] = time_match.group(0)
            else:
                details["time"] = "14:00"
                
        elif "assessment" in combined_text or "test" in combined_text or "exam" in combined_text:
            category = "Assessment"
            # Extract deadline
            date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', body)
            if date_match:
                details["deadline"] = date_match.group(0)
            else:
                details["deadline"] = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                
        elif "rejection" in combined_text or "not moving forward" in combined_text or "unsuccessful" in combined_text:
            category = "Rejection"
        elif "offer" in combined_text or "pleased to offer" in combined_text:
            category = "Offer"
            
        parsed_emails.append({
            "message_id": msg_id,
            "subject": subject,
            "body": body,
            "date": date_str,
            "category": category,
            "details": details
        })
        
    return parsed_emails

def schedule_calendar_event(event_details: dict, service=None) -> dict:
    """Schedules an event on Google Calendar (or mock calendar service).
    """
    if service is None:
        raise ValueError("Real Google Calendar API client not configured. Please supply a mock service client.")
        
    # Validate event structure
    required_fields = ["summary", "start_time", "end_time"]
    for field in required_fields:
        if field not in event_details:
            return {
                "success": False,
                "event_id": None,
                "error": f"Missing required event field: {field}"
            }
            
    try:
        # Pass event to the mock/real service
        event_id = service.create_event(event_details)
        return {
            "success": True,
            "event_id": event_id
        }
    except Exception as e:
        return {
            "success": False,
            "event_id": None,
            "error": str(e)
        }
