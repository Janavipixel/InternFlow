import re


# Canonical dictionary for formatting display names
CANONICAL_DISPLAY = {
    "c": "C",
    "c++": "C++",
    "c#": "C#",
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "go": "Go",
    "rust": "Rust",
    "ruby": "Ruby",
    "php": "PHP",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "r": "R",
    "sql": "SQL",
    "nosql": "NoSQL",
    "html": "HTML",
    "css": "CSS",
    "react": "React",
    "node.js": "Node.js",
    "vue.js": "Vue.js",
    "angular": "Angular",
    "django": "Django",
    "flask": "Flask",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "git": "Git",
    "github": "GitHub",
    "linux": "Linux",
    "mongodb": "MongoDB",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "redis": "Redis",
    "networking": "Networking",
    "network security": "Network Security",
    "cybersecurity": "Cybersecurity",
    "penetration testing": "Penetration Testing",
    "vulnerability assessment": "Vulnerability Assessment",
    "siem": "SIEM",
    "ids/ips": "IDS/IPS",
    "firewall": "Firewall",
    "vpn": "VPN",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "artificial intelligence": "Artificial Intelligence",
    "data science": "Data Science",
}

# Known aliases mapping to normalized canonical token
SKILL_ALIASES = {
    "golang": "go",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "vue": "vue.js",
    "vuejs": "vue.js",
    "k8s": "kubernetes",
    "postgres": "postgresql",
    "pen testing": "penetration testing",
    "penetration tests": "penetration testing",
    "vulnerability assessments": "vulnerability assessment",
    "network": "networking",
    "computer networking": "networking",
    "operating systems": "operating system",
    "firewalls": "firewall",
    "vpns": "vpn",
    "siem tool": "siem",
    "siem tools": "siem",
    "idss/ips": "ids/ips",
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "artificial intelligence",
}


def normalize_skill(skill):
    """
    Normalizes a skill string:
    - Strips whitespace and lowers casing
    - Preserves crucial symbols like ++ and # (C++, C#) and dots in node.js
    - Standardizes hyphens to spaces (except in special constructs)
    - Maps recognized aliases to canonical tokens
    """
    if skill is None:
        return ""

    skill_str = str(skill).strip().lower()
    if not skill_str:
        return ""

    # Replace hyphens with spaces for general words, but keep c++ / c# intact
    skill_clean = re.sub(r"\s+", " ", skill_str)

    # Check alias lookup first (e.g. "node.js", "pen testing")
    if skill_clean in SKILL_ALIASES:
        return SKILL_ALIASES[skill_clean]

    # Normalize hyphens
    skill_no_hyphen = skill_clean.replace("-", " ")
    skill_no_hyphen = " ".join(skill_no_hyphen.split())

    if skill_no_hyphen in SKILL_ALIASES:
        return SKILL_ALIASES[skill_no_hyphen]

    return skill_no_hyphen


def get_display_skill(raw_skill, normalized_skill):
    """
    Returns canonical display casing for a skill.
    Prefers predefined canonical names, otherwise falls back to title-cased raw skill.
    """
    if normalized_skill in CANONICAL_DISPLAY:
        return CANONICAL_DISPLAY[normalized_skill]
    if raw_skill and isinstance(raw_skill, str) and raw_skill.strip():
        # Preserve original if already had intentional casing
        cleaned = raw_skill.strip()
        if any(c.isupper() for c in cleaned):
            return cleaned
        return cleaned.title()
    return normalized_skill.title()


def skills_match(student_skill, internship_skill):
    """
    Checks if a student skill matches an internship requirement.
    Uses exact token matching or whole-phrase boundary matching to prevent false positives:
    - C does NOT match CSS, Cloud, C++, C#
    - Java does NOT match JavaScript
    - Go does NOT match Django, MongoDB, Algorithms
    - SQL does NOT match NoSQL
    """
    s_norm = normalize_skill(student_skill)
    i_norm = normalize_skill(internship_skill)

    if not s_norm or not i_norm:
        return False

    # Exact normalized match
    if s_norm == i_norm:
        return True

    # Critical language distinctions: Never match across these
    distinct_languages = {"c", "c++", "c#", "java", "javascript", "r", "go", "sql", "nosql", "html", "css"}
    if s_norm in distinct_languages or i_norm in distinct_languages:
        # If either is in distinct_languages and they didn't exact match, reject!
        return False

    # For multi-word terms, allow matching if one is a complete sub-phrase with word boundaries
    # e.g., "penetration testing" matches "web application penetration testing"
    # But "cloud" must match "\bcloud\b", not "soundcloud"
    pattern = r"\b" + re.escape(s_norm) + r"\b"
    if re.search(pattern, i_norm):
        return True

    pattern_rev = r"\b" + re.escape(i_norm) + r"\b"
    if re.search(pattern_rev, s_norm):
        return True

    return False


def calculate_match(student_skills, internship_skills):
    """
    Compares student skills against internship requirements:
    - Deduplicates both student and internship skill lists
    - Handles case variants (C vs c, Python vs python) properly
    - Denominator is strictly the count of unique required internship skills
    - Returns: (matched_skills_display, missing_skills_display, match_percentage)
    - match_percentage is None when internship has no required skills (Unknown)
    """
    if not isinstance(student_skills, (list, tuple, set)):
        student_skills = []
    if not isinstance(internship_skills, (list, tuple, set)):
        internship_skills = []

    # Map normalized token -> canonical display for student skills
    student_map = {}
    for s in student_skills:
        if s is None:
            continue
        norm = normalize_skill(s)
        if norm and norm not in student_map:
            student_map[norm] = get_display_skill(s, norm)

    # Map normalized token -> canonical display for internship skills (deduplicated)
    internship_map = {}
    for req in internship_skills:
        if req is None:
            continue
        norm = normalize_skill(req)
        if norm and norm not in internship_map:
            internship_map[norm] = get_display_skill(req, norm)

    unique_required_count = len(internship_map)
    if unique_required_count == 0:
        return ([], [], None)

    matched_tokens = set()
    matched_skills = []
    missing_skills = []

    # Check each unique required skill against student's skills
    for req_norm, req_display in internship_map.items():
        is_matched = False
        for s_norm, s_display in student_map.items():
            if skills_match(s_norm, req_norm):
                is_matched = True
                matched_tokens.add(req_norm)
                # Show the skill with canonical display
                display_name = req_display
                if display_name not in matched_skills:
                    matched_skills.append(display_name)
                break

        if not is_matched:
            if req_display not in missing_skills:
                missing_skills.append(req_display)

    match_percentage = round((len(matched_tokens) / unique_required_count) * 100, 2)

    return (matched_skills, missing_skills, match_percentage)