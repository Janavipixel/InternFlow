def normalize_skill(skill):
    return skill.lower().replace(" ", "")


def calculate_match(student_skills, internship_skills):

    matched_skills = []

    for student_skill in student_skills:

        normalized_student_skill = normalize_skill(student_skill)

        for internship_skill in internship_skills:

            normalized_internship_skill = normalize_skill(internship_skill)

            if normalized_student_skill == normalized_internship_skill:
                matched_skills.append(student_skill)
                break

    missing_skills = []

    for internship_skill in internship_skills:

        found = False

        for student_skill in student_skills:

            if normalize_skill(internship_skill) == normalize_skill(student_skill):
                found = True
                break

        if not found:
            missing_skills.append(internship_skill)

    if len(internship_skills) > 0:

        match_percentage = (
            len(matched_skills) / len(internship_skills)
        ) * 100

        match_percentage = round(match_percentage, 2)

    else:

        match_percentage = None

    return matched_skills, missing_skills, match_percentage