def normalize_skill(skill):

    skill = str(skill).lower().strip()

    # Common variations
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

    # Replace hyphens with spaces
    skill = skill.replace("-", " ")

    # Remove extra spaces
    skill = " ".join(skill.split())

    # Apply known replacement
    skill = replacements.get(
        skill,
        skill
    )

    return skill


def skills_match(
    student_skill,
    internship_skill
):

    student = normalize_skill(
        student_skill
    )

    internship = normalize_skill(
        internship_skill
    )


    # --------------------------------
    # Exact match
    # --------------------------------

    if student == internship:

        return True


    # --------------------------------
    # Phrase containment
    # --------------------------------
    #
    # Example:
    #
    # Cybersecurity
    # cybersecurity concepts
    #
    # Network
    # networking
    #
    # --------------------------------

    if (
        student in internship
        or internship in student
    ):

        return True


    return False


def calculate_match(
    student_skills,
    internship_skills
):

    matched_skills = []
    missing_skills = []


    # --------------------------------
    # FIND MATCHED SKILLS
    # --------------------------------

    for student_skill in student_skills:

        for internship_skill in internship_skills:

            if skills_match(
                student_skill,
                internship_skill
            ):

                matched_skills.append(
                    student_skill
                )

                break


    # --------------------------------
    # FIND MISSING SKILLS
    # --------------------------------

    for internship_skill in internship_skills:

        found = False


        for student_skill in student_skills:

            if skills_match(
                student_skill,
                internship_skill
            ):

                found = True

                break


        if not found:

            missing_skills.append(
                internship_skill
            )


    # --------------------------------
    # CALCULATE MATCH %
    # --------------------------------

    if len(internship_skills) > 0:

        match_percentage = (
            len(matched_skills)
            /
            len(internship_skills)
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
