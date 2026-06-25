import re
import abc

# Bishal Sarkar's Profile Constant
BISHAL_PROFILE = {
    "name": "Bishal Sarkar",
    "email": "bishalsarkar999997@gmail.com",
    "phone": "+91 7630032632",
    "address": "Madhya Bhuban Ban, Agartala, Tripura - 799002",
    "dob": "2001-07-19",
    "education": "BA in Psychology (ICFAI Tripura University, 2023-2026), Higher Secondary (Henry Derozio Academy, 2018-2020)",
    "skills": [
        "Python", "Bash", "Bash Scripting", "Linux",
        "AI & Machine Learning", "Deep Learning", "LLMs", "Generative AI",
        "AI Agents", "Agentic AI Development", "Prompt Engineering",
        "Web Development", "Front-End", "Back-End", "API Development",
        "Cybersecurity", "Networking",
        "Financial Analysis", "FX Trading",
        "Critical Thinking", "Remote Collaboration"
    ],
    "certifications": [
        "Python Essentials (Cisco, 01/2026)",
        "AI Fundamentals (02/2025)",
        "Introduction to Cybersecurity (Cisco, 12/2025)",
        "Prompt Engineering with the OpenAI API (DataCamp, 04/2026)",
        "Introduction to AI Agents (DataCamp, 04/2026)",
        "Working with the OpenAI API (DataCamp, 04/2026)"
    ],
    "work_experience": "Branch Relationship Executive at SBI Card (01/2026 - 03/2026, Agartala)",
    "projects": [
        "Aggressive LLM-Powered Forex Trading Bot (Multi-Agent Architecture, Azure OpenAI / AWS Bedrock)",
        "Forex Agentic — Autonomous Multi-Agent Trading System (github.com/bishallllllll/forex-agentic)"
    ],
    "github": "github.com/bishallllllll",
    "website": "bishalsarkar.me",
    "linkedin": "linkedin.com/in/bishalsarkar",
    "location_pref": ["Agartala", "Tripura", "Remote"],
    "languages": ["English", "Bengali", "Hindi"],
    "qualifications": "BA in Psychology from ICFAI Tripura University. Cisco-certified in Python Essentials and Cybersecurity. "
        "DataCamp-certified in Prompt Engineering, AI Agents, and OpenAI API. "
        "Built multi-agent AI trading systems with Python, LLMs, and cloud APIs. "
        "Skilled in Python automation, Bash scripting, Linux administration, web development, and networking. "
        "Experience as Branch Relationship Executive at SBI Card."
}

# Settings for scraper selection
SETTINGS = {
    "USE_MOCK": True
}

class BaseScraper(abc.ABC):
    @abc.abstractmethod
    def scrape(self, query: str, location: str) -> list[dict]:
        """
        Scrape jobs matching the query and location.
        Returns raw job dictionaries in the standardized interface contract format.
        """
        pass

