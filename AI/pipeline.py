import os
import json
import re
import concurrent.futures
from datetime import datetime

from dotenv import load_dotenv
from tavily import TavilyClient

from AI.verify_application import verify_application_url
from AI.gemini_client import ask_gemini
from AI.matching import calculate_match, normalize_skill, get_display_skill
from AI.stipend import extract_stipend_amount

load_dotenv()


# ========================================
# TEMPORARY TEST MODE
# ========================================

USE_MOCK_GEMINI = False


# ========================================
# GEMINI API LIMIT
# ========================================

MAX_GEMINI_RESULTS = 3


# ========================================
# DEDUPLICATE SKILLS LIST
# ========================================

def deduplicate_skills_list(skills_list):
    """
    Given a list or comma-separated string of skills (from AI extraction or fallback),
    normalizes tokens, deduplicates case variants (e.g. C and c, Python and python),
    and returns a clean list of canonical display names.
    """
    if not skills_list:
        return []
    if isinstance(skills_list, str):
        skills_list = [s.strip() for s in skills_list.split(",") if s.strip()]
    seen = set()
    cleaned = []
    for s in skills_list:
        if not s:
            continue
        norm = normalize_skill(s)
        if norm and norm not in seen:
            seen.add(norm)
            cleaned.append(get_display_skill(s, norm))
    return cleaned


# ========================================
# UNWANTED PAGE FILTER
# ========================================

def is_unwanted_page(url, title):
    url_lower = (url or "").lower()
    title_lower = (title or "").lower()

    unwanted_domains = [
        "indeed.com",
        "quora.com",
        "naukri.com",
        "glassdoor.co.in",
        "glassdoor.com",
        "coursera.org",
        "udemy.com",
        "medium.com",
        "reddit.com",
        "youtube.com",
        "hirist.tech",
        "hlcommission.org",
        "wikipedia.org",
    ]

    unwanted_url_patterns = [
        "/jobs/search",
        "/job-search",
        "/find-jobs",
        "/search",
        "/blog/",
        "/blogs/",
        "/article/",
        "/articles/",
        "/guide/",
        "/guides/",
        "/career-guide/",
        "/q-",
        "/jobs/view-all",
        "/internships/work-from-home",
        "/accreditation/",
    ]

    unwanted_title_words = [
        "guide",
        "how to",
        "top internships",
        "career guide",
        "job vacancies",
        "explore careers",
        "syllabus",
        "curriculum",
        "accreditation",
        "best internships",
        "tips for",
    ]

    for domain in unwanted_domains:
        if domain in url_lower:
            return True, "unwanted domain"

    for pattern in unwanted_url_patterns:
        if pattern in url_lower:
            return True, "generic job/search/article page"

    # Match exact /jobs or /jobs/ landing pages, but allow specific postings like /jobs/123 or /jobs/role-title
    if re.search(r"/jobs/?(?:\?|$)", url_lower):
        return True, "generic job landing page"

    for word in unwanted_title_words:
        if word in title_lower:
            return True, "article/guide/generic page"

    return False, None


# ========================================
# INTERNSHIP CHECK
# ========================================

def looks_like_internship_page(url, title, content):
    text = f"{title} {content}".lower()
    title_lower = (title or "").lower()

    # Must contain intern/trainee/apprentice in title OR explicit internship hiring intent in content
    has_intern_title = any(w in title_lower for w in ["intern", "internship", "trainee", "apprentice"])
    has_intern_content = any(w in text for w in [
        "internship opportunity", "intern role", "intern position",
        "hiring interns", "summer intern", "intern responsibilities",
        "apply for internship", "internship program", "looking for an intern"
    ])

    return has_intern_title or has_intern_content


# ========================================
# REMOVE DUPLICATES
# ========================================

def remove_duplicate_internships(internships):

    unique_internships = []
    seen = set()

    for internship in internships:

        company = str(
            internship.get("company", "")
        ).lower().strip()

        role = str(
            internship.get("role", "")
        ).lower().strip()

        location = str(
            internship.get("location", "")
        ).lower().strip()

        key = (
            company,
            role,
            location
        )

        if key in seen:

            print(
                "Skipped: duplicate internship"
            )

            continue

        seen.add(key)

        unique_internships.append(
            internship
        )

    return unique_internships


# ========================================
# FALLBACK: EXTRACT COMPANY
# ========================================

