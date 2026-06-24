"""Local Mock Environment Services and Servers.
"""

import re
import email
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Global in-memory storage for mock services
submitted_applications = []
mock_emails = []
mock_calendar_events = []

class MockHTTPRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence default logging output in tests
        pass

    def do_GET(self):
        if self.path == "/apply":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            html = """<html>
<head><title>Job Application Form</title></head>
<body>
    <h1>Apply for Job</h1>
    <form action="/submit" method="POST" enctype="multipart/form-data">
        Name: <input type="text" name="name"><br>
        Email: <input type="email" name="email"><br>
        Qualifications: <textarea name="qualifications"></textarea><br>
        Resume: <input type="file" name="resume"><br>
        <button type="submit">Submit</button>
    </form>
</body>
</html>"""
            self.wfile.write(html.encode("utf-8"))
            
        elif self.path == "/feed":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            # Standard HTML mock feed containing normal jobs and scam jobs
            html = """<html>
<head><title>Job Listings Feed</title></head>
<body>
    <div class="job-listing" id="job_001">
        <span class="company">TechCorp</span>
        <span class="position">Python Developer</span>
        <span class="location">Remote</span>
        <span class="salary">$60,000</span>
        <p class="description">Looking for a junior Python Developer with Linux automation skills. 12th pass okay.</p>
    </div>
    <div class="job-listing" id="job_002">
        <span class="company">MLM Ventures</span>
        <span class="position">Marketing Executive</span>
        <span class="location">Tripura</span>
        <span class="salary">$20,000</span>
        <p class="description">Earn money fast by joining our multi-level marketing network! Upfront payment required.</p>
    </div>
    <div class="job-listing" id="job_003">
        <span class="company">NetSystems</span>
        <span class="position">Network Associate</span>
        <span class="location">Tripura</span>
        <span class="salary">$30,000</span>
        <p class="description">Need a support technician to manage Linux systems and network routers.</p>
    </div>
</body>
</html>"""
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/submit":
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))
            
            body = self.rfile.read(content_length)
            
            # Parse multipart/form-data using standard email package
            msg_bytes = f"Content-Type: {content_type}\r\n\r\n".encode("utf-8") + body
            msg = email.message_from_bytes(msg_bytes)
            
            form_fields = {}
            files = {}
            
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue
                
                disposition = part.get("content-disposition", "")
                name_match = re.search(r'name="([^"]+)"', disposition)
                if name_match:
                    field_name = name_match.group(1)
                    filename_match = re.search(r'filename="([^"]+)"', disposition)
                    
                    payload = part.get_payload(decode=True)
                    if filename_match:
                        files[field_name] = {
                            "filename": filename_match.group(1),
                            "content": payload
                        }
                    else:
                        form_fields[field_name] = payload.decode("utf-8").strip()
            
            # Validation logic
            name = form_fields.get("name", "")
            email_val = form_fields.get("email", "")
            qualifications = form_fields.get("qualifications", "")
            resume = files.get("resume")
            
            errors = []
            if not name:
                errors.append("Name is required")
            if not email_val or "@" not in email_val:
                errors.append("Valid email is required")
            if not qualifications:
                errors.append("Qualifications are required")
            if not resume or not resume["content"]:
                errors.append("Non-empty resume file upload is required")
                
            if errors:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                err_html = f"<html><body><h1>Error</h1><p>{'; '.join(errors)}</p></body></html>"
                self.wfile.write(err_html.encode("utf-8"))
            else:
                # Store application in memory
                app_data = {
                    "name": name,
                    "email": email_val,
                    "qualifications": qualifications,
                    "resume_name": resume["filename"],
                    "resume_size": len(resume["content"])
                }
                submitted_applications.append(app_data)
                
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                success_html = "<html><body><h1>Success</h1><p>Application submitted!</p></body></html>"
                self.wfile.write(success_html.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

class MockGmailService:
    """Mock Gmail IMAP Service.
    """
    def list_messages(self) -> list:
        return mock_emails

    def add_mock_email(self, msg_id: str, subject: str, body: str, date: str) -> None:
        mock_emails.append({
            "id": msg_id,
            "subject": subject,
            "body": body,
            "date": date
        })

    def reset(self) -> None:
        mock_emails.clear()

class MockCalendarService:
    """Mock Google Calendar API Service.
    """
    def __init__(self):
        self.counter = 0

    def create_event(self, event_details: dict) -> str:
        # Validate event payload structures
        summary = event_details.get("summary", "")
        start_time = event_details.get("start_time", "")
        end_time = event_details.get("end_time", "")
        
        if not summary:
            raise ValueError("Event summary cannot be empty.")
        if not start_time or not end_time:
            raise ValueError("Event must have start_time and end_time.")
            
        # Basic validation for ISO date formats (e.g., 2026-06-26T14:00:00)
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        if not re.match(iso_pattern, start_time) or not re.match(iso_pattern, end_time):
            raise ValueError(f"Invalid date-time format. Start: {start_time}, End: {end_time}. Must be ISO format.")
            
        self.counter += 1
        event_id = f"evt_{self.counter}"
        
        mock_calendar_events.append({
            "id": event_id,
            "summary": summary,
            "start_time": start_time,
            "end_time": end_time,
            "description": event_details.get("description", "")
        })
        return event_id

    def list_events(self) -> list:
        return mock_calendar_events

    def reset(self) -> None:
        mock_calendar_events.clear()
        self.counter = 0

def reset_mock_state() -> None:
    """Clears all in-memory mock states.
    """
    submitted_applications.clear()
    mock_emails.clear()
    mock_calendar_events.clear()

# Thread-safe server control
class MockServerThread(threading.Thread):
    def __init__(self, host="localhost", port=0):
        super().__init__()
        self.server = HTTPServer((host, port), MockHTTPRequestHandler)
        self.port = self.server.server_port
        self.daemon = True

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()
