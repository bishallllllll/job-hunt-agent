# Project: Job Hunt Agent

## Architecture
The Job Hunt Agent system is designed as a Python CLI suite and modular package. It consists of:
- `job_hunt_agent/cli.py`: CLI entry point for executing tasks (search, fit scoring, customize, tracker, apply, integration sync).
- `job_hunt_agent/search.py`: Job search, scraping, scam filtering, and profile fit scoring.
- `job_hunt_agent/customizer.py`: Resume bullet points and customized cover letter generator.
- `job_hunt_agent/tracker.py`: Spreadsheet operations (CSV/Google Sheets) and file management (within `/Jobs/`).
- `job_hunt_agent/apply.py`: Browser/automation system (using Playwright) to autofill job application forms.
- `job_hunt_agent/integrations.py`: Gmail inbox monitor and Google Calendar event synchronization.
- `job_hunt_agent/mock_env.py`: Test environment containing local mock HTML form, mock email server/data, and mock calendar API responses.

## Code Layout
- `/home/monarch/teamwork_projects/job_hunt_agent/`
  - `PROJECT.md` (Global index)
  - `TEST_READY.md` (E2E Test Suite status signal)
  - `MANUAL.md` (Setup and execution guide)
  - `job_hunt_agent/`
    - `__init__.py`
    - `cli.py`
    - `search.py`
    - `customizer.py`
    - `tracker.py`
    - `apply.py`
    - `integrations.py`
    - `mock_env.py`
  - `tests/`
    - `conftest.py`
    - `test_r1_search.py`
    - `test_r2_customize.py`
    - `test_r3_tracker.py`
    - `test_r4_apply.py`
    - `test_r5_gmail_calendar.py`
    - `test_e2e.py`

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | E2E Test Suite | Create comprehensive E2E test infra, tests Tiers 1-4 | None | DONE (Conv ID: 438c2d05-4b4c-4360-bd90-e94e77f7c3e3) |
| 2 | R1: Job Search & Fit Scoring | Implement search, scam filter, fit scoring | M1 | DONE (Conv ID: d5cc5189-7dc1-4516-a279-ec213b684250) |
| 3 | R2: Tailoring Resume & Cover Letters | Tailor resume bullets and cover letters | M1, M2 | DONE (Conv ID: d5cc5189-7dc1-4516-a279-ec213b684250) |
| 4 | R3: Tracker & Filesystem | Write to spreadsheet, organize under `/Jobs/` | M1, M3 | DONE (Conv ID: d5cc5189-7dc1-4516-a279-ec213b684250) |
| 5 | R4: Auto-Apply | Automated form filling with Playwright/mock | M1, M4 | DONE (Conv ID: d5cc5189-7dc1-4516-a279-ec213b684250) |
| 6 | R5: Email & Calendar | Email monitoring & calendar event scheduling | M1, M5 | DONE (Conv ID: d5cc5189-7dc1-4516-a279-ec213b684250) |
| 7 | R6 & Final Validation | Manual, mock environment validation & Tier 5 coverage hardening | M1-M6 | DONE (Conv ID: d5cc5189-7dc1-4516-a279-ec213b684250) |

## Interface Contracts
### `job_hunt_agent.search` ↔ `job_hunt_agent.customizer`
- `search.py` outputs a list of job dicts: `[{"job_id": str, "company": str, "position": str, "description": str, "fit_score": int}]`
- `customizer.py` consumes job dict and generates custom bullets and cover letter: `customize_for_job(job: dict, candidate_profile: dict) -> dict`

### `job_hunt_agent.tracker` ↔ `/Jobs/` folder
- `tracker.py` interacts exclusively with `/Jobs` absolute or relative to the workspace, creating files under `Applications/`, `Resumes/`, `CoverLetters/`, `InterviewPrep/`.

### `job_hunt_agent.apply` ↔ Mock HTML Form
- `apply.py` navigates to target URL, uses Playwright to populate inputs `name`, `email`, `qualifications`, and upload file from `Resumes/`.
