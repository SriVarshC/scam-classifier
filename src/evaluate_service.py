"""End-to-end check of the LIVE service decision on real calls it has never seen.

Sends whole real calls from Test R (held out from every model) to POST /v1/classify and reports how often
the service says fraud / uncertain / not_fraud for genuine calls and for scams.
  * genuine: CallCenterEN calls, sampled evenly per domain (SEED)
  * scams:   every robocall / youtube_scam call in Test R
Texts are the raw transcripts (before clean.py). CallCenterEN redaction tags are filled with neutral words
so the service sees normal speech. Nothing is printed or stored except labels, scores and flag ids.

Usage: python src/evaluate_service.py --url https://<host> --token-file <file> [--per-domain 15]
"""
import argparse
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from config import PROCESSED, RESULTS, SEED

MAX_CHARS = 19000   # service limit is 20,000


def neutral(text):
    text = text.replace("ccpersonnamecc", "Alex").replace("x@x", "my email")
    text = re.sub(r"\[ORGANIZATION\]", "the company", text)
    text = re.sub(r"\[LOCATION\]", "the city", text)
    return re.sub(r"\s+", " ", re.sub(r"\[[A-Z_]+\]", " ", text)).strip()


def pick_calls(per_domain):
    test = pd.read_csv(PROCESSED / "splits" / "R_test.csv")
    parents = set(test["id"].str.replace(r"_c\d+$", "", regex=True))
    raw = pd.read_csv(PROCESSED / "raw_merged.csv")
    raw = raw[raw["id"].isin(parents)]
    genuine = (raw[raw["source"] == "callcenter_en"].groupby("scam_type", group_keys=False)
               .apply(lambda g: g.sample(min(per_domain, len(g)), random_state=SEED)))
    scams = raw[raw["source"].isin(["robocall", "youtube_scam"]) & (raw["label"] == 1)]
    calls = pd.concat([genuine, scams])
    calls["send"] = [neutral(t)[:MAX_CHARS] for t in calls["text"]]
    return calls


def classify(url, token, rid, text):
    req = urllib.request.Request(f"{url}/v1/classify", method="POST",
                                 data=json.dumps({"request_id": rid, "text": text}).encode(),
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=200) as r:
            out = json.load(r)
        return {"id": rid, "seconds": round(time.time() - t, 1), "label_out": out["label"],
                "risk_level": out["risk_level"], "risk_score": out["risk_score"], "llm_verdict": out["llm_verdict"],
                "llm_backend": out.get("llm_backend"), "category": out.get("category"),
                "flags": "|".join(f["id"] for f in out["red_flags"]), "error": ""}
    except Exception as e:
        return {"id": rid, "seconds": round(time.time() - t, 1), "error": f"{type(e).__name__}: {e}"[:200]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--token-file", required=True)
    ap.add_argument("--per-domain", type=int, default=15)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--n-genuine", type=int, default=0, help="quick check: only this many genuine calls")
    ap.add_argument("--n-scam", type=int, default=0, help="quick check: only this many scam calls")
    ap.add_argument("--out", default="service_eval_real", help="result file name (results/<out>.csv/.md)")
    args = ap.parse_args()
    token = open(args.token_file).read().strip()
    calls = pick_calls(args.per_domain)
    if args.n_genuine or args.n_scam:   # quick check: a small random subset of each
        calls = pd.concat([calls[calls["label"] == 0].sample(min(args.n_genuine, (calls["label"] == 0).sum()), random_state=SEED),
                           calls[calls["label"] == 1].sample(min(args.n_scam, (calls["label"] == 1).sum()), random_state=SEED)])
    print(f"{len(calls)} calls: {calls.groupby(['source', 'label']).size().to_dict()}", flush=True)
    results = []
    with ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(classify, args.url.rstrip("/"), token, i, t) for i, t in zip(calls["id"], calls["send"])]
        for k, f in enumerate(futs, 1):
            results.append(f.result())
            if k % 20 == 0:
                print(f"  {k}/{len(futs)}", flush=True)
    res = calls[["id", "source", "scam_type", "label"]].merge(pd.DataFrame(results), on="id")
    res.to_csv(RESULTS / f"{args.out}.csv", index=False)
    ok = res[res["error"] == ""]
    md = ["# Live service on real calls (Test R, never seen by any model)\n",
          f"{len(res)} calls sent, {len(res) - len(ok)} errors. Median time {ok['seconds'].median():.1f}s; "
          f"LLM backend: {ok['llm_backend'].value_counts().to_dict()}\n"]
    for lab, name in ((0, "Genuine calls (CallCenterEN)"), (1, "Real scam calls (robocall + youtube_scam)")):
        g = ok[ok["label"] == lab]
        dist = g["label_out"].value_counts(normalize=True).mul(100).round(1)
        md += [f"## {name}: n={len(g)}\n",
               "| service label | % |", "|---|---|"] + [f"| {k} | {v} |" for k, v in dist.items()] + [""]
        md += ["Risk level: " + ", ".join(f"{k} {v}%" for k, v in
                                           g["risk_level"].value_counts(normalize=True).mul(100).round(1).items()),
               "LLM verdict: " + ", ".join(f"{k} {v}%" for k, v in
                                            g["llm_verdict"].value_counts(normalize=True).mul(100).round(1).items()), ""]
        if lab == 0:
            fp = g[g["label_out"] != "not_fraud"]
            md += ["Genuine calls not labelled not_fraud, by domain:\n",
                   g.groupby("scam_type")["label_out"].apply(lambda s: f"{(s != 'not_fraud').mean():.0%}").to_frame("flagged").to_markdown(), "",
                   "Red flags on those calls: " + str(fp["flags"].str.split("|").explode().value_counts().head(10).to_dict()), ""]
    (RESULTS / f"{args.out}.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
