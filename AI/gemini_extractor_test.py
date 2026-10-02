from gemini_client import ask_gemini

internship_text = """
Quantiphi is hiring a Cyber Security Intern in Mumbai.
The internship duration is 6 months and the stipend is ₹20,000 per month.
Candidates should have knowledge of cybersecurity, networking and Linux.
Apply online through the company's application page.
"""

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
- If something is not mentioned, use "Not mentioned".
- skills should be a list.
- Return valid JSON only.

Internship text:
{internship_text}
"""

result = ask_gemini(prompt)

print(result)