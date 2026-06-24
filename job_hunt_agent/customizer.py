"""Resume and Cover Letter Customization.
"""

import re

def customize_for_job(job: dict, candidate_profile: dict) -> dict:
    """Compares candidate profile against job descriptions to generate tailored resume bullet points
    and customized cover letters.
    """
    job_desc = job.get("description", "").lower()
    job_pos = job.get("position", "")
    company = job.get("company", "")
    
    # 1. Tailor resume bullets based on matching keywords in the job description
    bullets = []
    
    # Check for keywords in job description
    has_python = "python" in job_desc or "script" in job_desc or "automation" in job_desc
    has_linux = "linux" in job_desc or "bash" in job_desc or "unix" in job_desc or "server" in job_desc
    has_network = "network" in job_desc or "cisco" in job_desc or "router" in job_desc or "ip" in job_desc
    
    # Generate bullets from candidate's profile and skills matching job requirements
    if has_python:
        bullets.append("Designed and implemented Python automation scripts to optimize routine backup routines.")
    if has_linux:
        bullets.append("Managed local Linux server environments, managing user access rights and shell scripts.")
    if has_network:
        bullets.append("Configured and maintained local network switch and router configurations, ensuring high uptime.")
        
    # If no specific technical matches, provide default relevant bullets based on candidate profile
    if not bullets:
        bullets.append("Applied core Python and Linux knowledge to build and troubleshoot local tools.")
        bullets.append("Supported local IT hardware and networking tasks to maintain operational readiness.")
        
    # 2. Build customized cover letter
    candidate_name = candidate_profile.get("name", "Bishal Sarkar")
    candidate_skills = ", ".join(candidate_profile.get("skills", ["Python", "Linux", "Networking"]))
    
    cover_letter = f"""Dear Hiring Manager,

I am writing to express my enthusiastic interest in the {job_pos} position at {company}. As a motivated candidate with a strong foundation in {candidate_skills}, I am excited about the opportunity to contribute to your team.

My technical background includes practical experience in:
"""
    for b in bullets:
        cover_letter += f"- {b}\n"
        
    cover_letter += f"""
I am particularly drawn to this role because of {company}'s focus on efficiency and technical excellence. I am confident that my hands-on knowledge of system administration and automation will allow me to integrate quickly and deliver value.

Thank you for your time and consideration. I look forward to the possibility of discussing how my skills align with your needs.

Sincerely,

{candidate_name}
"""
    
    return {
        "resume_bullets": bullets,
        "cover_letter": cover_letter.strip()
    }
