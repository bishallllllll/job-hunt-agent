# MANUAL: Job Hunt Agent Setup and Execution Guide

This manual provides detailed instructions on setting up, running, testing, and scaling the **Job Hunt Agent** system from local mock verification to real-world deployment.

---

## 1. Setup Instructions

To get the Job Hunt Agent running on your system, follow the steps below to initialize the virtual environment, install the project dependencies, and set up the browser automation engine.

### Prerequisites
* Python 3.10 or higher installed.
* Access to a terminal with bash (or similar shell).

### Step 1: Initialize Virtual Environment
Navigate to the project root directory and create a virtual environment:
```bash
# Navigate to the project root
cd /home/monarch/teamwork_projects/job_hunt_agent/

# Create a virtual environment named .venv
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate
```

### Step 2: Install Dependencies
Upgrade pip and install the required packages for running the CLI application, handling HTTP requests, browser automation, and testing:
```bash
# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install pytest pytest-playwright pytest-mock
```
*Note: The CLI is built entirely on the Python Standard Library, meaning no additional third-party dependencies are required for basic operations, but `playwright` is required for form filling and `pytest` for the test suite.*

### Step 3: Install Playwright Browsers
Initialize the Playwright browser binaries required for GUI automation and screenshots:
```bash
# Install the Playwright Chromium browser binaries
playwright install chromium
```

---

## 2. Running the Test Suite

The Job Hunt Agent comes with a robust test suite that covers four distinct testing Tiers (from unit/happy paths to complex integration and E2E scenarios).

### How to Run All Tests
Execute `pytest` from the project root with the `PYTHONPATH` environment variable set to ensure the `job_hunt_agent` module can be resolved:
```bash
# Run the complete test suite
PYTHONPATH=. .venv/bin/pytest -v
```

### Running Specific Test Modules
If you are developing or debugging a specific feature, you can run individual test files:
```bash
# Run Search & Fit Scoring tests (F1, F2, F3)
PYTHONPATH=. .venv/bin/pytest tests/test_r1_search.py -v

# Run Customizer tests (F4)
PYTHONPATH=. .venv/bin/pytest tests/test_r2_customize.py -v

# Run Tracker tests (F5)
PYTHONPATH=. .venv/bin/pytest tests/test_r3_tracker.py -v

# Run Auto-Apply Form Filler tests (F6)
PYTHONPATH=. .venv/bin/pytest tests/test_r4_apply.py -v

# Run Email & Calendar Integration tests (F7)
PYTHONPATH=. .venv/bin/pytest tests/test_r5_gmail_calendar.py -v

# Run complete End-to-End lifecycle scenario tests (Tier 4)
PYTHONPATH=. .venv/bin/pytest tests/test_e2e.py -v
```

---

## 3. Transitioning from Mock to Real APIs

By default, the application runs in a local mock environment (using local HTML feeds, local SMTP/IMAP simulations, and mock Google Calendar handlers). To transition the agent to a live production environment, follow the configuration steps below.

### A. Configuring Google Cloud Credentials for Gmail & Google Calendar

To monitor a real Gmail inbox and schedule real Google Calendar interview events, you must set up OAuth 2.0 credentials in the Google Cloud Console.

#### Step 1: Enable APIs in Google Cloud Console
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. In the API Library, search for and enable:
   * **Gmail API**
   * **Google Calendar API**
4. Configure the OAuth Consent Screen (add `gmail.readonly` and `calendar.events` scopes, and add your email to the Test Users list).

#### Step 2: Obtain Client Secrets File
1. Navigate to **APIs & Services > Credentials**.
2. Click **Create Credentials > OAuth client ID**.
3. Choose **Desktop app** as the Application type, give it a name, and click Create.
4. Download the generated client secrets JSON file and save it as `credentials.json` in the root of the project (ensure it is ignored in `.gitignore`).

#### Step 3: Implement Authentication Token Flow
Install the required Google Auth helper libraries:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Below is the standard integration code snippet to replace mock clients with authenticated Google API service clients (e.g. in `job_hunt_agent/integrations.py`):

```python
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes required by the agent
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar'
]

def get_google_credentials():
    creds = None
    # token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_real_gmail_service():
    creds = get_google_credentials()
    return build('gmail', 'v1', credentials=creds)

def get_real_calendar_service():
    creds = get_google_credentials()
    return build('calendar', 'v3', credentials=creds)
```

In `job_hunt_agent/cli.py` or your main loop, check for credentials and pass `get_real_gmail_service()` and `get_real_calendar_service()` into `poll_gmail()` and `schedule_calendar_event()`.

---

### B. Integrating with a Real Spreadsheet Tracker

#### Using local CSV Tracker
The tracker writes by default to `/Jobs/job_tracker.csv`. You can customize the location using the `--tracker-path` CLI option:
```bash
python -m job_hunt_agent.cli track job_1 --action add --tracker-path "/path/to/my_real_tracker.csv" --jobs-dir "/path/to/my_jobs"
```

