from pipeline import search_and_process_internships


# --------------------------------
# Temporary student information
# --------------------------------

student_skills = [
    "Python",
    "Cybersecurity",
    "Linux"
]

preferred_domain = "Cybersecurity"

location = "Mumbai"

minimum_stipend = 15000


# --------------------------------
# Run AI pipeline
# --------------------------------

results = search_and_process_internships(
    student_skills,
    preferred_domain,
    location,
    minimum_stipend
)


# --------------------------------
# Display results
# --------------------------------

print("\n================================")
print("FINAL INTERNSHIP RESULTS")
print("================================")

print("Total internships:", len(results))


for internship in results:

    print("\n--------------------------------")

    print("Company:", internship["company"])

    print("Role:", internship["role"])

    print("Skills:", internship["skills"])

    print("Location:", internship["location"])

    print("Stipend:", internship["stipend"])

    print("Stipend amount:", internship["stipend_amount"])

    print("Duration:", internship["duration"])

    print("Deadline:", internship["deadline"])

    print("Eligibility:", internship["eligibility"])

    print("Application URL:", internship["application_url"])

    print("Matched skills:", internship["matched_skills"])

    print("Missing skills:", internship["missing_skills"])

    print("Match percentage:", internship["match_percentage"])