def extract_company_from_result(title, url, content):

    clean_title = title.strip()

    # --------------------------------
    # Common title separators
    # --------------------------------

    separators = [
        " — ",
        " | ",
        " - ",
        " – ",
        " :: "
    ]

    for separator in separators:

        if separator in clean_title:

            parts = clean_title.split(
                separator
            )

            first_part = parts[0].strip()

            if (
                len(first_part) >= 3
                and len(first_part) <= 100
            ):

                return first_part


    # --------------------------------
    # Try common company phrases
    # --------------------------------

    company_patterns = [

        r"internship\s+at\s+([A-Za-z0-9&.,'() -]{3,80})",

        r"intern\s+at\s+([A-Za-z0-9&.,'() -]{3,80})",

        r"careers\s+at\s+([A-Za-z0-9&.,'() -]{3,80})",

        r"([A-Za-z0-9&.,'() -]{3,80})\s+internship",

    ]

    combined_text = (
        clean_title + " " + content
    )

    for pattern in company_patterns:

        match = re.search(
            pattern,
            combined_text,
            re.IGNORECASE
        )

        if match:

            company = match.group(1).strip()

            # Avoid returning overly long sentences
            company = company.split(".")[0].strip()

            if len(company) >= 3:

                return company


    # --------------------------------
    # Try extracting domain name
    # --------------------------------

    domain_match = re.search(
        r"https?://(?:www\.)?([^/]+)",
        url
    )

    if domain_match:

        domain = domain_match.group(1)

        domain_parts = domain.split(".")

        if domain_parts:

            company = domain_parts[0]

            if company.lower() not in [
                "www",
                "jobs",
                "careers"
            ]:

                return company.replace(
                    "-",
                    " "
                ).title()


    return "Company information unavailable"


# ========================================
# FALLBACK: EXTRACT ROLE
# ========================================

def extract_role_from_result(
    title,
    content,
    preferred_domain
):

    text = (
        title + " " + content
    ).lower()

    # More specific roles first
    role_keywords = [

        "cybersecurity intern",
        "cyber security intern",
        "security intern",

        "software development intern",
        "software developer intern",
        "software engineering intern",
        "software intern",

        "python intern",
        "java intern",

        "web development intern",
        "web developer intern",

        "data science intern",
        "data analyst intern",
        "data intern",

        "machine learning intern",
        "ai intern",

        "cloud intern",
        "devops intern",

        "networking intern",
        "network intern",

        "iot intern",

        "frontend intern",
        "backend intern",
        "full stack intern",
    ]

    for keyword in role_keywords:

        if keyword in text:

            return keyword.title()


    # --------------------------------
    # Domain-based fallback
    # --------------------------------

    if "cybersecurity" in preferred_domain.lower():

        return "Cybersecurity Intern"

    if "software" in preferred_domain.lower():

        return "Software Intern"

    if "data" in preferred_domain.lower():

        return "Data Intern"

    if "python" in preferred_domain.lower():

        return "Python Intern"

    if "web" in preferred_domain.lower():

        return "Web Development Intern"


    return "Internship"


# ========================================
# FALLBACK: EXTRACT SKILLS
# ========================================

def extract_skills_from_result(
    title,
    content,
    student_skills
):
    text = (title + " " + content)
    text_lower = text.lower()

    raw_detected = []

    # Safe regex boundary patterns for special programming languages
    special_patterns = {
        "c": r"(?<![a-zA-Z0-9#+])c(?![a-zA-Z0-9#+])",
        "c++": r"(?<![a-zA-Z0-9])c\+\+(?![a-zA-Z0-9])",
        "c#": r"(?<![a-zA-Z0-9])c\#(?![a-zA-Z0-9])",
        "r": r"(?<![a-zA-Z0-9])r(?![a-zA-Z0-9])",
        "go": r"\b(?:golang|go\s+programming|go\s+developer|go\s+language)\b|(?<![a-zA-Z0-9])go(?:\s*,|\s*\.|\s*\/|\s+and|\s+or)",
    }

    known_skills = [
        "python",
        "java",
        "javascript",
        "typescript",
        "html",
        "css",
        "react",
        "node.js",
        "node",
        "sql",
        "nosql",
        "mongodb",
        "postgresql",
        "mysql",
        "cybersecurity",
        "cyber security",
        "networking",
        "network security",
        "ethical hacking",
        "penetration testing",
        "vulnerability assessment",
        "siem",
        "firewall",
        "linux",
        "git",
        "github",
        "cloud",
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "data science",
        "iot",
        "embedded systems",
        "c",
        "c++",
        "c#",
        "oop",
    ]

    candidates = list(student_skills or []) + known_skills

    for candidate in candidates:
        if not candidate:
            continue
        c_clean = str(candidate).strip()
        c_lower = c_clean.lower()

        if c_lower in special_patterns:
            if re.search(special_patterns[c_lower], text_lower):
                raw_detected.append(c_clean)
        else:
            pattern = r"\b" + re.escape(c_lower) + r"\b"
            if re.search(pattern, text_lower):
                raw_detected.append(c_clean)

    return deduplicate_skills_list(raw_detected)



