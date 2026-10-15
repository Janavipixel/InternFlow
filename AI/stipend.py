import re


def extract_stipend_amount(stipend):
    """
    Extracts a numeric monthly stipend value from a freeform text string.
    Properly differentiates between:
    - Currency prefixes (₹, Rs, INR, $, USD)
    - Abbreviations like 'k' (e.g., 20k -> 20,000)
    - Full numbers with commas (e.g., 15,000)
    - Durations (e.g., "3 months", "6 months") which should NOT be parsed as stipend amounts.
    - Explicit unpaid/free/performance-based indicators.

    Returns:
        int: Normalized monthly stipend amount if detected.
        0: If expressly unpaid / volunteer.
        None: If unknown or not specified.
    """
    if not stipend:
        return None

    raw_text = str(stipend).strip()
    text = raw_text.lower()

    # Check for unpaid / voluntary keywords
    if any(keyword in text for keyword in ["unpaid", "volunteer", "no stipend", "0/month", "nil", "expenses only"]):
        return 0

    # Remove commas in numbers like 15,000
    cleaned = re.sub(r"(\d),(\d)", r"\1\2", text)

    # 1. Look for 'k' notation with or without currency symbol: e.g. "₹20k", "20k/mo", "Rs. 15k"
    # Ensure it's not preceded/followed by words that invalidate it
    k_match = re.search(r"(?:₹|rs\.?|inr|\$)?\s*(\d+(?:\.\d+)?)\s*k\b", cleaned)
    if k_match:
        try:
            val = float(k_match.group(1)) * 1000
            return int(val)
        except (ValueError, TypeError):
            pass

    # 2. Look for numbers explicitly accompanied by currency symbol or salary/stipend keywords
    # e.g., "₹ 15000 / month", "INR 25000", "Rs 8000"
    currency_match = re.search(r"(?:₹|rs\.?|inr|\$)\s*(\d+)", cleaned)
    if currency_match:
        try:
            val = int(currency_match.group(1))
            # Stipends are usually >= 500
            if val >= 500:
                return val
        except (ValueError, TypeError):
            pass

    # 3. Look for number followed by monthly indicator: "15000 / month", "10000 per mo"
    monthly_match = re.search(r"(\d+)\s*(?:/|\s*per\s*)(?:month|mo|pm)\b", cleaned)
    if monthly_match:
        try:
            val = int(monthly_match.group(1))
            if val >= 500:
                return val
        except (ValueError, TypeError):
            pass

    # 4. If string is JUST a number or range, e.g. "20000" or "15000 - 20000"
    # Reject strings that look like duration e.g. "3 months", "2 to 4 months", "6 weeks"
    if re.search(r"\b(?:month|months|week|weeks|day|days|year|years|hrs|hours)\b", text):
        # Has duration words but no currency or monthly indicator!
        return None

    pure_num = re.search(r"\b(\d{4,6})\b", cleaned)
    if pure_num:
        try:
            return int(pure_num.group(1))
        except (ValueError, TypeError):
            pass

    return None