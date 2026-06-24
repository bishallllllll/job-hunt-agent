# Job Hunt Agent

> An intelligent, modular Python CLI suite that automates the end-to-end job search workflow — from discovering roles and scoring fit, to tailoring resumes, tracking applications, and auto-applying.

---

## Features

| Module | Capability |
|--------|-----------|
| **Search & Score** | Scrapes job boards, filters scam postings, and scores each listing against your candidate profile. |
| **Resume & Cover Letter Customizer** | Generates tailored resume bullet points and cover letters for every job. |
| **Application Tracker** | Manages a structured CSV/Google Sheets tracker and organises files under a `/Jobs/` directory. |
| **Auto-Apply** | Uses Playwright browser automation to fill and submit application forms. |
| **Gmail & Calendar Sync** | Monitors your inbox for recruiter replies and creates Google Calendar events for interviews. |

## Architecture Overview

```
┌──────────┐     ┌──────────────┐     ┌───────────┐
│  CLI     │────▶│  search.py   │────▶│customizer │
│ (cli.py) │     │  (scrape,    │     │ (resume & │
│          │     │   filter,    │     │  cover    │
│          │     │   score)     │     │  letter)  │
└──────────┘     └──────────────┘     └───────────┘
      │                                     │
      ▼                                     ▼
┌──────────┐     ┌──────────────┐     ┌───────────┐
│ apply.py │     │ tracker.py   │     │integrations│
│(Playwright│     │ (CSV/Sheets, │     │ (Gmail &  │
│ autofill)│     │  /Jobs/ fs)  │     │ Calendar) │
└──────────┘     └──────────────┘     └───────────┘
```

## Project Structure

```
job_hunt_agent/
├── job_hunt_agent/          # Core package
│   ├── __init__.py
│   ├── cli.py               # CLI entry point
│   ├── search.py            # Job search, scraping, scam filter, fit scoring
│   ├── customizer.py        # Resume & cover letter generation
│   ├── tracker.py           # CSV/Sheets tracker & file management
│   ├── apply.py             # Playwright-based auto-apply
│   ├── integrations.py      # Gmail & Google Calendar sync
│   └── mock_env.py          # Mock test environment (HTML form, email, calendar)
├── tests/                   # Test suite
│   ├── conftest.py          # Shared fixtures
│   ├── test_r1_search.py    # R1: Search & fit scoring tests
│   ├── test_r2_customize.py # R2: Customization tests
│   └── test_r4_apply.py     # R4: Auto-apply tests
├── PROJECT.md               # Architecture & milestone tracking
├── TEST_INFRA.md            # E2E test infrastructure design
├── ORIGINAL_REQUEST.md      # Original project requirements
├── CHANGELOG.md             # Version history
└── README.md                # This file
```

## Installation & Setup

### Prerequisites

- Python 3.10+
- [Playwright](https://playwright.dev/python/) (for auto-apply)

### Quick Start

```bash
# Clone the repository
git clone <repo-url> && cd job_hunt_agent

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt   # (when available)

# Install Playwright browsers
playwright install
```

## Usage

```bash
# Run a job search
python -m job_hunt_agent.cli search --query "software engineer" --location "remote"

# Customize resume for a specific job
python -m job_hunt_agent.cli customize --job-id <ID>

# Track an application
python -m job_hunt_agent.cli track --add --job-id <ID>

# Auto-apply to a job
python -m job_hunt_agent.cli apply --job-id <ID>
```

## Running Tests

```bash
pytest tests/ -v
```

## License

This project is currently unlicensed. A license will be added in a future release.