# ========================================
# FALLBACK: EXTRACT LOCATION
# ========================================

def extract_location_from_result(
    title,
    content,
    requested_location
):

    text = (
        title + " " + content
    )

    text_lower = text.lower()


    # --------------------------------
    # Remote
    # --------------------------------

    if (
        "remote" in text_lower
        or "work from home" in text_lower
        or "wfh" in text_lower
    ):

        return "Remote"


    # --------------------------------
    # Common Indian locations
    # --------------------------------

    indian_locations = [

        "Mumbai",
        "Pune",
        "Delhi",
        "New Delhi",
        "Bangalore",
        "Bengaluru",
        "Hyderabad",
        "Chennai",
        "Kolkata",
        "Ahmedabad",
        "Noida",
        "Gurugram",
        "Gurgaon",
        "Thane",
        "Navi Mumbai",
        "Nagpur",
        "Jaipur",
        "Indore",
        "Chandigarh",
        "Kerala",
        "Maharashtra",
        "India"
    ]

    for city in indian_locations:

        if city.lower() in text_lower:

            return city


    # --------------------------------
    # If Tavily doesn't reveal location
    # --------------------------------

    return "Location not specified"


# ========================================
# FALLBACK: EXTRACT STIPEND
# ========================================

def extract_stipend_from_result(
    content
):

    text = content.lower()

    stipend_patterns = [

        r"₹\s?[\d,]+(?:\s?-\s?₹?\s?[\d,]+)?",

        r"rs\.?\s?[\d,]+(?:\s?-\s?rs\.?\s?[\d,]+)?",

        r"inr\s?[\d,]+(?:\s?-\s?inr?\s?[\d,]+)?",

    ]

    for pattern in stipend_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return match.group(0).strip()


    return ""


# ========================================
# DEADLINE NORMALIZATION & EXTRACTION
# ========================================