class MockScraper(BaseScraper):
    def __init__(self):
        # The 8 curated mock postings described in the explorer's analysis.md
        self.jobs = [
            {
                "job_id": "job_1",
                "company": "TechSolutions India",
                "position": "Junior Python Scripting Developer",
                "location": "Remote",
                "description": "Looking for a junior developer to write Python scripts for automating Linux server administration. Basic understanding of TCP/IP networking, routing, and DNS is a plus. Perfect for freshers or high school graduates with strong programming logic.",
                "salary": "₹4,00,000 - ₹5,50,000 per annum",
                "source": "LinkedIn"
            },
            {
                "job_id": "job_2",
                "company": "Tripura Telecoms",
                "position": "Network Assistant & IT Support",
                "location": "Agartala, Tripura",
                "description": "Local telecom services company seeking an IT support assistant. Responsibilities include configuring Linux routers and switches, diagnosing network connectivity issues, and executing basic Python troubleshooting scripts. Candidates who have passed 12th standard with certification in CCNA are encouraged to apply.",
                "salary": "₹2,40,000 per annum",
                "source": "Indeed"
            },
            {
                "job_id": "job_3",
                "company": "Global Hosters",
                "position": "Linux System Administrator Trainee",
                "location": "Remote",
                "description": "Entry level position for managing Debian and Ubuntu systems. Must be proficient with command-line interfaces and bash scripting. Python knowledge is preferred but not required. High school graduates with relevant self-taught skills are welcome.",
                "salary": "₹3,00,000 per annum",
                "source": "Indeed"
            },
            {
                "job_id": "job_4",
                "company": "Bangalore WebWorks",
                "position": "Python Software Engineer",
                "location": "Bangalore, Karnataka",
                "description": "Seeking a Python Software Engineer to build web applications using Django and React. Must have a Bachelor's degree in Computer Science. This is a strictly on-site role in Bangalore.",
                "salary": "₹8,00,000 per annum",
                "source": "Naukri"
            },
            {
                "job_id": "job_5",
                "company": "Online Jobs Ltd",
                "position": "Work from Home Data Typist",
                "location": "Remote",
                "description": "Earn money by typing simple documents from the comfort of your home. Easy work, suitable for students and freshers. Note: A refundable registration fee of ₹500 is required for training materials and software setup. Once the first assignment is submitted, the deposit will be refunded.",
                "salary": "₹25,000 per month",
                "source": "Quickr"
            },
            {
                "job_id": "job_6",
                "company": "Dynamic Marketing Network",
                "position": "Independent Business Associate",
                "location": "Agartala, Tripura",
                "description": "Be your own boss and build your network! We are an international multi-level marketing company looking for partners in Agartala. High commission rates, recruit friends and family to build your downline team and earn residual income. No technical experience required, 12th pass candidates welcome.",
                "salary": "₹50,000 - ₹2,00,000 per month commission",
                "source": "Facebook Jobs"
            },
            {
                "job_id": "job_7",
                "company": "Private Employer",
                "position": "Part-time Copy Paste Operator",
                "location": "Remote",
                "description": "Earn money online daily. Easy copy paste work. No resume required. Earn up to ₹5,000 per day. For details, send an email to jobs4you@gmail.com.",
                "salary": "₹1,50,000 per month",
                "source": "WhatsApp Group"
            },
            {
                "job_id": "job_8",
                "company": "Cisco Systems",
                "position": "Senior Network Architect",
                "location": "Remote",
                "description": "Designing large scale enterprise networks. Must have a Master's degree in Telecommunications or Computer Science. Minimum 10 years of experience. Python automation and advanced Linux administration required. Must understand enterprise Kubernetes deployments.",
                "salary": "₹25,00,000 per annum",
                "source": "LinkedIn"
            }
        ]

    def scrape(self, query: str, location: str) -> list[dict]:
        filtered = []
        q = (query or "").lower().strip()
        loc = (location or "").lower().strip()

        for job in self.jobs:
            # Query match: check position or description
            match_query = True
            if q:
                match_query = (q in job["position"].lower()) or (q in job["description"].lower())

            # Location match: check location
            match_loc = True
            if loc:
                match_loc = (loc in job["location"].lower())

            if match_query and match_loc:
                filtered.append(job)
        return filtered

class PlaywrightScraper(BaseScraper):
    """
    Real-world scraper using Playwright to extract data from Indeed/LinkedIn.
    Used in production mode.
    """
    def scrape(self, query: str, location: str) -> list[dict]:
        raise NotImplementedError("Network calls disabled in CODE_ONLY mode.")

def check_suspicious_salary(job_details: dict) -> bool:
    pos = (job_details.get("position", "") or "").lower()
    sal = (job_details.get("salary", "") or "").lower()
    desc = (job_details.get("description", "") or "").lower()

    # Check if position refers to basic task
    basic_task_keywords = ["data entry", "typing", "form filling", "copy paste", "sms sending", "data typist", "operator"]
    is_basic_task = any(kw in pos for kw in basic_task_keywords)
    if not is_basic_task:
        return False

    sal_clean = sal.replace(",", "")
    desc_clean = desc.replace(",", "")

    # Monthly check:
    # Monthly threshold: ₹1,00,000 INR or $1,200 USD
    if "lakh" in sal_clean or "lakh" in desc_clean:
        return True

    # If "month" or "monthly" or "pm" or "/mo" is in salary string:
    if any(kw in sal_clean for kw in ["month", "monthly", "pm", "/mo"]):
        amounts = [int(n) for n in re.findall(r"\d+", sal_clean)]
        for amt in amounts:
            if amt >= 100000 or (("$" in sal_clean or "usd" in sal_clean) and amt >= 1200):
                return True

    # Daily check:
    # Daily threshold: ₹5,000 INR or $60 USD
    if any(kw in sal_clean for kw in ["day", "daily", "pd", "/day"]):
        amounts = [int(n) for n in re.findall(r"\d+", sal_clean)]
        for amt in amounts:
            if amt > 5000 or (("$" in sal_clean or "usd" in sal_clean) and amt >= 60):
                return True

    # Check description for daily claims:
    daily_desc_matches = re.findall(r"(?:earn|make|up to|get|receive)\s*(?:₹|\$)?\s*(\d+)\s*(?:per\s*day|daily|a\s*day)", desc_clean)
    for amt_str in daily_desc_matches:
        amt = int(amt_str)
        if amt >= 5000:
            return True

    # Hourly check:
    # Hourly threshold: ₹1,000 INR or $12 USD
    if any(kw in sal_clean for kw in ["hour", "hourly", "hr", "/hr"]):
        amounts = [int(n) for n in re.findall(r"\d+", sal_clean)]
        for amt in amounts:
            if amt >= 1000 or (("$" in sal_clean or "usd" in sal_clean) and amt >= 12):
                return True

    # Check description for hourly claims:
    hourly_desc_matches = re.findall(r"(?:earn|make|pay|rate of)?\s*(?:₹|\$)?\s*(\d+)\s*(?:per\s*hour|hourly|/hr|an\s*hour)", desc_clean)
    for amt_str in hourly_desc_matches:
        amt = int(amt_str)
        if amt >= 1000:
            return True

    # If salary field has no period indicator, but it contains a high number:
    all_sal_numbers = [int(n) for n in re.findall(r"\d+", sal_clean)]
    for amt in all_sal_numbers:
        if amt >= 100000 and not any(kw in sal_clean for kw in ["annum", "year", "pa", "/yr"]):
            return True

    return False

