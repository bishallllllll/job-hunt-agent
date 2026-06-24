"""Playwright Form Filler Automation.
"""

import os
from playwright.sync_api import sync_playwright

def apply_to_job(url: str, candidate_info: dict, resume_path: str, screenshot_path: str = None) -> dict:
    """Automates form filling and document upload on job portals using Playwright.
    """
    if not os.path.exists(resume_path):
        return {
            "success": False,
            "message": f"Resume file not found at path: {resume_path}",
            "screenshot": None
        }

    try:
        with sync_playwright() as p:
            # Launch chromium in headless mode
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to the form URL
            page.goto(url, wait_until="load")
            
            # Fill out the form fields
            # We use robust selectors (e.g. name, ID, placeholder or label)
            page.fill('input[name="name"]', candidate_info.get("name", ""))
            page.fill('input[name="email"]', candidate_info.get("email", ""))
            
            # Qualifications could be an input or textarea
            if page.locator('textarea[name="qualifications"]').count() > 0:
                page.fill('textarea[name="qualifications"]', candidate_info.get("qualifications", ""))
            elif page.locator('input[name="qualifications"]').count() > 0:
                page.fill('input[name="qualifications"]', candidate_info.get("qualifications", ""))
                
            # File upload for the resume
            page.set_input_files('input[type="file"]', resume_path)
            
            # Click submit
            # Find submit button by text or selector
            submit_btn = page.locator('button[type="submit"]')
            if submit_btn.count() == 0:
                submit_btn = page.locator('input[type="submit"]')
            if submit_btn.count() == 0:
                submit_btn = page.get_by_role("button", name="Submit")
                
            submit_btn.click()
            
            # Wait for navigation or success page content
            page.wait_for_timeout(1000) # brief wait for mock server response
            
            # Check success condition by analyzing page content
            # (e.g., presence of "Success" or status code or lack of error messages)
            content = page.content()
            success = "success" in content.lower() and "error" not in content.lower()
            
            # Save screenshot proof of application if requested
            saved_screenshot = None
            if screenshot_path:
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                page.screenshot(path=screenshot_path)
                saved_screenshot = screenshot_path
                
            browser.close()
            
            if success:
                return {
                    "success": True,
                    "message": "Application submitted successfully.",
                    "screenshot": saved_screenshot
                }
            else:
                return {
                    "success": False,
                    "message": f"Application submission failed or returned error. Page Content: {content[:200]}",
                    "screenshot": saved_screenshot
                }
                
    except Exception as e:
        return {
            "success": False,
            "message": f"Playwright automation encountered an error: {str(e)}",
            "screenshot": None
        }
