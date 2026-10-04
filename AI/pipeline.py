import os
import json
from datetime import datetime
from verify_application import verify_application_url
from dotenv import load_dotenv
from tavily import TavilyClient

from gemini_client import ask_gemini
from matching import calculate_match
from stipend import extract_stipend_amount


load_dotenv()


# ========================================
# TEMPORARY TEST MODE
# ========================================
# True  = Gemini ke bina test karega
# False = Actual Gemini API use karega

USE_MOCK_GEMINI = True


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

    tavily_key = os.getenv("TAVILY_API_KEY")

    if not tavily_key:

        print("TAVILY_API_KEY not found.")

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

    print("Searching for internships...")
    print(f"Query: {query}")


    # --------------------------------
    # Tavily search
    # --------------------------------

    response = tavily.search(
        query=query,
        search_depth="advanced",
        max_results=10,
        include_raw_content=True
    )

    results = response.get(
        "results",
        []
    )

    internships = []


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
            result.get("raw_content")
            or result.get("content")
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
        # STEP 3: Gemini prompt
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
        # STEP 4: Gemini / Mock Gemini
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
                    "Mumbai",

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

            except Exception as e:

                print(
                    f"Gemini failed for {url}: {e}"
                )

                continue


        # ========================================
        # STEP 5: Clean Gemini response
        # ========================================

        if isinstance(
            internship,
            str
        ):

            internship = internship.strip()


            # Remove markdown code fences

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


            # Convert JSON string to Python object

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
        # STEP 6: Handle accidental list
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
                "Skipped: Gemini returned invalid object"
            )

            continue


        # ========================================
        # STEP 7: Make sure fields exist
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
        # STEP 8: Basic validation
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
        # STEP 9: Remove closed internships
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
        # STEP 10: Deadline validation
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

                # Unknown date format.
                # Do not reject automatically.

                pass


        # ========================================
        # STEP 11: Stipend filtering
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
        # STEP 12: Location filtering
        # ========================================

        internship_location = str(
            internship["location"]
        ).lower()

        requested_location = location.lower()


        allowed_location = (

            requested_location
            in internship_location

            or "remote"
            in internship_location

            or "india"
            in internship_location

            or "pan india"
            in internship_location

        )


        if not allowed_location:

            print(
                "Skipped: location mismatch"
            )

            continue



        # ========================================
        # STEP 13: Verify application URL
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
        # STEP 14: Skill matching
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
        # STEP 15: Add matching information
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
        # STEP 16: Add final result
        # ========================================

        internships.append(
            internship
        )


        print(
            f"Added: "
            f"{internship['company']} - "
            f"{internship['role']}"
        )


    # ========================================
    # STEP 17: Sort by match percentage
    # ========================================

    internships.sort(

        key=lambda x:
            (
                x["match_percentage"]
                if x["match_percentage"] is not None
                else -1
            ),

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