def is_scam(job_details: dict) -> bool:
    """
    Apply heuristics and rules to determine if a job posting is a scam.
    Returns True if a scam is detected, False otherwise.
    """
    pos = (job_details.get("position", "") or "").lower()
    desc = (job_details.get("description", "") or "").lower()
    comp = (job_details.get("company", "") or "").lower()

    # Rule S1: Payment/Deposit Requests
    s1_regex = r"\b(pay|deposit|fee|charge|cost)\b.*\b(refundable|registration|security|processing|training|laptop|kit|equipment|upfront)\b"
    s1_keywords = ["registration fee", "refundable deposit", "security deposit", "processing fee", "buy training kit", "pay for laptop", "laptop deposit", "application fee"]
    if re.search(s1_regex, desc) or re.search(s1_regex, pos) or any(kw in desc for kw in s1_keywords) or any(kw in pos for kw in s1_keywords):
        return True

    # Rule S2: MLM & Pyramid Schemes
    s2_regex = r"\b(mlm|network marketing|pyramid scheme|recruit\b.*\bdownline|multi-level marketing)\b"
    s2_keywords = ["mlm", "multi-level marketing", "pyramid scheme", "recruit friends", "be your own boss", "downline", "commission only", "network marketing", "residual income", "unlimited earning potential"]
    if re.search(s2_regex, desc) or re.search(s2_regex, pos) or any(kw in desc for kw in s2_keywords) or any(kw in pos for kw in s2_keywords):
        return True

    # Rule S3: Unrealistic/Suspicious Salaries
    if check_suspicious_salary(job_details):
        return True

    # Rule S4: Vague / Missing Company Details
    is_vague_company = not comp.strip() or comp.strip() in ["unknown", "confidential", "private employer", "recruiter"]
    is_short_desc = len(desc.strip()) < 120

    public_email_pattern = r"\b[a-zA-Z0-9._%+-]+@(gmail|yahoo|outlook|hotmail)\.com\b"
    has_public_email = bool(re.search(public_email_pattern, desc))
    generic_title_keywords = ["data entry", "typing", "form filling", "copy paste", "sms sending", "whatsapp chat support", "operator", "associate", "assistant", "agent", "helper"]
    has_generic_title = any(kw in pos for kw in generic_title_keywords)
    is_vague_email_scam = has_public_email and has_generic_title

    if is_vague_company or is_short_desc or is_vague_email_scam:
        return True

    # Rule S5: Typical Scam Role Titles
    scam_titles = [
        "data entry operator",
        "part-time typing job",
        "form filling work from home",
        "sms sending job",
        "whatsapp chat support (no experience)",
        "online copy paste job"
    ]
    if any(title in pos for title in scam_titles):
        return True

    return False

def has_skill_category(text: str, keywords: list[str], is_python: bool = False) -> bool:
    """
    Checks if a skill category keyword matches in the text.
    Ignores the match if it is accompanied by "not required" or "optional" within 40 characters.
    """
    for kw in keywords:
        pattern = r"\b" + re.escape(kw) + r"\b"
        for match in re.finditer(pattern, text):
            # Check context around the match
            start = max(0, match.start() - 40)
            end = min(len(text), match.end() + 40)
            context = text[start:end]
            if "not required" in context or "optional" in context:
                continue

            # If checking python and the keyword is scripting, ensure it's not bash/shell/linux scripting
            if is_python and kw == "scripting":
                prefix = text[max(0, match.start() - 15):match.start()].lower()
                if "bash" in prefix or "shell" in prefix or "linux" in prefix:
                    continue
            return True
    return False