def normalize_date(date_text):
    if not date_text:
        return None

    text = str(date_text).strip()
    text = re.sub(r"(\d)(st|nd|rd|th)", r"\1", text, flags=re.IGNORECASE)

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d %Y",
        "%b %d %Y"
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def extract_deadline_from_text(text):
    if not text:
        return None

    text_str = str(text)
    patterns = [
        r"(?:application\s+)?deadline\s*[:\-]?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})",
        r"(?:application\s+)?deadline\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})",
        r"(?:apply\s+by|applications?\s+(?:close|closes|closed|end|ends))\s*[:\-]?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})",
        r"(?:apply\s+by|applications?\s+(?:close|closes|closed|end|ends))\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})",
        r"\b(\d{4}-\d{2}-\d{2})\b",
        r"\b(\d{1,2}/\d{1,2}/\d{4})\b",
        r"\b(\d{1,2}-\d{1,2}-\d{4})\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text_str, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1)
            norm = normalize_date(candidate)
            if norm:
                return norm
    return None


# ========================================
# CLEAN GEMINI RESPONSE
# ========================================

def clean_gemini_response(response):
    if not response:
        return None
    if isinstance(response, dict):
        return response

    text = str(response).strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    try:
        data = json.loads(text)
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
    return None


# ========================================
# TAVILY FALLBACK
# ========================================

def create_tavily_fallback(
    title,
    url,
    content,
    location,
    student_skills,
    preferred_domain
):

    print(
        "Creating structured Tavily fallback..."
    )


    company = extract_company_from_result(
        title,
        url,
        content
    )


    role = extract_role_from_result(
        title,
        content,
        preferred_domain
    )


    skills = extract_skills_from_result(
        title,
        content,
        student_skills
    )


    internship_location = extract_location_from_result(
        title,
        content,
        location
    )


    stipend = extract_stipend_from_result(
        content
    )


    # --------------------------------
    # Application status
    # --------------------------------

    text_lower = (
        title + " " + content
    ).lower()

    if (
        "applications are closed" in text_lower
        or "application closed" in text_lower
        or "applications closed" in text_lower
    ):

        application_status = "closed"

    elif (
        "apply now" in text_lower
        or "applications open" in text_lower
        or "currently hiring" in text_lower
        or "apply for internship" in text_lower
    ):

        application_status = "open"

    else:

        application_status = "unknown"


    return {

        "company":
            company,

        "role":
            role,

        "skills":
            skills,

        "location":
            internship_location,

        "stipend":
            stipend,

        "duration":
            "",

        "deadline":
            extract_deadline_from_text(content) or "",

        "eligibility":
            "",

        "application_url":
            url,

        "posted_date":
            "",

        "application_status":
            application_status
    }


# ========================================
# SINGLE CANDIDATE PROCESSING (PARALLELIZABLE)
# ========================================

def process_single_candidate(result, student_skills, preferred_domain, location, minimum_stipend):
    title = result.get("title", "")
    url = result.get("url", "")
    content = result.get("content") or ""

    print(f"\nProcessing: {title}")

    prompt = f"""
You are extracting structured internship information
from a web page.

Return ONLY ONE valid JSON object.

Do NOT return a JSON array.
Do NOT include markdown.
Do NOT include explanations.

Extract these fields:

{{
    "company": "",
    "role": "",
    "skills": [],
    "location": "",
    "stipend": "",
    "duration": "",
    "deadline": "",
    "eligibility": "",
    "description": "",
    "application_url": "",
    "posted_date": "",
    "application_status": ""
}}

Rules:

1. Return exactly ONE internship object.

2. company:
   Extract the actual company/organization offering the internship. Do not use generic job portal names.

3. role:
   Extract the specific internship title (e.g., 'Cybersecurity Analyst Intern', 'Security Operations Intern').

4. skills:
   Return a list of skills explicitly mentioned for the internship. Do not invent skills.

5. location:
   Extract the physical city/state if mentioned (e.g. 'Mumbai, Maharashtra', 'Pune, Maharashtra', 'Bengaluru').
   If hybrid or remote, specify clearly (e.g. 'Mumbai (Hybrid)', 'Pune (On-site)', 'Remote - Pan India').
   Do not write 'Remote' if a specific city or office location is provided.

6. stipend:
   Extract the exact compensation if mentioned (e.g., '₹15,000/month', '₹20,000 - ₹25,000/month', '$20/hr').
   If not stated, return 'Disclosed on application / Paid'.

7. duration:
   Extract duration (e.g., '3 months', '6 months'). If unspecified, return 'Flexible / 3-6 months'.

8. deadline:
   Extract the application deadline date (YYYY-MM-DD) if explicitly mentioned.
   If hiring continuously, return 'Rolling — Open until filled'.

9. eligibility:
   Extract candidate qualifications (e.g., 'College students, B.Tech/BCA/MCA/B.Sc IT or recent graduates').

10. description:
    Provide a concise 1-2 sentence summary of what the intern will actually work on.

11. application_url:
    Use the direct internship application URL if available. Otherwise use:
    {url}

12. posted_date:
    Extract only if explicitly mentioned.

13. application_status:
    Allowed values: 'open', 'closed', 'unknown'. Use 'open' if currently accepting applications.

IMPORTANT:

Do not invent missing information.

WEB PAGE TITLE:
{title}

SOURCE URL:
{url}

WEB PAGE CONTENT:
{content[:12000]}
"""

    if USE_MOCK_GEMINI:
        print("Using MOCK Gemini response...")
        internship = {
            "company": "Test Cybersecurity Company",
            "role": "Cybersecurity Intern",
            "skills": ["Python", "Cybersecurity", "Networking"],
            "location": location,
            "stipend": "₹15000/month",
            "duration": "6 months",
            "deadline": "",
            "eligibility": "Students with basic cybersecurity knowledge",
            "application_url": url,
            "posted_date": "",
            "application_status": "open"
        }
    else:
        internship_obj = None
        try:
            raw_response = ask_gemini(prompt)
            if raw_response:
                internship_obj = clean_gemini_response(raw_response)
                if (
                    internship_obj
                    and internship_obj.get("company")
                    and internship_obj.get("role")
                ):
                    print("Gemini extracted structured internship details.")
                else:
                    print("Gemini response missing essential fields. Using structured Tavily fallback.")
                    internship_obj = None
            else:
                print("Gemini unavailable. Using structured Tavily fallback.")
        except Exception as error:
            print(f"Gemini processing error: {error}. Using structured Tavily fallback.")

        if not internship_obj:
            internship = create_tavily_fallback(
                title,
                url,
                content,
                location,
                student_skills,
                preferred_domain
            )
        else:
            internship = internship_obj

    fields = [
        "company", "role", "skills", "location", "stipend",
        "duration", "deadline", "eligibility", "application_url",
        "posted_date", "application_status"
    ]
    for field in fields:
        internship.setdefault(field, "")

    if not internship.get("skills"):
        detected_skills = extract_skills_from_result(title, content, student_skills)
        if detected_skills:
            internship["skills"] = detected_skills

    if not internship["company"] or not internship["role"]:
        print("Skipped: company or role not found")
        return None

    if internship["application_status"] == "closed":
        print("Skipped: application closed")
        return None

    deadline = internship.get("deadline")
    if deadline:
        norm_dl = normalize_date(deadline)
        if norm_dl:
            internship["deadline"] = norm_dl
            deadline = norm_dl
    else:
        norm_dl = extract_deadline_from_text(content)
        if norm_dl:
            internship["deadline"] = norm_dl
            deadline = norm_dl

    if deadline:
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
            today = datetime.now().date()
            if deadline_date < today:
                print("Skipped: deadline expired")
                return None
        except ValueError:
            pass

    stipend_amount = extract_stipend_amount(internship["stipend"])
    if stipend_amount is not None and minimum_stipend and stipend_amount < minimum_stipend:
        print("Skipped: stipend below minimum")
        return None

    internship_location = str(internship["location"]).lower().strip()
    requested_location = location.lower().strip()

    CITY_ALIASES = {
        "bengaluru": ["bengaluru", "bangalore", "blr", "karnataka"],
        "bangalore": ["bengaluru", "bangalore", "blr", "karnataka"],
        "mumbai": ["mumbai", "bombay", "navi mumbai", "thane", "maharashtra"],
        "pune": ["pune", "poona", "maharashtra"],
        "delhi ncr": ["delhi", "ncr", "new delhi", "noida", "gurugram", "gurgaon", "faridabad", "ghaziabad"],
        "delhi": ["delhi", "ncr", "new delhi", "noida", "gurugram", "gurgaon"],
        "noida": ["noida", "greater noida", "delhi ncr", "ncr"],
        "gurugram": ["gurugram", "gurgaon", "delhi ncr", "ncr"],
        "hyderabad": ["hyderabad", "secunderabad", "cyberabad", "telangana"],
        "chennai": ["chennai", "madras", "tamil nadu"],
        "kolkata": ["kolkata", "calcutta", "west bengal"],
        "ahmedabad": ["ahmedabad", "gandhinagar", "gujarat"]
    }
    aliases = CITY_ALIASES.get(requested_location, [requested_location])
    matches_alias = any(alias in internship_location for alias in aliases)

    if requested_location == "anywhere in india":
        allowed_location = (internship_location != "")
    elif requested_location == "remote":
        allowed_location = (
            "remote" in internship_location
            or "work from home" in internship_location
            or "wfh" in internship_location
        )
    else:
        allowed_location = (
            matches_alias
            or "remote" in internship_location
            or "pan india" in internship_location
            or "india" in internship_location
            or "hybrid" in internship_location
            or internship_location == "location not specified"
            or not internship_location
        )

    if not allowed_location:
        print("Skipped: location mismatch")
        return None

    application_url = internship.get("application_url", "")
    if not application_url:
        print("Skipped: application URL not found")
        return None

    print(f"Verifying application URL: {application_url}")
    if not verify_application_url(application_url):
        print("Skipped: application URL not reachable")
        return None

    print("Application URL verified.")

    internship["skills"] = deduplicate_skills_list(internship.get("skills", []))
    internship_skills = internship["skills"]
    (
        matched_skills,
        missing_skills,
        match_percentage
    ) = calculate_match(student_skills, internship_skills)

    internship["stipend_amount"] = stipend_amount
    internship["matched_skills"] = matched_skills
    internship["missing_skills"] = missing_skills
    internship["match_percentage"] = match_percentage
    internship["source_url"] = url

    print(f"Added: {internship['company']} - {internship['role']} ({match_percentage}% match)")
    return internship


# ========================================
# MAIN PIPELINE
# ========================================

def search_and_process_internships(
    student_skills,
    preferred_domain,
    location,
    minimum_stipend
):
    student_skills = deduplicate_skills_list(student_skills)

    # --------------------------------
    # Tavily setup
    # --------------------------------

    tavily_key = os.getenv("TAVILY_API_KEY")

    if not tavily_key:
        print("TAVILY_API_KEY not found.")
        return []

    tavily = TavilyClient(api_key=tavily_key)
    current_year = datetime.now().year

    query = f"{preferred_domain} internship {location} apply {current_year}"

    print("Searching for internships...")
    print(f"Query: {query}")

    # --------------------------------
    # Tavily search
    # --------------------------------

    try:
        response = tavily.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_raw_content=False
        )
        results = response.get("results", [])
    except Exception as err:
        print(f"[Pipeline] Tavily search error: {err}")
        return []

    # --------------------------------
    # Filter candidates & run extraction concurrently
    # --------------------------------
    valid_candidates = []
    for result in results:
        t = result.get("title", "")
        u = result.get("url", "")
        c = (result.get("content") or "")

        unwanted, reason = is_unwanted_page(u, t)
        if unwanted:
            print(f"Skipped: {reason}")
            continue

        if not looks_like_internship_page(u, t, c):
            print("Skipped: not clearly internship-related")
            continue

        valid_candidates.append(result)
        if not USE_MOCK_GEMINI and len(valid_candidates) >= MAX_GEMINI_RESULTS:
            break

    if not valid_candidates:
        return []

    internships = []
    if len(valid_candidates) == 1:
        res = process_single_candidate(
            valid_candidates[0],
            student_skills,
            preferred_domain,
            location,
            minimum_stipend
        )
        if res:
            internships.append(res)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(valid_candidates), 3)) as executor:
            future_to_cand = {
                executor.submit(
                    process_single_candidate,
                    cand,
                    student_skills,
                    preferred_domain,
                    location,
                    minimum_stipend
                ): cand for cand in valid_candidates
            }
            for future in concurrent.futures.as_completed(future_to_cand, timeout=18):
                try:
                    res = future.result()
                    if res:
                        internships.append(res)
                except Exception as err:
                    print(f"[Pipeline] Concurrent candidate error: {err}")


    # ========================================
    # STEP 18: Remove duplicates
    # ========================================

    internships = remove_duplicate_internships(
        internships
    )


    # ========================================
    # STEP 19: Sort by match percentage
    # ========================================

    internships.sort(
        key=lambda x: x.get("match_percentage") or 0,
        reverse=True
    )


    return internships


