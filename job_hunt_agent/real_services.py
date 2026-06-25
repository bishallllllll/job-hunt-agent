"""Real Gmail and Google Calendar service clients using existing OAuth credentials.

Uses the credentials stored at ~/.gmail-mcp/ which are already authenticated
with Gmail scopes for bishalsarkar999997@gmail.com.
"""

import os
import json
import time

# Paths to existing credentials
GCP_OAUTH_KEYS_PATH = os.path.expanduser("~/.gmail-mcp/gcp-oauth.keys.json")
CREDENTIALS_PATH = os.path.expanduser("~/.gmail-mcp/credentials.json")
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", "token.json")


def _get_google_credentials():
    """Load and return valid Google OAuth credentials.
    
    Uses the google-auth libraries to manage token refresh automatically.
    Falls back to raw HTTP refresh if libraries aren't available.
    """
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        raise ImportError(
            "Google auth libraries not installed. Run:\n"
            "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
        )
    
    # Load the OAuth keys for client_id/client_secret
    with open(GCP_OAUTH_KEYS_PATH, "r") as f:
        keys = json.load(f)
    
    installed = keys.get("installed", keys.get("web", {}))
    client_id = installed["client_id"]
    client_secret = installed["client_secret"]
    token_uri = installed.get("token_uri", "https://oauth2.googleapis.com/token")
    
    # Load existing credentials (access + refresh tokens)
    with open(CREDENTIALS_PATH, "r") as f:
        cred_data = json.load(f)
    
    creds = Credentials(
        token=cred_data.get("access_token"),
        refresh_token=cred_data.get("refresh_token"),
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=cred_data.get("scope", "").split(" ") if isinstance(cred_data.get("scope"), str) else cred_data.get("scope", [])
    )
    
    # Refresh if expired
    if not creds.valid:
        creds.refresh(Request())
    
    return creds


def get_real_gmail_service():
    """Build and return a real Gmail API service client."""
    from googleapiclient.discovery import build
    creds = _get_google_credentials()
    return build('gmail', 'v1', credentials=creds)


def get_real_calendar_service():
    """Build and return a real Google Calendar API service client."""
    from googleapiclient.discovery import build
    creds = _get_google_credentials()
    return build('calendar', 'v3', credentials=creds)


class RealGmailService:
    """Adapter that wraps the Google Gmail API to match the mock service interface.
    
    The mock interface expects:
      - list_messages() -> list of dicts with 'id', 'subject', 'body', 'date'
    """
    
    def __init__(self, max_results=20, query=""):
        self._service = get_real_gmail_service()
        self.max_results = max_results
        self.query = query or "is:inbox newer_than:7d"
    
    def list_messages(self) -> list:
        """Fetch recent emails and return them in the mock-compatible format."""
        import base64
        
        results = self._service.users().messages().list(
            userId='me',
            maxResults=self.max_results,
            q=self.query
        ).execute()
        
        messages = results.get('messages', [])
        parsed = []
        
        for msg_meta in messages:
            try:
                msg = self._service.users().messages().get(
                    userId='me',
                    id=msg_meta['id'],
                    format='full'
                ).execute()
                
                headers = msg.get('payload', {}).get('headers', [])
                subject = ""
                date = ""
                for h in headers:
                    if h['name'].lower() == 'subject':
                        subject = h['value']
                    elif h['name'].lower() == 'date':
                        date = h['value']
                
                # Extract body text
                body = _extract_body(msg.get('payload', {}))
                
                parsed.append({
                    "id": msg_meta['id'],
                    "subject": subject,
                    "body": body,
                    "date": date
                })
            except Exception as e:
                print(f"Warning: Could not fetch message {msg_meta['id']}: {e}")
                continue
        
        return parsed


