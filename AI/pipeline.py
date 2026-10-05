import os
import json
import re
from datetime import datetime

from dotenv import load_dotenv
from tavily import TavilyClient

from AI.verify_application import verify_application_url
from AI.gemini_client import ask_gemini
from AI.matching import calculate_match
from AI.stipend import extract_stipend_amount

load_dotenv()


# ========================================
# TEMPORARY TEST MODE
# ========================================

USE_MOCK_GEMINI = False


# ========================================
# GEMINI API LIMIT
# ========================================

MAX_GEMINI_RESULTS = 5


# ========================================
# UNWANTED PAGE FILTER
# ========================================

def is_unwanted_page(url, title):

    url_lower = url.lower()
    title_lower = title.lower()

    unwanted_domains = [
        "indeed.com",
        "quora.com",
        "naukri.com",
        "linkedin.com",
        "glassdoor.co.in",
        "coursera.org",
    ]

    unwanted_url_patterns = [
        "/jobs",
        "/job-search",
        "/search",
        "/blog/",
        "/article/",
        "/articles/",
        "/guide/",
        "/guides/",
    ]

    unwanted_title_words = [
        "guide",
        "how to",
        "top internships",
        "career guide",
        "jobs -",
        "job vacancies",
        "explore careers",
    ]

    for domain in unwanted_domains:

        if domain in url_lower:
            return True, "unwanted domain"

    for pattern in unwanted_url_patterns:

        if pattern in url_lower:
            return True, "generic job/search/article page"

    for word in unwanted_title_words:

        if word in title_lower:
            return True, "article/guide/generic page"

    return False, None


# ========================================
# INTERNSHIP CHECK
# ========================================

def looks_like_internship_page(url, title, content):

    text = f"{title} {content}".lower()

    internship_keywords = [
        "intern",
        "internship",
        "trainee",
        "student",
        "graduate",
        "apply now",
        "applications open",
        "currently hiring",
    ]

    for keyword in internship_keywords:

        if keyword in text:
            return True

    return False


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

    text = (
        title + " " + content
    ).lower()

    detected_skills = []

    # Skills we specifically understand
    known_skills = [

        "python",
        "java",
        "javascript",
        "html",
        "css",
        "react",
        "node.js",
        "node",
        "sql",
        "mongodb",

        "cybersecurity",
        "cyber security",
        "networking",
        "network security",
        "ethical hacking",

        "linux",
        "git",
        "github",

        "cloud",
        "aws",
        "azure",

        "docker",
        "kubernetes",

        "machine learning",
        "artificial intelligence",
        "data science",

        "iot",
        "embedded systems",

        "c",
        "c++",
        "oop"
    ]


    # --------------------------------
    # First check student's skills
    # --------------------------------

    for skill in student_skills:

        skill_lower = skill.lower().strip()

        if skill_lower in text:

            if skill not in detected_skills:

                detected_skills.append(
                    skill
                )


    # --------------------------------
    # Then detect known skills
    # --------------------------------

    for skill in known_skills:

        if skill in text:

            display_skill = skill

            if skill == "node":
                display_skill = "Node.js"

            elif skill == "cyber security":
                display_skill = "Cybersecurity"

            elif skill == "artificial intelligence":
                display_skill = "AI"

            elif skill == "oop":
                display_skill = "OOP"

            if display_skill not in detected_skills:

                detected_skills.append(
                    display_skill
                )


    return detected_skills


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
            "",

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
# MAIN PIPELINE
# ========================================

