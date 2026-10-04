import re


def extract_stipend_amount(stipend):

    if not stipend:
        return None

    stipend = stipend.lower().replace(",", "")

    # ₹20k / 20k

    match = re.search(
        r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*k",
        stipend
    )

    if match:

        amount = float(match.group(1)) * 1000

        return int(amount)

    # ₹20000 / 20000

    match = re.search(
        r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)",
        stipend
    )

    if match:

        amount = float(match.group(1))

        return int(amount)

    return None


if __name__ == "__main__":

    print(extract_stipend_amount("₹20K/mo"))

    print(extract_stipend_amount("₹15,000 per month"))

    print(extract_stipend_amount("20000"))

    print(extract_stipend_amount("Not mentioned"))