"""Keyword rules that assign a fraud type (F0–F9) to each robocall transcript.

Rules are checked in order; the first match wins. Unmatched rows get UNK and are
excluded from training/eval until a human reviews them.

Usage (writes a review sample): python src/label_robocall.py
"""
import re

import pandas as pd

from config import PROCESSED, RAW, SEED, UNKNOWN

# (fraud_type, rule_name, regex) — order matters
RULES = [
    ("F0", "benign_notice", r"\btest call\b|\bstay home\b|\bstay safe\b|\bvote\b|\bsurvey\b|\bappointment reminder\b"),
    ("F8", "family_emergency", r"\bgrandpa\b|\bgrandma\b|grandson|granddaughter"),
    ("F3", "gov_ssa", r"social (security|insurance)|\bssn\b|\bssa\b|our department|legal action|case file"
                      r"|about (your|this) case|discuss your case"),
    ("F3", "gov_tax", r"\birs\b|internal revenue|back tax|\btax(es)?\b"),
    ("F3", "gov_law", r"customs|border protection|\bofficer\b|\bwarrant\b|\barrest|legal department|law enforcement"
                      r"|\bpolice\b|\bsheriff\b|federal|government|department of|\bftc\b|consulate|embassy"
                      r"|state of texas|under your name|discuss your case|medicare"),
    ("F4", "biz_retail", r"\bamazon\b|\bapple\b|\biphone\b|airpods|\bwalmart\b|\bebay\b|order (has been |was )?placed"
                         r"|pre.?authori[sz]ed order"),
    ("F4", "biz_tech", r"microsoft|windows|computer|\bvirus\b|tech(nical)? support|geek squad|norton|mcafee"
                       r"|subscription|auto.?renew"),
    ("F4", "biz_utility_telecom", r"spectrum|directv|\bdish\b|at ?& ?t|verizon|t.?mobile|comcast|xfinity"
                                  r"|electric|utility|\bpower (bill|company)\b|gas bill"),
    ("F4", "biz_warranty", r"warranty"),
    ("F1", "financial", r"\bbank\b|credit card|card ?services|card ?member|interest rate|\bvisa\b|mastercard"
                        r"|\bchase\b|wells fargo|\bfargo\b|bank of america|\bzelle\b|paypal|\bcash ?app\b"
                        r"|\bdiscover\b|rate (reduction|expiration)"),
    ("F4", "biz_billing_delivery", r"cancel (your |the )?(order|payment)|been charged|purchase|customer service"
                                   r"|disconnection|interruption|delinquent account|billing department|past due"
                                   r"|\bfedex\b|\bups\b|\bdhl\b|parcel|package|discounts? on your account"
                                   r"|support team"),
    ("F0", "home_services_telemarketing", r"home ?project|home improvement|solar"),
    ("F9", "debt_relief", r"processing center|reviewing your file|student loan"),
    ("F9", "prize_job_fee", r"\bwon\b|winner|\bprize\b|congratulations|complimentary|free (vacation|cruise|trip|stay)"
                            r"|\bcruise\b|vacation|\bgrant\b|\bhiring\b|\bjob\b|work from home|\bloan\b|\bdebt\b"
                            r"|gift card|\breward\b|qualified|been selected"),
]
_COMPILED = [(ft, name, re.compile(rx, re.I)) for ft, name, rx in RULES]


def label_transcript(text):
    """Return (fraud_type, rule_name) for one transcript."""
    for ft, name, rx in _COMPILED:
        if rx.search(text or ""):
            return ft, name
    return UNKNOWN, "no_match"


def label_frame(df, text_col="transcript"):
    out = df[text_col].fillna("").map(label_transcript)
    return df.assign(fraud_type=[o[0] for o in out], label_rule=[o[1] for o in out])


if __name__ == "__main__":
    meta = pd.read_csv(RAW / "robocall" / "metadata.csv")
    meta = label_frame(meta[meta.language == "en"])
    print(meta.fraud_type.value_counts().to_string(), "\n")
    print(meta.label_rule.value_counts().to_string())
    PROCESSED.mkdir(parents=True, exist_ok=True)
    review = meta.sample(40, random_state=SEED)[["file_name", "fraud_type", "label_rule", "transcript"]]
    review.to_csv(PROCESSED / "robocall_label_review.csv", index=False)
    print(f"\nreview sample -> {PROCESSED / 'robocall_label_review.csv'}")