def search_and_process_internships(
    student_skills,
    preferred_domain,
    location,
    minimum_stipend
):

    # --------------------------------
    # Tavily setup
    # --------------------------------

    tavily_key = os.getenv(
        "TAVILY_API_KEY"
    )

    if not tavily_key:

        print(
            "TAVILY_API_KEY not found."
        )

        return []

    tavily = TavilyClient(
        api_key=tavily_key
    )

    current_year = datetime.now().year

    query = (
        f"{preferred_domain} internships {location} "
        f"{current_year} currently hiring OR apply now "
        f"OR applications open"
    )

    print(
        "Searching for internships..."
    )

    print(
        f"Query: {query}"
    )


    # --------------------------------
    # Tavily search
    # --------------------------------

    response = tavily.search(
        query=query,
        search_depth="basic",
        max_results=5,
        include_raw_content=False
    )

    results = response.get(
        "results",
        []
    )

    internships = []


    # --------------------------------
    # Gemini request counter
    # --------------------------------

    gemini_results_processed = 0


    # --------------------------------
    # Process results
    # --------------------------------

    for result in results:

        title = result.get(
            "title",
            ""
        )

        url = result.get(
            "url",
            ""
        )

        content = (
            result.get("content")
            or ""
        )

        print(
            f"\nProcessing: {title}"
        )


        # ========================================
        # STEP 1: Remove unwanted pages
        # ========================================

        unwanted, reason = is_unwanted_page(
            url,
            title
        )

        if unwanted:

            print(
                f"Skipped: {reason}"
            )

            continue


        # ========================================
        # STEP 2: Check internship relevance
        # ========================================

        if not looks_like_internship_page(
            url,
            title,
            content
        ):

            print(
                "Skipped: not clearly internship-related"
            )

            continue


        # ========================================
        # STEP 3: Gemini request limit
        # ========================================

        if (
            not USE_MOCK_GEMINI
            and gemini_results_processed
            >= MAX_GEMINI_RESULTS
        ):

            print(
                "Gemini result limit reached."
            )

            break


        if not USE_MOCK_GEMINI:

            gemini_results_processed += 1

            print(
                f"Gemini request "
                f"{gemini_results_processed}/"
                f"{MAX_GEMINI_RESULTS}"
            )


        # ========================================
        # STEP 4: Gemini prompt
        # ========================================

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
    "application_url": "",
    "posted_date": "",
    "application_status": ""
}}

Rules:

1. Return exactly ONE internship object.

2. company:
   Extract the actual company/organization
   offering the internship.

3. role:
   Extract the actual internship role.

4. skills:
   Return a list of skills explicitly mentioned
   for the internship.
   Do not invent skills.

5. location:
   Extract the internship location.
   Use "Remote" if explicitly stated.

6. stipend:
   Extract the stipend/salary if explicitly mentioned.
   Otherwise return "".

7. duration:
   Extract duration only if explicitly mentioned.

8. deadline:
   Extract the application deadline only if explicitly mentioned.
   Do not guess.

9. eligibility:
   Extract eligibility requirements if explicitly mentioned.

10. application_url:
    Use the actual internship application URL if available.
    Otherwise use this source URL:

    {url}

11. posted_date:
    Extract only if explicitly mentioned.

12. application_status:
    Allowed values:
    "open"
    "closed"
    "unknown"

    Use "open" only if the page clearly indicates
    that applications are currently being accepted.

    Use "closed" only if the page explicitly says
    applications are closed, the deadline has passed,
    or applications are no longer being accepted.

    Otherwise use "unknown".

IMPORTANT:

Do not invent missing information.

WEB PAGE TITLE:
{title}

SOURCE URL:
{url}

