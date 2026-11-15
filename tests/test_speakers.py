"""Two-speaker calls from the transcription API ("Caller: ..." = other party, "Receiver: ..." = the user)."""
from call_analysis.flags import RED_FLAGS, _f01_accept, find_phrase

RISKY = "Read me the six digit code we texted you right now and do not tell anyone, or your account will be frozen today."
CALM = "Hi, this is your bank calling about a recent charge. Can you confirm whether you made it?"
F01 = [p for f, _, _, p in RED_FLAGS if f == "F01"][0]


def test_red_flags_only_on_the_callers_lines(service):
    by_caller = service.analyze(f"Caller: {RISKY}\nReceiver: Um, okay, who is this?", "s1")
    by_user = service.analyze(f"Caller: {CALM}\nReceiver: {RISKY}", "s2")
    assert {"F01", "F12", "F13"} <= {f["id"] for f in by_caller["red_flags"]}
    assert by_user["red_flags"] == []
    assert any("Caller's lines only" in n for n in by_user["notes"])


def test_unlabelled_text_checks_every_line(service):
    out = service.analyze(f"{CALM} {RISKY}", "s3")
    assert "F01" in {f["id"] for f in out["red_flags"]}
    assert any("checked on every line" in n for n in out["notes"])


def test_f01_catches_digit_code_wordings_but_not_zip_codes():
    hit = lambda t: bool(find_phrase(t, F01, accept=_f01_accept))  # noqa: E731
    assert hit("Read me the six digit code we texted you")
    assert hit("give me the four digit code on your screen")
    assert hit("what's the code we texted you")
    assert not hit("can you please just tell me the zip code again")
    assert not hit("read me the promo code")
    assert not hit("we texted you a six digit code, never share it with anyone")
