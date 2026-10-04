import requests


def verify_application_url(url):

    if not url:
        return False

    # --------------------------------
    # Reject social-media URLs
    # --------------------------------

    unwanted_domains = [
        "instagram.com",
        "facebook.com",
        "youtube.com",
        "youtu.be",
        "twitter.com",
        "x.com",
        "tiktok.com"
    ]

    url_lower = url.lower()

    for domain in unwanted_domains:

        if domain in url_lower:

            return False


    # --------------------------------
    # Check whether URL is reachable
    # --------------------------------

    try:

        response = requests.get(
            url,
            timeout=10,
            allow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        if 200 <= response.status_code < 400:

            return True

        return False


    except requests.RequestException:

        return False

