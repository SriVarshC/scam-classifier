"""Smoke test + speed check for a deployed scam service (standard library only).

Usage: python3 smoke_test.py https://<domain> <SCAM_SERVICE_TOKEN>
Checks: /healthz, 401 without a token, one scam and one genuine call (prints label, risk and time).
"""
import json
import sys
import time
import urllib.error
import urllib.request

SAMPLES = {
    "scam (bank code + safe account)":
        "hi this is mark from the fraud department at your bank we detected a suspicious transfer of two "
        "thousand dollars to protect your money we need to move it to a secure account right now i just sent "
        "you a verification code please read it back to me and don't tell anyone at the branch about this call",
    "genuine (dentist reminder)":
        "hello this is sarah from bright smile dental calling to remind you of your cleaning appointment on "
        "thursday at 3 pm if you need to reschedule please call our office at the number on our website thanks "
        "and have a great day",
}


def post(base, token, text):
    req = urllib.request.Request(f"{base}/v1/classify", data=json.dumps({"request_id": "smoke", "text": text}).encode(),
                                 headers={"Content-Type": "application/json",
                                          **({"Authorization": f"Bearer {token}"} if token else {})})
    return urllib.request.urlopen(req, timeout=180)


def main(base, token):
    base = base.rstrip("/")
    print("healthz:", urllib.request.urlopen(f"{base}/healthz", timeout=20).read().decode())
    try:
        post(base, None, "test")
        print("WARNING: request without token was accepted")
    except urllib.error.HTTPError as e:
        print("no token ->", e.code, "(expected 401)")
    for name, text in SAMPLES.items():
        t0 = time.time()
        body = json.loads(post(base, token, text).read())
        print(f"\n{name}: {time.time() - t0:.1f}s")
        print("  classes:", body["classes"])
        print("  summary:", body["summary"])
        if body.get("notes"):
            print("  notes:  ", body["notes"])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python3 smoke_test.py https://<domain> <token>")
    main(sys.argv[1], sys.argv[2])