# ========================================
# TEST RUN
# ========================================

if __name__ == "__main__":

    results = search_and_process_internships(

        student_skills=[
            "Python",
            "Cybersecurity",
            "Networking"
        ],

        preferred_domain=
            "Cybersecurity",

        location=
            "Mumbai",

        minimum_stipend=
            5000
    )


    print("\n")
    print("FINAL INTERNSHIPS")
    print("=================")


    if not results:

        print(
            "No suitable internships found."
        )


    else:

        for index, internship in enumerate(
            results,
            start=1
        ):

            print(
                f"\n{index}. "
                f"{internship['company']} - "
                f"{internship['role']}"
            )

            print(
                f"Location: "
                f"{internship['location']}"
            )

            print(
                f"Stipend: "
                f"{internship['stipend']}"
            )

            print(
                f"Match: "
                f"{internship['match_percentage']}%"
            )

            print(
                f"Status: "
                f"{internship['application_status']}"
            )

            print(
                f"Deadline: "
                f"{internship['deadline']}"
            )

            print(
                f"Posted: "
                f"{internship['posted_date']}"
            )

            print(
                f"Application URL: "
                f"{internship['application_url']}"
            )

            print(
                f"Source URL: "
                f"{internship['source_url']}"
            )

            print(
                f"Matched Skills: "
                f"{internship['matched_skills']}"
            )

            print(
                f"Missing Skills: "
                f"{internship['missing_skills']}"
            )

