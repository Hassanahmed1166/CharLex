"""The fourteen lexical descriptors of Stream II (Table 6 of the paper).

This is the exact definition used for every reported model. Two known
weaknesses are documented in Section 4.2 of the paper and kept here on purpose,
so that the published results can be reproduced:

* ``Max Brand Similarity`` compares each brand with the whole URL using
  ``difflib.SequenceMatcher.quick_ratio``, which ignores character order and
  mainly tracks URL length.
* ``paypal`` and ``ebay`` appear in both SUSPICIOUS and TOP_BRANDS, so
  descriptors 12 and 14 count them twice.
"""
import difflib
import math
import re

TOP_BRANDS = ["google", "paypal", "microsoft", "facebook", "apple", "amazon", "netflix", "instagram",
              "whatsapp", "linkedin", "yahoo", "twitter", "adobe", "dropbox", "wordpress", "ebay"]

SUSPICIOUS = {"secure", "account", "update", "banking", "login", "ebay", "paypal", "signin", "verify",
              "wallet", "crypto", "confirm", "password"}

FEATURE_NAMES = ["URL Length", "Dot Count", "Hyphen Count", "At Symbol", "Digit Count", "Digit Ratio",
                 "Question Mark", "Equals Count", "Ampersand Count", "IP Presence", "Shannon Entropy",
                 "Suspicious Word Count", "Max Brand Similarity", "Brand Hit Count"]

# descriptors stored as floats; all others are integer counts
FLOAT_FEATURES = ("Digit Ratio", "Shannon Entropy", "Max Brand Similarity")

_IP_RE = re.compile(r"(([01]?\d\d?|2[0-4]\d|25[0-5])\.){3}([01]?\d\d?|2[0-4]\d|25[0-5])")


def shannon_entropy(s):
    if not s:
        return 0.0
    freq = {c: s.count(c) / len(s) for c in set(s)}
    return -sum(p * math.log2(p) for p in freq.values())


def extract_descriptors(url):
    """Return the 14 descriptors of one URL, in the order of FEATURE_NAMES.

    The string is lower-cased first. Descriptors are computed on the full
    string, before the truncation to 200 characters used by Stream I.
    """
    url = str(url).lower()
    n = max(len(url), 1)
    digits = sum(c.isdigit() for c in url)
    return [
        len(url),
        url.count("."),
        url.count("-"),
        url.count("@"),
        digits,
        digits / n,
        url.count("?"),
        url.count("="),
        url.count("&"),
        1 if _IP_RE.search(url) else 0,
        shannon_entropy(url),
        sum(1 for w in SUSPICIOUS if w in url),
        max((difflib.SequenceMatcher(None, b, url).quick_ratio() for b in TOP_BRANDS), default=0.0),
        sum(1 for b in TOP_BRANDS if b in url),
    ]
