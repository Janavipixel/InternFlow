import requests
from urllib.parse import urlparse


UNWANTED_DOMAINS = [
    "instagram.com",
    "facebook.com",
    "youtube.com",
    "youtu.be",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "pinterest.com",
    "reddit.com",
]

# Signatures in URL indicating expired, generic search, or login walls
UNWANTED_URL_PATTERNS = [
    "/search",
    "/jobs/search",
    "/find-jobs",
    "/login",
    "/signin",
    "/auth",
    "/register",
]


def verify_application_url(url, timeout=2.5):
    """
    Verifies that an application URL is actionable:
    1. Checks for non-empty string and valid HTTP scheme.
    2. Rejects social networks and known dead ends.
    3. Performs an HTTP GET request with sensible headers and timeout.
    4. Validates status code (200-399).
    5. Inspects final redirected URL and initial response content to detect soft 404s,
       expired notices, or login walls.

    Returns:
        bool: True if verified and actionable, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False

    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return False

    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    path = parsed.path.lower()

    for domain in UNWANTED_DOMAINS:
        if domain in netloc:
            return False

    for pattern in UNWANTED_URL_PATTERNS:
        if pattern in path:
            return False

    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
        )

        # Check for successful response
        if 200 <= response.status_code < 400:
            # Check final redirected URL for unwanted patterns (e.g. redirected to login page)
            final_url = response.url.lower()
            if any(d in final_url for d in UNWANTED_DOMAINS):
                return False
            if any(p in final_url for p in ["/login", "/signin", "/auth", "/register"]):
                return False

            # Soft 404 or expired check in the body sample (first 10,000 characters)
            content_sample = response.text[:10000].lower()
            expired_phrases = [
                "this job has expired",
                "this job is no longer available",
                "this opening is closed",
                "applications are closed",
                "page not found",
                "404 not found",
                "job post not found",
                "position has been filled",
            ]
            if any(phrase in content_sample for phrase in expired_phrases):
                return False

            return True

        # Anti-bot / rate-limit detection: Cloudflare, PerimeterX, or Akamai challenges
        # A human student clicking from an email can view the job, but scrapers receive 403/429
        if response.status_code in (401, 403, 429):
            server_header = response.headers.get("server", "").lower()
            cf_ray = "cf-ray" in response.headers
            content_sample = response.text[:4000].lower()
            is_anti_bot = (
                cf_ray
                or "cloudflare" in server_header
                or "just a moment" in content_sample
                or "attention required" in content_sample
                or "access denied" in content_sample
                or "security check" in content_sample
            )
            if is_anti_bot and len(path) > 3 and not any(p in path for p in UNWANTED_URL_PATTERNS):
                return True
            return False

        # Any 404, 410, 5xx server errors indicate dead or broken listing
        return False

    except (requests.RequestException, Exception):
        return False

