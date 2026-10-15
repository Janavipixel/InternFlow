import pytest
from AI.pipeline import (
    is_unwanted_page,
    looks_like_internship_page,
    normalize_date,
    extract_deadline_from_text,
    clean_gemini_response,
    create_tavily_fallback,
    remove_duplicate_internships,
)


def test_is_unwanted_page():
    # Unwanted domain
    unwanted, reason = is_unwanted_page("https://www.indeed.com/viewjob?id=123", "Python Intern")
    assert unwanted is True
    assert "domain" in reason

    # Generic search URL
    unwanted, reason = is_unwanted_page("https://company.com/jobs/search?q=intern", "Search Jobs")
    assert unwanted is True

    # Guide/article title
    unwanted, reason = is_unwanted_page("https://blog.example.com/post/1", "Complete Guide to Internships 2026")
    assert unwanted is True

    # Valid specific posting
    unwanted, reason = is_unwanted_page("https://careers.company.com/posting/4567", "Software Engineer Intern")
    assert unwanted is False
    assert reason is None


def test_looks_like_internship_page():
    assert looks_like_internship_page("https://site.com", "Software Engineer Intern", "Applications open for summer") is True
    assert looks_like_internship_page("https://site.com", "Cooking Recipes", "Delicious pasta recipes") is False


def test_normalize_date():
    assert normalize_date("2026-10-31") == "2026-10-31"
    assert normalize_date("31-10-2026") == "2026-10-31"
    assert normalize_date("31/10/2026") == "2026-10-31"
    assert normalize_date("October 31, 2026") == "2026-10-31"
    assert normalize_date("Oct 31, 2026") == "2026-10-31"
    assert normalize_date("31st October 2026") == "2026-10-31"
    assert normalize_date("invalid-date") is None
    assert normalize_date(None) is None


def test_extract_deadline_from_text():
    sample1 = "Applications for this role will close on Deadline: 30th November 2026. Please apply early."
    assert extract_deadline_from_text(sample1) == "2026-11-30"

    sample2 = "Apply by 15-12-2026 to be considered."
    assert extract_deadline_from_text(sample2) == "2026-12-15"

    sample3 = "No deadline stated anywhere in this paragraph."
    assert extract_deadline_from_text(sample3) is None


def test_clean_gemini_response_variations():
    # Clean JSON string
    raw1 = '{"company": "Google", "role": "SWE Intern"}'
    assert clean_gemini_response(raw1) == {"company": "Google", "role": "SWE Intern"}

    # Markdown code fences
    raw2 = '```json\n{"company": "Microsoft", "role": "Cloud Intern"}\n```'
    assert clean_gemini_response(raw2) == {"company": "Microsoft", "role": "Cloud Intern"}

    # Extra conversational prose around JSON
    raw3 = 'Here is the extracted data:\n{"company": "Amazon", "role": "SDE Intern"}\nHope this helps!'
    assert clean_gemini_response(raw3) == {"company": "Amazon", "role": "SDE Intern"}

    # Invalid JSON
    assert clean_gemini_response("Not valid JSON at all") is None
    assert clean_gemini_response(None) is None


def test_create_tavily_fallback():
    title = "Stripe — Software Engineering Intern"
    url = "https://stripe.com/jobs/123"
    content = "Stripe is hiring a Software Engineering Intern in Bengaluru. Requires Python and SQL. Stipend ₹25,000/month. Apply now."
    res = create_tavily_fallback(
        title=title,
        url=url,
        content=content,
        location="Bengaluru",
        student_skills=["Python", "SQL"],
        preferred_domain="Software Engineering",
    )
    assert res["company"] == "Stripe"
    assert "Intern" in res["role"]
    assert "Python" in res["skills"] or "python" in [s.lower() for s in res["skills"]]
    assert res["application_status"] == "open"
    assert res["application_url"] == url


def test_remove_duplicate_internships():
    listings = [
        {"company": "Amazon", "role": "SDE Intern", "location": "Bangalore", "id": 1},
        {"company": "amazon", "role": "sde intern", "location": " bangalore ", "id": 2},
        {"company": "Google", "role": "SWE Intern", "location": "Bangalore", "id": 3},
    ]
    unique = remove_duplicate_internships(listings)
    assert len(unique) == 2
    assert unique[0]["company"] == "Amazon"
    assert unique[1]["company"] == "Google"


def test_deduplicate_skills_list():
    from AI.pipeline import deduplicate_skills_list
    raw = ["C", "c", "Python", "python", "JavaScript", "js", "Node.js", "node"]
    cleaned = deduplicate_skills_list(raw)
    assert cleaned == ["C", "Python", "JavaScript", "Node.js"]


def test_extract_skills_boundary_safety():
    from AI.pipeline import extract_skills_from_result
    # Text with words containing 'c' like cybersecurity, cloud, react
    # Should NOT falsely extract the programming language 'C'
    text1 = "We are seeking an intern with knowledge of cybersecurity and cloud computing."
    skills1 = extract_skills_from_result("Security Role", text1, ["Python"])
    assert "C" not in skills1
    assert "Cybersecurity" in skills1
    assert "Cloud" in skills1

    # Text that explicitly lists C and C++
    text2 = "Requirements: proficiency in C, C++, and Python."
    skills2 = extract_skills_from_result("Systems Engineer Intern", text2, ["Python"])
    assert "C" in skills2
    assert "C++" in skills2
    assert "Python" in skills2


def test_extract_location_from_result():
    from AI.pipeline import extract_location_from_result
    # Remote detection
    assert extract_location_from_result("SWE Intern", "This position is 100% remote / work from home.", "Mumbai") == "Remote"
    # City detection
    assert extract_location_from_result("Analyst Intern", "Internship based at our Pune tech center.", "Pune") == "Pune"
    assert extract_location_from_result("Software Intern", "Location: Bengaluru office", "Bengaluru") == "Bengaluru"