WEB PAGE CONTENT:
{content[:12000]}
"""


        # ========================================
        # STEP 5: Gemini / Fallback
        # ========================================

        if USE_MOCK_GEMINI:

            print(
                "Using MOCK Gemini response..."
            )

            internship = {

                "company":
                    "Test Cybersecurity Company",

                "role":
                    "Cybersecurity Intern",

                "skills": [
                    "Python",
                    "Cybersecurity",
                    "Networking"
                ],

                "location":
                    location,

                "stipend":
                    "₹15000/month",

                "duration":
                    "6 months",

                "deadline":
                    "",

                "eligibility":
                    "Students with basic cybersecurity knowledge",

                "application_url":
                    url,

                "posted_date":
                    "",

                "application_status":
                    "open"
            }


        else:

            try:

                internship = ask_gemini(
                    prompt
                )


                # ========================================
                # GEMINI UNAVAILABLE
                # ========================================

                if internship is None:

                    print(
                        "Gemini unavailable."
                    )

                    print(
                        "Using structured Tavily fallback."
                    )

                    internship = create_tavily_fallback(
                        title,
                        url,
                        content,
                        location,
                        student_skills,
                        preferred_domain
                    )


                


            except Exception as e:

                print(
                    f"Gemini failed for {url}: {e}"
                )

                error_text = str(e).upper()


                if (
                    "RESOURCE_EXHAUSTED" in error_text
                    or "429" in error_text
                    or "QUOTA" in error_text
                    or "RATE LIMIT" in error_text
                ):

                    print(
                        "Gemini quota/rate limit reached."
                    )

                else:

                    print(
                        "Gemini failed."
                    )


                print(
                    "Using structured Tavily fallback."
                )


                internship = create_tavily_fallback(
                    title,
                    url,
                    content,
                    location,
                    student_skills,
                    preferred_domain
                )


        # ========================================
        # STEP 6: Clean Gemini response
        # ========================================

        if isinstance(
            internship,
            str
        ):

            internship = internship.strip()


            if internship.startswith("```"):

                internship = internship.replace(
                    "```json",
                    ""
                )

                internship = internship.replace(
                    "```",
                    ""
                )

                internship = internship.strip()


            try:

                internship = json.loads(
                    internship
                )

            except json.JSONDecodeError:

                print(
                    "Skipped: Gemini returned invalid JSON"
                )

                continue


        # ========================================
        # STEP 7: Handle accidental list
        # ========================================

        if isinstance(
            internship,
            list
        ):

            if len(internship) == 0:

                print(
                    "Skipped: Gemini returned empty list"
                )

                continue

            internship = internship[0]


        if not isinstance(
            internship,
            dict
        ):

            print(
                "Skipped: invalid internship object"
            )

            continue


        # ========================================
        # STEP 8: Make sure fields exist
        # ========================================

        fields = [

            "company",
            "role",
            "skills",
            "location",
            "stipend",
            "duration",
            "deadline",
            "eligibility",
            "application_url",
            "posted_date",
            "application_status"

        ]


        for field in fields:

            internship.setdefault(
                field,
                ""
            )


        # ========================================
        # STEP 9: Basic validation
        # ========================================

        if (
            not internship["company"]
            or not internship["role"]
        ):

            print(
                "Skipped: company or role not found"
            )

            continue


        # ========================================
        # STEP 10: Remove closed internships
        # ========================================

        if (
            internship["application_status"]
            == "closed"
        ):

            print(
                "Skipped: application closed"
            )

            continue


        # ========================================
        # STEP 11: Deadline validation
        # ========================================

        deadline = internship["deadline"]

        if deadline:

            try:

                deadline_date = datetime.strptime(
                    deadline,
                    "%Y-%m-%d"
                ).date()

                today = datetime.now().date()

                if deadline_date < today:

                    print(
                        "Skipped: deadline expired"
                    )

                    continue

            except ValueError:

                pass


        # ========================================
        # STEP 12: Stipend filtering
        # ========================================

        stipend_amount = extract_stipend_amount(
            internship["stipend"]
        )

        if (
            stipend_amount is not None
            and stipend_amount < minimum_stipend
        ):

            print(
                "Skipped: stipend below minimum"
            )

            continue


        # ========================================
        # STEP 13: Location filtering
        # ========================================

        internship_location = str(
            internship["location"]
        ).lower().strip()

        requested_location = (
            location.lower().strip()
        )


        if requested_location == "anywhere in india":

            allowed_location = (
                internship_location != ""
            )


        elif requested_location == "remote":

            allowed_location = (
                "remote" in internship_location
                or "work from home" in internship_location
                or "wfh" in internship_location
            )


        else:

            allowed_location = (
                requested_location in internship_location
                or "remote" in internship_location
                or "pan india" in internship_location
                or "india" in internship_location
                or internship_location
                == "location not specified"
            )


        if not allowed_location:

            print(
                "Skipped: location mismatch"
            )

            continue


        # ========================================
        # STEP 14: Verify application URL
        # ========================================

        application_url = internship.get(
            "application_url",
            ""
        )

        if not application_url:

            print(
                "Skipped: application URL not found"
            )

            continue


        print(
            f"Verifying application URL: "
            f"{application_url}"
        )


        if not verify_application_url(
            application_url
        ):

            print(
                "Skipped: application URL not reachable"
            )

            continue


        print(
            "Application URL verified."
        )


        # ========================================
        # STEP 15: Skill matching
        # ========================================

        internship_skills = internship[
            "skills"
        ]

        if not isinstance(
            internship_skills,
            list
        ):

            internship_skills = []


        (
            matched_skills,
            missing_skills,
            match_percentage
        ) = calculate_match(

            student_skills,
            internship_skills

        )


        # ========================================
        # STEP 16: Add matching information
        # ========================================

        internship[
            "stipend_amount"
        ] = stipend_amount

        internship[
            "matched_skills"
        ] = matched_skills

        internship[
            "missing_skills"
        ] = missing_skills

        internship[
            "match_percentage"
        ] = match_percentage

        internship[
            "source_url"
        ] = url


        # ========================================
        # STEP 17: Add final result
        # ========================================

        internships.append(
            internship
        )

        print(
            f"Added: "
            f"{internship['company']} - "
            f"{internship['role']} "
            f"({match_percentage}% match)"
        )


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

