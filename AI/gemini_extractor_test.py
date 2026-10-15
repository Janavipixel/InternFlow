try:
    from AI.gemini_client import ask_gemini
except ImportError:
    from gemini_client import ask_gemini


def run_extractor_test():
    internship_text = """
    Quantiphi is hiring a Cyber Security Intern in Mumbai.
    The internship duration is 6 months and the stipend is ₹20,000 per month.
    Candidates should have knowledge of cybersecurity, networking and Linux.
    Apply online through the company's application page.
    """

    prompt = f"""
    Extract the internship information from the text below.

    Return ONLY JSON with these fields:
    company, role, skills, location, stipend, duration, deadline, eligibility, application_url

    Internship text:
    {internship_text}
    """

    result = ask_gemini(prompt)
    print(result)


if __name__ == "__main__":
    run_extractor_test()