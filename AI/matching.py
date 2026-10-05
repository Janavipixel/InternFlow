def normalize_skill(skill):

    if skill is None:
        return ""

    skill = str(skill).lower().strip()

    replacements = {
        "vulnerability assessments": "vulnerability assessment",
        "penetration testing": "penetration testing",
        "penetration tests": "penetration testing",

        "networking": "network",
        "computer networking": "network",

        "network security": "network security",

        "siem tools": "siem",
        "siem tool": "siem",

        "operating systems": "operating system",

        "firewalls": "firewall",
        "vpns": "vpn",

        "idss/ips": "ids/ips",
        "ids/ips": "ids/ips",
    }

    skill = skill.replace("-", " ")
    skill = " ".join(skill.split())

    skill = replacements.get(
        skill,
        skill
    )

    return skill


def skills_match(student_skill, internship_skill):

    student = normalize_skill(student_skill)
    internship = normalize_skill(internship_skill)

    if not student or not internship:
        return False

    # Exact match
    if student == internship:
        return True

    # Single-letter skills such as C should
    # not use substring matching.
    if len(student) == 1 or len(internship) == 1:
        return False

    # Phrase containment for multi-word skills.
    if (
        student in internship
        or internship in student
    ):
        return True

    return False


def calculate_match(student_skills, internship_skills):

    if not isinstance(student_skills, list):
        student_skills = []

    if not isinstance(internship_skills, list):
        internship_skills = []

    matched_skills = []
    missing_skills = []

    for student_skill in student_skills:

        for internship_skill in internship_skills:

            if skills_match(
                student_skill,
                internship_skill
            ):

                if student_skill not in matched_skills:
                    matched_skills.append(student_skill)

                break

    for internship_skill in internship_skills:

        found = False

        for student_skill in student_skills:

            if skills_match(
                student_skill,
                internship_skill
            ):

                found = True
                break

        if not found and internship_skill not in missing_skills:
            missing_skills.append(internship_skill)

    if len(internship_skills) > 0:

        match_percentage = (
            len(matched_skills)
            / len(internship_skills)
        ) * 100

        match_percentage = round(
            match_percentage,
            2
        )

    else:
        match_percentage = None

    return (
        matched_skills,
        missing_skills,
        match_percentage
    )