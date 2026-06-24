# Job Hunt Agent — End-to-End (E2E) Test Infrastructure Design

This document details the architecture, design, and execution strategy of the End-to-End (E2E) Test Infrastructure for the autonomous Job Hunt Agent system.

---

## 1. Test Philosophy

The E2E test infrastructure for the Job Hunt Agent is built around three core principles:
1. **Opaque-Box Testing**: Testing is conducted purely from the external boundary of the system. The tests will invoke the public CLI entry points (via `job_hunt_agent/cli.py`) and public package interfaces without directly manipulating internal state variables or injecting code hooks. This ensures that the system behaves correctly as a whole.
2. **Requirement-Driven Design**: Every test case directly traces back to the primary requirements (R1–R6) and acceptance criteria outlined in the project scope. There are no "tests for the sake of tests"; every case verifies a specific system promise.
3. **Hermetic & Mock-Based Execution**: Because the Job Hunt Agent interacts with external networks, third-party job boards, email servers, and calendar systems, the E2E suite executes in a hermetic mock environment. All external APIs (Google Sheets, Gmail SMTP/IMAP, Google Calendar REST API, and job application forms) are intercepted and redirected to a local mock environment (`job_hunt_agent/mock_env.py`). This guarantees test reproducibility, avoids rate limiting, and protects real accounts/credentials.

---

## 2. Feature Inventory (R1–R6 Mapping)

The system requirements are mapped to seven distinct system features under test.

| Feature ID | Feature Name | Requirement Mapping | Description & Verification Method |
|---|---|---|---|
| **F1** | Job Search & Listing Extraction | **R1** (Search and extract remote/local jobs suitable for a 12th-pass) | Evaluates search queries targeting Tripura/Remote and Python/Linux/Networking keywords. Verified by ensuring the parser correctly extracts structured listing fields (company, position, description, location) from mock HTML page responses. |
| **F2** | Scam & MLM Filter | **R1** (Filter out obvious scams, MLM, paid offers) | Evaluates classification logic against mock postings with scam signatures (e.g., upfront payment requests, multi-level marketing keywords). Verified by asserting that scam jobs are completely excluded from the output list. |
| **F3** | Profile Fit Scoring | **R1** (Calculate fit score 1-10 based on candidate profile) | Evaluates match scoring engine comparing Bishal Sarkar's profile to job descriptions. Verified by asserting that high-match jobs (e.g., Python entry-level) score $\ge 6$ and low-match jobs score low. |
| **F4** | Resume & Cover Letter Tailoring | **R2** (Tailored resume bullets & customized cover letters) | Evaluates LLM/template-driven tailoring engine. Verified by asserting that generated documents contain candidate-specific details and match keywords from the target job description. |
| **F5** | Spreadsheet Tracker & Jobs Filesystem | **R3** (Organize tracker and store files exclusively under `/Jobs`) | Evaluates CSV/spreadsheet updates and directory management. Verified by asserting that job files are saved strictly within `/Jobs/Applications`, `/Jobs/Resumes`, etc., and that the spreadsheet records all required columns. |
| **F6** | Playwright Auto-Apply Form Filler | **R4** (Automate form filing & upload resume for fit $\ge 6/10$) | Evaluates browser automation engine using Playwright. Verified by running Playwright headless, navigating to a local mock HTML form, populating fields (name, email, qualifications, resume upload), and verifying submission status. |
| **F7** | Gmail Monitor & Calendar Scheduler | **R5** (Monitor emails and schedule calendar events) | Evaluates email polling and calendar synchronization. Verified by reading mock email headers/bodies (extracting invitations/rejections) and asserting that events are created correctly via the mock calendar interface. |

---

## 3. Test Tiers & Coverage Thresholds

The E2E test suite is organized into four hierarchical Tiers to systematically harden the agent from unit functionality to complete agent workflows.

```
       +---------------------------------------------+
       |       Tier 4: Real-World Scenarios          |
       |  (Simulated daily runs, multi-job queues)   |
       +---------------------------------------------+
                              ▲
                              │
       +---------------------------------------------+
       |   Tier 3: Cross-Feature Combinations        |
       |     (Search -> Customize -> Auto-Apply)     |
       +---------------------------------------------+
                              ▲
                              │
       +---------------------------------------------+
       |    Tier 2: Boundary & Corner Cases          |
       |  (Scam edge cases, broken forms, network)   |
       +---------------------------------------------+
                              ▲
                              │
       +---------------------------------------------+
       |       Tier 1: Feature Coverage              |
       |     (Happy paths for F1-F7 features)        |
       +---------------------------------------------+
```

### Tier 1: Feature Coverage (Happy Paths)
* **Goal**: Validate that all seven features (F1–F7) perform their basic operations correctly under optimal conditions.
* **Scope**: Happy path scenarios with standard inputs and functioning mocks.
* **Coverage Threshold**: 100% of defined features under test must have at least 5 dedicated Tier 1 tests.
* **Example**: Searching for a matching job, getting a high fit score, verifying a valid cover letter is generated, and asserting that the tracker spreadsheet appends a row successfully.

