"""Playwright Form Filler Automation.
"""

import os
import random
import time
from playwright.sync_api import sync_playwright
from job_hunt_agent.search import SETTINGS

def apply_to_job(url: str, candidate_info: dict, resume_path: str, screenshot_path: str = None) -> dict:
    """Automates form filling and document upload on job portals using Playwright (mock) or SeleniumBase UC (live).
    """
    if not os.path.exists(resume_path):
        return {
            "success": False,
            "message": f"Resume file not found at path: {resume_path}",
            "screenshot": None
        }

    info = candidate_info.copy()
    if not info.get("qualifications"):
        education = info.get("education", "")
        skills = info.get("skills", [])
        if isinstance(skills, list):
            skills_str = ", ".join(skills)
        else:
            skills_str = str(skills)
        info["qualifications"] = f"Education: {education}. Skills: {skills_str}."

    # Check the mode from SETTINGS
    if SETTINGS.get("USE_MOCK", True):
        # Execute the existing Playwright flow
        try:
            with sync_playwright() as p:
                # Launch chromium in headless mode
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                
                # Navigate to the form URL
                page.goto(url, wait_until="load")
                
                # Semantic form filling
                # Find all potential inputs, textareas, selects
                elements = page.locator('input, textarea, select').all()
                
                for el in elements:
                    name_attr = (el.get_attribute("name") or "").lower()
                    id_attr = (el.get_attribute("id") or "").lower()
                    placeholder = (el.get_attribute("placeholder") or "").lower()
                    aria_label = (el.get_attribute("aria-label") or "").lower()
                    el_type = (el.get_attribute("type") or "").lower()
                    
                    # Associated label text
                    label_text = ""
                    if id_attr:
                        label_el = page.locator(f'label[for="{id_attr}"]')
                        if label_el.count() > 0:
                            label_text = label_el.first.text_content().lower()
                    
                    if not label_text:
                        label_text = el.evaluate("""el => {
                            let parent = el.closest('label');
                            if (parent) return parent.textContent;
                            let prev = el.previousElementSibling;
                            if (prev && prev.tagName === 'LABEL') return prev.textContent;
                            return '';
                        }""").lower()
                    
                    combined_text = f"{name_attr} {id_attr} {placeholder} {aria_label} {label_text}".strip()
                    
                    # Match fields semantically
                    if el_type in ["checkbox", "radio"]:
                        has_required = el.get_attribute("required") is not None
                        agreement_keywords = ["agree", "accept", "consent", "terms"]
                        has_agreement = any(kw in combined_text for kw in agreement_keywords)
                        if has_required or has_agreement:
                            try:
                                if not el.is_checked():
                                    el.check()
                            except Exception:
                                pass
                    elif el_type == "file" or any(kw in combined_text for kw in ["resume", "cv", "upload", "attachment"]):
                        el.set_input_files(resume_path)
                    elif "email" in combined_text or "mail" in combined_text:
                        el.fill(info.get("email", ""))
                    elif any(kw in combined_text for kw in ["name", "fullname", "first", "last"]):
                        if any(mod in combined_text for mod in ["emergency", "contact", "referrer", "relative"]):
                            # Do not fill emergency contact/referrer/relative name fields with candidate's name
                            pass
                        else:
                            if "first" in combined_text and not "last" in combined_text:
                                el.fill(info.get("name", "").split()[0])
                            elif "last" in combined_text and not "first" in combined_text:
                                parts = info.get("name", "").split()
                                el.fill(parts[-1] if len(parts) > 1 else "")
                            else:
                                el.fill(info.get("name", ""))
                    elif any(kw in combined_text for kw in ["qualification", "experience", "education", "summary", "about", "cover"]):
                        is_experience = "experience" in combined_text
                        tag_name = el.evaluate("el => el.tagName").lower()
                        is_short_text = (tag_name == "input" and el_type in ["", "text"])
                        
                        if is_experience and (el_type == "number" or is_short_text):
                            if el_type == "number" or "years" in combined_text:
                                el.fill("2")
                            else:
                                # Short text input, ignore if inappropriate (do not fill with qualifications)
                                pass
                        else:
                            el.fill(info.get("qualifications", ""))
                
                # Save screenshot of the completed form before submission
                saved_screenshot = None
                if not screenshot_path:
                    screenshot_path = os.path.join(os.getcwd(), "Jobs", "Screenshots", "completed_form.png")
                
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                page.screenshot(path=screenshot_path)
                saved_screenshot = screenshot_path
                
                # Human-in-the-loop Submission halt
                print(f"\n[HITL] Form filled for {url}.")
                print(f"[HITL] Screenshot saved at: {saved_screenshot}")
                
                approval = input("Awaiting manual approval to submit. Type 'yes' or 'y' to submit, or anything else to abort: ")
                
                if approval.lower() in ["yes", "y"]:
                    # Find submit button by text or selector
                    submit_btn = page.locator('button[type="submit"]')
                    if submit_btn.count() == 0:
                        submit_btn = page.locator('input[type="submit"]')
                    if submit_btn.count() == 0:
                        submit_btn = page.get_by_role("button", name="Submit")
                    
                    if submit_btn.count() > 0:
                        submit_btn.first.click()
                    
                    # Wait for navigation or success page content
                    page.wait_for_timeout(1000) # brief wait for mock server response
                    
                    # Check success condition by analyzing page content
                    content = page.content()
                    success = "success" in content.lower() and "error" not in content.lower()
                    message = "Application submitted successfully." if success else f"Application submission failed or returned error. Page Content: {content[:200]}"
                else:
                    success = False
                    message = "Application submission aborted by user."
                    
                browser.close()
                
                return {
                    "success": success,
                    "message": message,
                    "screenshot": saved_screenshot
                }
                    
        except Exception as e:
            return {
                "success": False,
                "message": f"Playwright automation encountered an error: {str(e)}",
                "screenshot": None
            }
    else:
        # Execute the new SeleniumBase UC flow
        from seleniumbase import SB
        from selenium.webdriver.common.action_chains import ActionChains

        if not screenshot_path:
            screenshot_path = os.path.join(os.getcwd(), "Jobs", "Screenshots", "completed_form.png")

        try:
            with SB(uc=True, headless=True) as sb:
                # Viewport size randomization
                sb.set_window_size(random.randint(1024, 1920), random.randint(768, 1080))
                
                sb.open(url)
                # Anti-bot / page load delay
                time.sleep(random.uniform(2.0, 4.0))
                
                # Fetch all inputs, textareas, selects
                elements = sb.driver.find_elements("css selector", "input, textarea, select")
                
                for el in elements:
                    try:
                        tag_name = el.tag_name.lower()
                        el_type = (el.get_attribute("type") or "").lower()
                        
                        name_attr = (el.get_attribute("name") or "").lower()
                        id_attr = (el.get_attribute("id") or "").lower()
                        placeholder = (el.get_attribute("placeholder") or "").lower()
                        aria_label = (el.get_attribute("aria-label") or "").lower()
                        
                        label_text = ""
                        if id_attr:
                            try:
                                label_el = sb.driver.find_element("css selector", f'label[for="{id_attr}"]')
                                label_text = label_el.text.lower()
                            except Exception:
                                pass
                        
                        if not label_text:
                            label_text = sb.execute_script("""
                                let el = arguments[0];
                                let parent = el.closest('label');
                                if (parent) return parent.textContent;
                                let prev = el.previousElementSibling;
                                if (prev && prev.tagName === 'LABEL') return prev.textContent;
                                return '';
                            """, el).lower()
                        
                        combined_text = f"{name_attr} {id_attr} {placeholder} {aria_label} {label_text}".strip()
                        
                        # Match fields semantically and fill
                        if el_type in ["checkbox", "radio"]:
                            has_required = el.get_attribute("required") is not None
                            agreement_keywords = ["agree", "accept", "consent", "terms", "policy", "understand", "acknowledge", "authorize", "permit", "yes", "correct", "true"]
                            negative_keywords = ["sponsor", "visa", "decline", "disagree"]
                            has_agreement = any(kw in combined_text for kw in agreement_keywords) and not any(kw in combined_text for kw in negative_keywords)
                            if (has_required or has_agreement) and not el.is_selected():
                                try:
                                    el.click()
                                except Exception:
                                    # Coordinate-based vision click fallback
                                    rect = sb.execute_script("""
                                        let rect = arguments[0].getBoundingClientRect();
                                        return {x: rect.left + rect.width / 2, y: rect.top + rect.height / 2};
                                    """, el)
                                    sb.execute_script("""
                                        let x = arguments[0]; let y = arguments[1];
                                        let target = document.elementFromPoint(x, y);
                                        if (target) target.click();
                                    """, rect["x"], rect["y"])
                                    try:
                                        actions = ActionChains(sb.driver)
                                        actions.move_to_location(int(rect["x"]), int(rect["y"])).click().perform()
                                    except Exception:
                                        pass
                        elif el_type == "file" or any(kw in combined_text for kw in ["resume", "cv", "upload", "attachment"]):
                            try:
                                el.send_keys(os.path.abspath(resume_path))
                            except Exception:
                                pass
                        elif tag_name == "select":
                            # Dropdown selection by matching semantic text
                            options = el.find_elements("tag name", "option")
                            is_yes_no = False
                            target_positive = True
                            if any(kw in combined_text for kw in ["authorized", "eligible", "permit", "citizen", "legal"]):
                                is_yes_no = True
                                target_positive = True
                            elif any(kw in combined_text for kw in ["sponsor", "visa", "require"]):
                                is_yes_no = True
                                target_positive = False
                            
                            if is_yes_no:
                                best_option = None
                                for opt in options:
                                    opt_text = opt.text.lower()
                                    if target_positive:
                                        if opt_text in ["yes", "y", "authorized", "agree", "true"]:
                                            best_option = opt
                                            break
                                    else:
                                        if opt_text in ["no", "n", "disagree", "false"]:
                                            best_option = opt
                                            break
                                if best_option:
                                    best_option.click()
                        else:
                            # Text input / textarea
                            value_to_fill = ""
                            if "email" in combined_text or "mail" in combined_text:
                                value_to_fill = info.get("email", "")
                            elif any(kw in combined_text for kw in ["phone", "mobile", "contact", "tel"]):
                                value_to_fill = info.get("phone", "")
                            elif any(kw in combined_text for kw in ["name", "fullname", "first", "last"]):
                                if any(mod in combined_text for mod in ["emergency", "contact", "referrer", "relative"]):
                                    pass
                                else:
                                    if "first" in combined_text and not "last" in combined_text:
                                        value_to_fill = info.get("name", "").split()[0]
                                    elif "last" in combined_text and not "first" in combined_text:
                                        parts = info.get("name", "").split()
                                        value_to_fill = parts[-1] if len(parts) > 1 else ""
                                    else:
                                        value_to_fill = info.get("name", "")
                            elif any(kw in combined_text for kw in ["qualification", "experience", "education", "summary", "about", "cover"]):
                                is_experience = "experience" in combined_text
                                is_short_text = (tag_name == "input" and el_type in ["", "text"])
                                if is_experience and (el_type == "number" or is_short_text):
                                    if el_type == "number" or "years" in combined_text:
                                        value_to_fill = "2"
                                else:
                                    value_to_fill = info.get("qualifications", "")
                            
                            if value_to_fill:
                                try:
                                    el.clear()
                                    el.send_keys(value_to_fill)
                                except Exception:
                                    # Coordinates-based vision click & type fallback
                                    rect = sb.execute_script("""
                                        let rect = arguments[0].getBoundingClientRect();
                                        return {x: rect.left + rect.width / 2, y: rect.top + rect.height / 2};
                                    """, el)
                                    sb.execute_script("""
                                        let x = arguments[0]; let y = arguments[1];
                                        let target = document.elementFromPoint(x, y);
                                        if (target) { target.focus(); target.click(); }
                                    """, rect["x"], rect["y"])
                                    try:
                                        actions = ActionChains(sb.driver)
                                        actions.move_to_location(int(rect["x"]), int(rect["y"])).click().send_keys(value_to_fill).perform()
                                    except Exception:
                                        sb.execute_script("arguments[0].value = arguments[1];", el, value_to_fill)
                    except Exception:
                        pass
                
                # Save screenshot of the completed form to the screenshots folder
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                sb.save_screenshot(screenshot_path)
                saved_screenshot = screenshot_path
                
                # Human-in-the-loop Submission halt
                print(f"\n[HITL] Form filled for {url}.")
                print(f"[HITL] Screenshot saved at: {saved_screenshot}")
                
                approval = input("Awaiting manual approval to submit. Type 'yes' or 'y' to submit, or anything else to abort: ")
                
                if approval.lower() in ["yes", "y"]:
                    # Find submit button
                    submit_btn = None
                    for selector in ['button[type="submit"]', 'input[type="submit"]']:
                        try:
                            if sb.is_element_visible(selector):
                                submit_btn = sb.driver.find_element("css selector", selector)
                                break
                        except Exception:
                            pass
                    if not submit_btn:
                        try:
                            for btn in sb.driver.find_elements("css selector", "button"):
                                btn_text = btn.text.lower()
                                if "submit" in btn_text or "apply" in btn_text:
                                    submit_btn = btn
                                    break
                        except Exception:
                            pass
                    
                    if submit_btn:
                        try:
                            submit_btn.click()
                        except Exception:
                            # Coordinates-based click fallback
                            rect = sb.execute_script("""
                                let rect = arguments[0].getBoundingClientRect();
                                return {x: rect.left + rect.width / 2, y: rect.top + rect.height / 2};
                            """, submit_btn)
                            try:
                                actions = ActionChains(sb.driver)
                                actions.move_to_location(int(rect["x"]), int(rect["y"])).click().perform()
                            except Exception:
                                sb.execute_script("arguments[0].click();", submit_btn)
                    
                    # Wait for navigation or success page content
                    time.sleep(1.0)
                    
                    content = sb.get_page_source()
                    success = "success" in content.lower() and "error" not in content.lower()
                    message = "Application submitted successfully." if success else f"Application submission failed or returned error. Page Content: {content[:200]}"
                else:
                    success = False
                    message = "Application submission aborted by user."
                
                return {
                    "success": success,
                    "message": message,
                    "screenshot": saved_screenshot
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"SeleniumBase automation encountered an error: {str(e)}",
                "screenshot": None
            }
