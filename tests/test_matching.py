import pytest
from AI.matching import normalize_skill, skills_match, calculate_match


def test_normalize_skill_casing_and_duplicates():
    assert normalize_skill("C") == "c"
    assert normalize_skill("c") == "c"
    assert normalize_skill("Python") == "python"
    assert normalize_skill("  JavaScript  ") == "javascript"
    assert normalize_skill(None) == ""
    assert normalize_skill("") == ""


def test_normalize_aliases():
    assert normalize_skill("golang") == "go"
    assert normalize_skill("js") == "javascript"
    assert normalize_skill("k8s") == "kubernetes"
    assert normalize_skill("react.js") == "react"
    assert normalize_skill("penetration tests") == "penetration testing"
    assert normalize_skill("vulnerability assessments") == "vulnerability assessment"


def test_skills_match_distinctions():
    # C vs C++ vs C# vs CSS
    assert skills_match("C", "c") is True
    assert skills_match("C", "C++") is False
    assert skills_match("C", "C#") is False
    assert skills_match("C", "CSS") is False

    # Java vs JavaScript
    assert skills_match("Java", "JavaScript") is False
    assert skills_match("JavaScript", "Java") is False
    assert skills_match("JavaScript", "js") is True

    # Go vs Django vs Algorithms vs MongoDB
    assert skills_match("Go", "Django") is False
    assert skills_match("Go", "Algorithms") is False
    assert skills_match("Go", "MongoDB") is False
    assert skills_match("Go", "golang") is True

    # SQL vs NoSQL
    assert skills_match("SQL", "NoSQL") is False
    assert skills_match("NoSQL", "SQL") is False


def test_skills_match_phrase_boundaries():
    assert skills_match("penetration testing", "advanced penetration testing") is True
    assert skills_match("network security", "network security fundamentals") is True
    # Should not match substring inside another word
    assert skills_match("cloud", "soundcloud") is False


def test_calculate_match_deduplication_and_percentage():
    # Known issue: required skills containing both C and c
    student_skills = ["c"]
    internship_skills = ["C", "c", "Python"]

    matched, missing, percentage = calculate_match(student_skills, internship_skills)
    assert matched == ["C"]
    assert missing == ["Python"]
    # Denominator must be 2 unique skills ("c", "python"), so 1/2 = 50.0%
    assert percentage == 50.0


def test_calculate_match_student_duplicate_skills():
    student_skills = ["Python", "python", "PYTHON"]
    internship_skills = ["Python", "FastAPI"]

    matched, missing, percentage = calculate_match(student_skills, internship_skills)
    assert matched == ["Python"]
    assert missing == ["FastAPI"]
    assert percentage == 50.0


def test_calculate_match_empty_skills():
    # Empty internship skills should return None percentage (Unknown)
    matched, missing, percentage = calculate_match(["Python"], [])
    assert matched == []
    assert missing == []
    assert percentage is None

    # Empty student skills should return 0.0%
    matched, missing, percentage = calculate_match([], ["Python", "Docker"])
    assert matched == []
    assert len(missing) == 2
    assert percentage == 0.0


def test_calculate_match_100_percent():
    student_skills = ["Python", "Docker", "Kubernetes", "AWS"]
    internship_skills = ["python", "k8s", "docker"]

    matched, missing, percentage = calculate_match(student_skills, internship_skills)
    assert len(missing) == 0
    assert percentage == 100.0