class RealCalendarService:
    """Adapter that wraps Google Calendar API to match mock service interface.
    
    The mock interface expects:
      - create_event(event_details) -> event_id string
    """
    
    def __init__(self):
        self._service = get_real_calendar_service()
    
    def create_event(self, event_details: dict) -> str:
        """Create a real Google Calendar event."""
        event_body = {
            'summary': event_details.get('summary', 'Job Hunt Event'),
            'description': event_details.get('description', ''),
            'start': {
                'dateTime': event_details['start_time'],
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': event_details['end_time'],
                'timeZone': 'Asia/Kolkata',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 30},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        
        event = self._service.events().insert(
            calendarId='primary',
            body=event_body
        ).execute()
        
        return event.get('id', 'unknown')


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text body from Gmail message payload."""
    import base64
    
    body_text = ""
    
    if payload.get('mimeType') == 'text/plain' and payload.get('body', {}).get('data'):
        body_text = base64.urlsafe_b64decode(
            payload['body']['data']
        ).decode('utf-8', errors='replace')
    elif payload.get('parts'):
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                body_text = base64.urlsafe_b64decode(
                    part['body']['data']
                ).decode('utf-8', errors='replace')
                break
            elif part.get('parts'):
                body_text = _extract_body(part)
                if body_text:
                    break
    
    return body_text[:5000]  # Limit body size


def get_real_sheets_service():
    """Build and return a real Google Sheets API service client."""
    from googleapiclient.discovery import build
    creds = _get_google_credentials()
    return build('sheets', 'v4', credentials=creds)


class RealSheetsService:
    """Adapter that wraps the Google Sheets API to append/update job rows."""
    
    def __init__(self, spreadsheet_id=None):
        self.spreadsheet_id = spreadsheet_id or os.environ.get("SPREADSHEET_ID")
        self._service = None
        if self.spreadsheet_id:
            try:
                self._service = get_real_sheets_service()
            except Exception as e:
                print(f"Warning: Could not initialize Google Sheets service: {e}")

    def add_job(self, job: dict) -> bool:
        """Add a job row to Google Sheets."""
        from datetime import datetime
        if not self._service or not self.spreadsheet_id:
            return False
        try:
            row_data = [
                job.get("job_id", ""),
                job.get("company", ""),
                job.get("position", ""),
                job.get("source", "MockFeed"),
                job.get("location", ""),
                job.get("salary", ""),
                datetime.now().strftime("%Y-%m-%d"),
                job.get("date_applied", ""),
                job.get("status", "Found"),
                job.get("notes", "")
            ]
            body = {'values': [row_data]}
            self._service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range="Sheet1!A:J",
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            return True
        except Exception as e:
            print(f"Warning: Failed to add job to Google Sheets: {e}")
            return False

    def update_job(self, job_id: str, status: str, notes: str = None, date_applied: str = None) -> bool:
        """Update a job status, notes, or date_applied in Google Sheets."""
        if not self._service or not self.spreadsheet_id:
            return False
        try:
            # Read existing sheet values to locate the correct row
            result = self._service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range="Sheet1!A:J"
            ).execute()
            rows = result.get('values', [])
            if not rows:
                return False
            
            # Find the row index (1-based, index 0 is header row)
            row_idx = -1
            for idx, row in enumerate(rows):
                if row and row[0] == job_id:
                    row_idx = idx + 1
                    break
            
            if row_idx == -1:
                return False
            
            # Columns: A=Job ID, B=Company, C=Position, D=Source, E=Location, F=Salary, G=Date Found, H=Date Applied, I=Status, J=Notes
            # Update Status (Col I, index 8)
            self._service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"Sheet1!I{row_idx}",
                valueInputOption="USER_ENTERED",
                body={'values': [[status]]}
            ).execute()
            
            if notes is not None:
                self._service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"Sheet1!J{row_idx}",
                    valueInputOption="USER_ENTERED",
                    body={'values': [[notes]]}
                ).execute()
                
            if date_applied is not None:
                self._service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"Sheet1!H{row_idx}",
                    valueInputOption="USER_ENTERED",
                    body={'values': [[date_applied]]}
                ).execute()
                
            return True
        except Exception as e:
            print(f"Warning: Failed to update job in Google Sheets: {e}")
            return False