#### Transitioning to Google Sheets
To sync application records directly to a shared Google Sheet:
1. Enable the **Google Sheets API** in Google Cloud Console.
2. Add the sheet scope `https://www.googleapis.com/auth/spreadsheets` to your `SCOPES` list.
3. Replace the local CSV writer logic in `job_hunt_agent/tracker.py` with the following Google Sheets client integration:

```python
def add_job_to_google_sheet(job: dict, spreadsheet_id: str, credentials):
    service = build('sheets', 'v4', credentials=credentials)
    
    # Define row structure
    row_data = [
        job.get("job_id", ""),
        job.get("company", ""),
        job.get("position", ""),
        job.get("source", ""),
        job.get("location", ""),
        job.get("salary", ""),
        datetime.now().strftime("%Y-%m-%d"),
        job.get("date_applied", ""),
        job.get("status", "Found"),
        job.get("notes", "")
    ]
    
    body = {
        'values': [row_data]
    }
    
    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="Sheet1!A:J",
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    
    return result
```

---

### C. Setting up Credentials & Targets for Real Job Portals

To search and extract job listings from live portals (Indeed, LinkedIn, ZipRecruiter):
1. **Disable Mock Search**: In `job_hunt_agent/search.py`, locate the `SETTINGS` block and set `"USE_MOCK"` to `False`:
   ```python
   SETTINGS = {
       "USE_MOCK": False
   }
   ```
2. **Implement Scraper Parsers**: Implement the `scrape` method of `PlaywrightScraper` in `job_hunt_agent/search.py`. This class should navigate to the target portal's search page, input search keywords and locations, and parse search results using CSS/XPath selectors.
3. **Authentication**: If target job boards require user authentication:
   * Program Playwright to navigate to the login page first.
   * Enter credentials securely via environment variables (do not hardcode them!):
     ```python
     username = os.environ.get("JOB_BOARD_USER")
     password = os.environ.get("JOB_BOARD_PASSWORD")
     page.fill('input[type="email"]', username)
     page.fill('input[type="password"]', password)
     page.click('button[type="submit"]')
     ```
   * Save session cookies/storage state locally after authenticating to avoid repeatedly logging in and getting flagged by bot-detection software.

---

## 4. Performing Dry-Runs on Live Job Portals

Before executing auto-apply campaigns on live job boards, it is highly recommended to perform **dry-runs**. A dry-run uses Playwright to navigate to the application page, fills in all fields, uploads the resume file, takes a screenshot of the filled form for validation, and closes the browser **without clicking the submit button**.

### Implementing Dry-Run Mode in Code
Add a `dry_run` parameter to the form filling logic in `job_hunt_agent/apply.py`:

```python
def apply_to_job(url: str, candidate_info: dict, resume_path: str, screenshot_path: str = None, dry_run: bool = False) -> dict:
    # ... [Playwright Setup & Navigation] ...
    
    # Fill out the form fields
    page.fill('input[name="name"]', candidate_info.get("name", ""))
    page.fill('input[name="email"]', candidate_info.get("email", ""))
    page.fill('textarea[name="qualifications"]', candidate_info.get("qualifications", ""))
    
    # File upload
    page.set_input_files('input[type="file"]', resume_path)
    
    # Dry-Run Check
    if dry_run:
        # Save screenshot verification of the populated form
        if screenshot_path:
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            page.screenshot(path=screenshot_path)
            
        browser.close()
        return {
            "success": True,
            "message": "[DRY-RUN] Form filled successfully. Submission skipped.",
            "screenshot": screenshot_path
        }
        
    # Real submission
    submit_btn = page.locator('button[type="submit"]')
    submit_btn.click()
    # ...
```

### Running Dry-Run via the CLI
To perform a dry-run from the command line, expose the `--dry-run` flag in the CLI parser:
1. In `job_hunt_agent/cli.py`, add the flag to the `apply` subcommand:
   ```python
   apply_parser.add_argument("--dry-run", action="store_true", help="Fill forms and screenshot without submitting")
   ```
2. Execute the dry-run command:
   ```bash
   # Run form fill dry-run and save the screenshot for confirmation
   python -m job_hunt_agent.cli apply job_1 \
     --url "https://real-job-board-url.com/apply" \
     --resume-path "/home/monarch/teamwork_projects/job_hunt_agent/Jobs/Resumes/job_1_resume.txt" \
     --screenshot-path "/home/monarch/teamwork_projects/job_hunt_agent/Jobs/Screenshots/job_1_dryrun.png" \
     --dry-run
   ```
3. Open the captured screenshot (under `Jobs/Screenshots/job_1_dryrun.png`) to verify that the form fields are filled correctly and the resume file is uploaded.
