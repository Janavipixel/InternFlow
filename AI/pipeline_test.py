try:
    from AI.pipeline import search_and_process_internships
except ImportError:
    from pipeline import search_and_process_internships


def run_pipeline_test():
    student_skills = ["Python", "Cybersecurity", "Linux"]
    preferred_domain = "Cybersecurity"
    location = "Mumbai"
    minimum_stipend = 15000

    results = search_and_process_internships(
        student_skills,
        preferred_domain,
        location,
        minimum_stipend
    )

    print("\n================================")
    print("FINAL INTERNSHIP RESULTS")
    print("================================")
    print("Total internships:", len(results))

    for internship in results:
        print("\n--------------------------------")
        print("Company:", internship.get("company"))
        print("Role:", internship.get("role"))
        print("Skills:", internship.get("skills"))
        print("Location:", internship.get("location"))
        print("Stipend:", internship.get("stipend"))
        print("Application URL:", internship.get("application_url"))
        print("Match percentage:", internship.get("match_percentage"))


if __name__ == "__main__":
    run_pipeline_test()