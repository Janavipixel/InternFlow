import os
import json

from dotenv import load_dotenv
from tavily import TavilyClient

from gemini_client import ask_gemini
from matching import calculate_match
from stipend import extract_stipend_amount


load_dotenv()


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

    tavily_client = TavilyClient(
        api_key=tavily_key
    )


    # --------------------------------
    # Dynamic search query
    # --------------------------------

    search_query = f"{preferred_domain} internships {location}"

    response = tavily_client.search(
        search_query,
        include_raw_content=True
    )


    # --------------------------------
    # Store processed internships
    # --------------------------------

    processed_internships = []


    # --------------------------------
    # Process every Tavily result
    # --------------------------------

    for result in response["results"]:

        title = result["title"]
        content = result["content"]
        url = result["url"]


        # --------------------------------
        # Basic result filtering
        # --------------------------------

        skip_domains = [
            "indeed.com",
            "quora.com",
            "naukri.com",
            "linkedin.com",
            "glassdoor.co.in"
        ]

        skip_url_patterns = [
            "/jobs",
            "/job-search",
            "/search",
            "/internships/cyber-security-internship"
        ]

        lower_url = url.lower()


        if any(domain in lower_url for domain in skip_domains):
            continue


        if any(pattern in lower_url for pattern in skip_url_patterns):
            continue


        # --------------------------------
        # Use raw content if available
        # --------------------------------

        raw_content = result.get("raw_content")

        if raw_content:
            internship_content = raw_content
        else:
            internship_content = content


        # --------------------------------
        # Gemini prompt
        # --------------------------------

        prompt = f"""
        Extract the internship information from the text below.

        Return ONLY JSON with these fields:

        company
        role
        skills
        location
        stipend
        duration
        deadline
        eligibility
        application_url

        Rules:

        - Do not guess information.
        - Extract skills only from the actual internship description,
          requirements, qualifications, responsibilities, or technologies
          mentioned for this internship.
        - Ignore skills and information belonging to similar internships,
          recommendations, advertisements, or other companies.
        - If specific skills are mentioned anywhere in the actual internship
          description, include them in the skills list.
        - If no specific skills are mentioned for this internship,
          use an empty list [].
        - skills must always be a list.
        - Return valid JSON only.

        Internship title:
        {title}

        Internship content:
        {internship_content}

        Application URL:
        {url}
        """


        # --------------------------------
        # Gemini extraction
        # --------------------------------

        result_from_gemini = ask_gemini(prompt)


        # --------------------------------
        # Clean Gemini response
        # --------------------------------

        clean_json = (
            result_from_gemini
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )


        # --------------------------------
        # JSON → Python dictionary
        # --------------------------------

        internship = json.loads(clean_json)


        # --------------------------------
        # Extract stipend amount
        # --------------------------------

        stipend_amount = extract_stipend_amount(
            internship["stipend"]
        )


        # --------------------------------
        # Stipend filtering
        # --------------------------------

        if stipend_amount is not None:

            if stipend_amount < minimum_stipend:
                continue


        # --------------------------------
        # Location filtering
        # --------------------------------

        internship_location = internship["location"]

        allowed_locations = [
            location.lower(),
            "remote",
            "india",
            "pan india"
        ]


        if internship_location:

            internship_location_lower = internship_location.lower()

            location_match = any(
                allowed in internship_location_lower
                for allowed in allowed_locations
            )

            if not location_match:
                continue


        # --------------------------------
        # Validate internship
        # --------------------------------

        if not internship["company"] or not internship["role"]:
            continue


        # --------------------------------
        # Matching
        # --------------------------------

        internship_skills = internship["skills"]

        matched, missing, percentage = calculate_match(
            student_skills,
            internship_skills
        )


        # --------------------------------
        # Add calculated information
        # --------------------------------

        internship["stipend_amount"] = stipend_amount

        internship["matched_skills"] = matched

        internship["missing_skills"] = missing

        internship["match_percentage"] = percentage


        # --------------------------------
        # Store internship
        # --------------------------------

        processed_internships.append(
            internship
        )


    # --------------------------------
    # Return final results
    # --------------------------------

    return processed_internships