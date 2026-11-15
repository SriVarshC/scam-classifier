"""Shared flagged-caller list: signed single-use tickets, hashed caller ids, public endpoints."""
import sqlite3

import pytest
from fastapi.testclient import TestClient

from conftest import TOKEN, FakeLLM
from service.callers import CallerRegistry, normalise_caller

SECRET = "x" * 40
SCAM = ("Caller: This is your bank fraud department. Your account is locked. Read me the six digit code we "
        "texted you right now and do not tell anyone, or your account will be frozen today.\nReceiver: okay")
ORIGIN = "https://sumit2015saurabh-tech.github.io"


@pytest.fixture
def reg(tmp_path):
    return CallerRegistry(SECRET, tmp_path / "callers.db")


@pytest.fixture
def client(reg):
    from service.app import create_app
    from service.pipeline import ScamService
    svc = ScamService(llm=FakeLLM(), callers=reg)
    return TestClient(create_app(service=svc, token=TOKEN)), svc


def test_normalise_caller():
    assert normalise_caller("+1 (555) 123-4567") == normalise_caller("15551234567") == "+15551234567"
    assert normalise_caller("0091 98765 43210") == "+919876543210"
    assert normalise_caller("WA:LID:12345") == "wa:lid:12345"
    assert normalise_caller("12") == "" and normalise_caller("") == ""


def test_fraud_ticket_flags_caller_and_check_finds_it(reg):
    t = reg.issue_ticket("fraud", "F1", 92)
    assert len("report:" + t) <= 100
    assert reg.check("+1 555 123 4567") == {"flagged": False, "reports": 0}
    out = reg.report(t, "+1 (555) 123-4567")
    assert out["ok"] and out["flagged"] and out["reports"] == 1 and out["category"] == "F1"
    assert reg.check("15551234567")["flagged"]            # same number, different formatting


def test_tickets_cannot_be_forged_reused_or_misused(reg):
    t = reg.issue_ticket("fraud", "F1", 92)
    assert reg.report(t, "+15551234567")["ok"]
    assert reg.report(t, "+15550000000")["reason"] == "ticket already used"
    body, sig = reg.issue_ticket("fraud", "F1", 92).split(".")
    assert not reg.report(body + "." + sig[::-1], "+15550000001")["ok"]                  # tampered signature
    other = CallerRegistry("y" * 40, reg.db_path).issue_ticket("fraud", "F1", 92)
    assert not reg.report(other, "+15550000002")["ok"]                                   # other server's key
    old = reg.issue_ticket("fraud", "F1", 92, now=1)
    assert reg.report(old, "+15550000003")["reason"] == "invalid or expired report ticket"
    unsure = reg.issue_ticket("uncertain", "F3", 30)
    assert not reg.report(unsure, "+15550000004")["ok"]                                 # needs a manual report
    assert reg.report(unsure, "+15550000004", manual=True)["ok"]
    assert reg.issue_ticket("not_fraud", "F0", 0) is None


def test_no_raw_caller_ids_are_stored(reg):
    reg.report(reg.issue_ticket("fraud", "F1", 92), "+15551234567")
    dump = "\n".join(sqlite3.connect(reg.db_path).iterdump())
    assert "5551234567" not in dump


def test_classify_returns_ticket_and_endpoints_work(client):
    c, _ = client
    out = c.post("/v1/classify", json={"request_id": "r1", "text": SCAM}, headers={"Authorization": f"Bearer {TOKEN}"}).json()
    tickets = [x[len("report:"):] for x in out["classes"] if x.startswith("report:")]
    assert out["label"] == "fraud" and len(tickets) == 1 and all(len(x) <= 100 for x in out["classes"])
    r = c.post("/v1/callers/report", json={"caller": "+1 555 123 4567", "ticket": tickets[0]}, headers={"Origin": ORIGIN})
    assert r.status_code == 200 and r.json()["flagged"]
    assert r.headers["access-control-allow-origin"] == ORIGIN
    assert c.post("/v1/callers/check", json={"caller": "+15551234567"}).json()["reports"] == 1
    assert c.post("/v1/callers/report", json={"caller": "+15551234567", "ticket": tickets[0]}).status_code == 400
    pre = c.options("/v1/callers/check", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in pre.headers


def test_genuine_call_gets_no_ticket(client):
    c, _ = client
    out = c.post("/v1/classify", json={"request_id": "g", "text": "Hi, this is the pharmacy, your refill is ready."},
                 headers={"Authorization": f"Bearer {TOKEN}"}).json()
    assert out["label"] == "not_fraud" and not any(x.startswith("report:") for x in out["classes"])
