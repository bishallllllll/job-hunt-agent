# Original User Request

## Initial Request — 2026-06-24T23:16:17+05:30

An autonomous Job Hunt Agent system designed to find, track, organize, and automatically apply to legitimate job postings matching Bishal Sarkar's profile, qualifications, and location preferences (Agartala, Tripura, India / Remote). The development team will choose the best architecture (e.g., Python CLI suite, background service, or dashboard).

Working directory: /home/monarch/teamwork_projects/job_hunt_agent
Integrity mode: development

## Requirements

### R1. Job Search, Extraction & Fit Scoring
- Search and extract remote jobs and local jobs (Tripura, India) suitable for a 12th-pass candidate with basic technical skills (Python, Linux, Networking).
- Filter out obvious scams, MLM, and paid job offers.
- Calculate a fit score (1–10) for each job based on the candidate's profile.

### R2. Resume & Cover Letter Customization
- Compare candidate profile against job descriptions.
- Generate tailored resume bullet points and customized cover letters.

### R3. Spreadsheet Tracker & Filesystem Organization
- Maintain an organized spreadsheet-based job tracker containing: Company, Position, Source, Location, Salary, Date Found, Date Applied, Status, Notes.
- Store job-related files exclusively under:
  - `/Jobs` (i.e. `/Jobs/Applications`, `/Jobs/Resumes`, `/Jobs/CoverLetters`, `/Jobs/InterviewPrep`)

### R4. Automated Application (Auto-Apply)
- Automate form filing and document upload on job portals when match fit is >= 6/10.
- Capture proof of application (confirmation screenshots, logs, or status confirmation).

### R5. Gmail & Calendar Integrations
- Monitor incoming emails for interview invitations, assessments, rejections, or offers.
- Schedule interview reminders, application deadlines, and exam dates on the calendar.

### R6. Verification System & Manual
- Implement a mock test environment (e.g., a local mock HTML form, mock email data, and mock calendar responses) to verify functionality safely.
- Write a step-by-step setup guide (`MANUAL.md`) detailing how to transition from the mock environment to real API keys and credentials.

## Acceptance Criteria

### Automated Verification
- [ ] **Scam & Fit Evaluation Test**: Programmatic test verifying that job postings are successfully classified, scams are filtered, and fit scores are calculated correctly.
- [ ] **Resume/Cover Letter Generation Test**: Programmatic test verifying that resume bullets and cover letters are generated dynamically and contain the candidate's specific background details.
- [ ] **Mock Auto-Apply Test**: Programmatic test running Playwright/Puppeteer to automatically fill a mock HTML form and verify all inputs (name, email, qualifications, resume upload) are entered correctly.
- [ ] **Data Tracker Test**: Programmatic test verifying that spreadsheet and directory file operations write data accurately to `/Jobs/` without accessing directories outside the specified paths.
- [ ] **Email & Calendar Mock Test**: Programmatic test verifying email parsing logic and mock calendar event scheduling.

### Documentation & Deliverables
- [ ] **Setup Guide**: A clear `MANUAL.md` file describing:
  1. How to run the automated test suite.
  2. How to configure real APIs (Gmail, Calendar, Google Sheets) and job portal credentials.
  3. How to perform dry-runs on live portals (filling out forms without submitting).
- [ ] **Reporting Output**: A formatted reporting script or dashboard showing the daily job report summary.