### Tier 2: Boundary & Corner Cases (Unhappy Paths)
* **Goal**: Validate agent robustness, error-handling, and data sanitization when facing abnormal inputs or network failures.
* **Scope**: Empty search results, invalid job structures, borderline fit scores (e.g., 5.9 vs 6.0), malformed mock HTML forms, SMTP/IMAP connection timeouts, and duplicate spreadsheet rows.
* **Coverage Threshold**: At least 5 dedicated Tier 2 test cases per feature (total of 35+ boundary tests). All error-recovery pathways must be verified.
* **Example**: Verifying that a job application form with missing target fields does not cause a silent failure, but instead logs a validation error and marks the application status as "FAILED" in the spreadsheet tracker.

### Tier 3: Cross-Feature Combinations (Pairwise & Integration Flows)
* **Goal**: Validate interaction boundaries and data pipelines between independent features.
* **Scope**:
  - `Job Search (F1) -> Fit Scoring (F2) -> Resume Customization (F3)` flow.
  - `Auto-Apply (F6) -> Tracker Update (F5) -> Calendar Scheduling (F7)` flow.
* **Coverage Threshold**: Coverage of all major inter-feature interface contracts. At least 6 complex interaction scenarios must be verified.
* **Example**: Ensuring that when an auto-apply task fails, the spreadsheet tracker logs the failure correctly, and the calendar scheduler does not register an interview reminder event.

### Tier 4: Real-World Scenarios (Full Life Cycle)
* **Goal**: Simulate complete operational days of Bishal Sarkar's job hunt.
* **Scope**: A full multi-job process: the CLI is invoked to scan a feed containing a mix of matching jobs, scam jobs, and non-matching jobs. The agent must:
  1. Filter scams and low-fit jobs.
  2. For high-fit jobs ($\ge 6$), tailors resume and cover letter, save them in the `/Jobs` directory.
  3. Perform auto-apply via Playwright to the mock form.
  4. Record the application status in the spreadsheet tracker.
  5. Check mock emails for an interview invitation.
  6. Schedule the interview invitation on the mock Google Calendar.
* **Coverage Threshold**: Full path execution validation. The test must run from start to finish without manual intervention and with zero errors.

---

## 4. Test Architecture & Environment

### Directory Layout
The project follows a standard python layout where the test suite is co-located under a single `tests/` directory at the project root:

```
/home/monarch/teamwork_projects/job_hunt_agent/
├── PROJECT.md                    # Project index
├── TEST_INFRA.md                 # Test architecture documentation (This file)
├── MANUAL.md                     # Setup and verification manual
├── job_hunt_agent/               # System package
│   ├── __init__.py
│   ├── cli.py                    # Entry CLI script
│   ├── search.py                 # Search and fit scoring
│   ├── customizer.py             # Resume & cover letter tailoring
│   ├── tracker.py                # Spreadsheet and directory organization
│   ├── apply.py                  # Playwright form automation
│   ├── integrations.py           # Gmail and Calendar integrations
│   └── mock_env.py               # Local mock server & data environment
└── tests/                        # E2E Test Suite
    ├── conftest.py               # Pytest global fixtures and configurations
    ├── test_r1_search.py         # Tests for F1, F2, F3
    ├── test_r2_customize.py      # Tests for F4
    ├── test_r3_tracker.py        # Tests for F5
    ├── test_r4_apply.py          # Tests for F6 (Playwright mock form tests)
    ├── test_r5_gmail_calendar.py # Tests for F7
    └── test_e2e.py               # Comprehensive Tier 4 E2E scenarios
```

### Test Runner & Dependency Bootstrapping
The E2E test suite utilizes **pytest** as its primary test runner. 

* **System Status Verification**: During the E2E Test Suite design phase, the system environment was verified. **Pytest is not currently installed or available** in the default Python environment.
* **Required Bootstrapping Step**: Before executing the tests, a virtual environment must be initialized and pytest along with necessary plugins must be installed:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install pytest pytest-playwright pytest-mock
  # Initialize Playwright browsers
  playwright install chromium
  ```

### Mock Environment Specification (`mock_env.py`)
To isolate tests from external live networks, the `job_hunt_agent/mock_env.py` module exposes simulated services:
1. **Mock HTML Form**: A lightweight local HTTP server (using Python's `http.server` or `Flask` bound to `localhost`) that renders a standard application form containing fields: `name`, `email`, `qualifications`, and a file input for the resume. The server validates that submission requests contain expected data and returns a success page or appropriate HTTP errors to test Tier 2 cases.
2. **Mock Email Client**: A mock mail data provider that simulates incoming IMAP responses for Gmail. It returns structured email dictionaries representing job notifications, interview invites, and assessment links.
3. **Mock Google Calendar API**: A mock client class that intercepts requests to the Google Calendar API, storing scheduled events in local memory and validating payload structures (e.g. date format, summary length).
4. **Mock Job Search Feed**: Local HTML pages mimicking job board listings (e.g. LinkedIn, Indeed) to test search queries and extraction capabilities.