def round_half_up(n: float) -> int:
    """
    Rounds a number to the nearest integer, rounding half up (standard math rounding).
    """
    return int(n + 0.5)

def calculate_fit_score(job_details: dict, profile: dict) -> int:
    """
    Calculate a fit score from 1 to 10 based on candidate profile.
    """
    job_loc = (job_details.get("location", "") or "").lower()
    job_desc = (job_details.get("description", "") or "").lower()
    pos = (job_details.get("position", "") or "").lower()
    text_to_search = pos + " " + job_desc

    # 1. Location Fit (Max 3 points)
    pref_matched = False
    for pref in profile.get("location_pref", []):
        if pref.lower() in job_loc:
            pref_matched = True
            break

    wfh_keywords = ["work from home", "remote friendly", "wfh", "remote-friendly"]
    wfh_matched = any(kw in job_desc for kw in wfh_keywords)

    loc_score = 3 if (pref_matched or wfh_matched) else 0

    # 2. Education Fit (Max 2 points)
    twelfth_keywords = ["12th pass", "12th standard", "high school", "diploma", "no degree", "freshers welcome", "fresher's welcome"]
    if any(kw in job_desc for kw in twelfth_keywords):
        edu_score = 2
    else:
        degree_pattern = r"\b(degree|bachelor|b\.tech|btech|bca|b\.s\.|m\.s\.|ms|msc|mca|master|ph\.d|phd|graduate|graduation)\b"
        if not re.search(degree_pattern, job_desc):
            edu_score = 2
        else:
            if "equivalent" in job_desc:
                edu_score = 1
            else:
                edu_score = 0

    # 3. Skill Match (Max 5 points)
    skill_score = 0.0
    python_keywords = ["python", "django", "flask", "fastapi", "scripting"]
    linux_keywords = ["linux", "ubuntu", "debian", "bash", "shell scripting"]
    networking_keywords = ["networking", "tcp/ip", "dns", "dhcp", "routing", "switching", "ccna", "routers", "switches"]

    if has_skill_category(text_to_search, python_keywords, is_python=True):
        skill_score += 2.0
    if has_skill_category(text_to_search, linux_keywords):
        skill_score += 1.5
    if has_skill_category(text_to_search, networking_keywords):
        skill_score += 1.5

    # 4. Penalties
    conflicting_skills = ["kubernetes", "docker", "aws", "java", "c++", "react", "angular"]
    conflicting_penalty = 0
    for skill in conflicting_skills:
        if skill == "c++":
            if re.search(r"\bc\+\+", text_to_search):
                conflicting_penalty += 1
        else:
            if re.search(r"\b" + re.escape(skill) + r"\b", text_to_search):
                conflicting_penalty += 1

    experience_penalty = 0
    has_senior_kw = any(kw in text_to_search for kw in ["senior", "lead", "architect"])
    years_pattern = r"\b(3|4|5|6|7|8|9|10|[1-9]\d+)\+?\s*years?\b"
    has_years = bool(re.search(years_pattern, text_to_search))
    word_years_pattern = r"\b(three|four|five|six|seven|eight|nine|ten)\s*years?\b"
    has_word_years = bool(re.search(word_years_pattern, text_to_search))

    if has_senior_kw or has_years or has_word_years:
        experience_penalty = 2

    # Calculate points
    net_skill_score = max(0.0, skill_score - conflicting_penalty)
    total_points = loc_score + edu_score + net_skill_score - experience_penalty
    fit_score = round_half_up(total_points)
    fit_score = max(1, min(10, fit_score))

    # Apply Experience Cap
    if experience_penalty > 0:
        fit_score = min(fit_score, 4)

    # Apply Location Cap
    if not pref_matched and not wfh_matched:
        if net_skill_score >= 5.0:
            fit_score = min(fit_score, 2)
        else:
            fit_score = min(fit_score, 1)

    return fit_score

def search_jobs(query: str, location: str, include_scams: bool = False) -> list[dict]:
    """
    Search and retrieve jobs matching the search query and location.
    Under CODE_ONLY mode, this returns filtered mock data or local JSON results.
    If include_scams is False (default), it filters out jobs flagged by is_scam.
    """
    if SETTINGS.get("USE_MOCK", True):
        scraper = MockScraper()
    else:
        scraper = PlaywrightScraper()

    raw_jobs = scraper.scrape(query, location)
    processed_jobs = []

    for job in raw_jobs:
        scam_flag = is_scam(job)
        if scam_flag and not include_scams:
            continue

        fit = calculate_fit_score(job, BISHAL_PROFILE)

        job_copy = job.copy()
        job_copy["is_scam"] = scam_flag
        job_copy["fit_score"] = fit
        processed_jobs.append(job_copy)

    return processed_jobs
