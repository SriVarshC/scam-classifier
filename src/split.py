"""Build train/val/test splits -> data/processed/splits/ (id, fraud_type, label only).

Test A  (main):  real data split ~70/15/15 by group (robocall: FTC campaign; others: conversation),
                 stratified by fraud type. Synthetic rows go to TRAIN ONLY, capped at 30% of train,
                 topping each fraud type up to >= 300 train examples first.
Test B  (leave-one-real-source-out): for each real source (abcd, robocall), train WITHOUT it and
                 test on ALL of its rows plus the other real source's Test A test rows, so both
                 FPR and recall are measurable. Val here needs both classes, so it uses the other real
                 source's val rows + a held-out 15% of synthetic rows (documented exception;
                 test stays real-only). No synthetic cap in B — it is a stress test.
Test C  (early decision): evaluate.py truncates the A and B test sets to the first 50 words.

Usage: python src/split.py
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from config import PROCESSED, RESULTS, SEED, UNKNOWN

SPLITS = PROCESSED / "splits"
MAX_SYNTH_SHARE = 0.30
MIN_PER_TYPE = 300
SYNTH_GENUINE_SHARE = 0.30  # share of the synthetic budget reserved for synthetic F0 (hard negatives)
N_FOLDS = 7  # 1 test fold + 1 val fold + 5 train folds ≈ 71/14/14
REAL_SOURCES = ["abcd", "robocall"]
OUT_COLS = ["id", "fraud_type", "label"]


def split_real(real):
    """Group-aware, type-stratified split of real rows into train/val/test."""
    sgkf = StratifiedGroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    fold = np.empty(len(real), dtype=int)
    for k, (_, idx) in enumerate(sgkf.split(real, real["fraud_type"], real["group_id"])):
        fold[idx] = k
    part = np.where(fold == 0, "test", np.where(fold == 1, "val", "train"))
    return {p: real[part == p] for p in ("train", "val", "test")}


def sample_synthetic_genuine(synth_f0, quota):
    """Synthetic F0 rows, taken round-robin across sources with synthetic_own (hard negatives) first,
    so synthetic style is not a fraud-only signal."""
    pools = [g.sample(frac=1, random_state=SEED) for _, g in
             sorted(synth_f0.groupby("source"), key=lambda kv: kv[0] != "synthetic_own")]
    picked, i = [], 0
    while len(picked) < quota and any(i < len(p) for p in pools):
        picked += [p.iloc[i] for p in pools if i < len(p)][: quota - len(picked)]
        i += 1
    return pd.DataFrame(picked)


def sample_synthetic(synth, real_train, rng):
    """Pick synthetic rows: reserve SYNTH_GENUINE_SHARE of the budget for synthetic F0, top every fraud
    type up to MIN_PER_TYPE, then fill the remaining budget evenly across fraud types."""
    budget = int(MAX_SYNTH_SHARE / (1 - MAX_SYNTH_SHARE) * len(real_train))
    genuine = sample_synthetic_genuine(synth[synth["fraud_type"] == "F0"], int(SYNTH_GENUINE_SHARE * budget))
    budget -= len(genuine)
    synth = synth[synth["fraud_type"] != "F0"]
    real_counts = real_train["fraud_type"].value_counts()
    pools = {t: g.sample(frac=1, random_state=SEED) for t, g in synth.groupby("fraud_type")}
    taken = {t: 0 for t in pools}

    for t, pool in pools.items():  # 1) top up to the minimum
        need = max(0, MIN_PER_TYPE - real_counts.get(t, 0))
        taken[t] = min(need, len(pool))
    budget_left = budget - sum(taken.values())
    if budget_left < 0:
        print(f"!! top-up alone needs {sum(taken.values())} synthetic rows, budget is {budget}; exceeding cap")

    while budget_left > 0:  # 2) round-robin the rest so no single type dominates
        open_types = [t for t in pools if taken[t] < len(pools[t])]
        if not open_types:
            break
        for t in sorted(open_types, key=lambda t: taken[t] + real_counts.get(t, 0)):
            if budget_left == 0:
                break
            taken[t] += 1
            budget_left -= 1
    return pd.concat([genuine, *[pools[t].iloc[:n] for t, n in taken.items()]])


def write(name, train, val, test):
    for part, df in (("train", train), ("val", val), ("test", test)):
        df[OUT_COLS].to_csv(SPLITS / f"{name}_{part}.csv", index=False)


def describe(name, parts, md):
    md.append(f"## {name}\n")
    rows = []
    for part, df in parts.items():
        r = {"split": part, "rows": len(df), "synthetic %": round(100 * df["is_synthetic"].mean(), 1),
             "fraud %": round(100 * df["label"].mean(), 1), "groups": df["group_id"].nunique()}
        r.update(df["fraud_type"].value_counts().to_dict())
        rows.append(r)
    tab = pd.DataFrame(rows).fillna(0)
    type_cols = sorted(c for c in tab.columns if c.startswith("F"))
    tab[type_cols] = tab[type_cols].astype(int)
    md += [tab[["split", "rows", "synthetic %", "fraud %", "groups", *type_cols]].to_markdown(index=False), ""]


def check_no_leak(name, train, val, test):
    for a, b, an, bn in ((train, test, "train", "test"), (train, val, "train", "val"), (val, test, "val", "test")):
        shared = set(a["group_id"]) & set(b["group_id"])
        assert not shared, f"{name}: {len(shared)} groups shared between {an} and {bn}"
        assert not set(a["id"]) & set(b["id"]), f"{name}: ids shared between {an} and {bn}"


def main():
    rng = np.random.default_rng(SEED)
    df = pd.read_csv(PROCESSED / "merged.csv")
    df = df[df["fraud_type"] != UNKNOWN]
    real, synth = df[~df["is_synthetic"]], df[df["is_synthetic"]]
    SPLITS.mkdir(parents=True, exist_ok=True)
    md = ["# Split summary\n"]

    # ---------- Test A ----------
    r = split_real(real)
    a_train = pd.concat([r["train"], sample_synthetic(synth, r["train"], rng)])
    check_no_leak("A", a_train, r["val"], r["test"])
    write("A", a_train, r["val"], r["test"])
    describe("Test A — main split", {"train": a_train, "val": r["val"], "test": r["test"]}, md)

    # ---------- Test B ----------
    synth_shuf = synth.sample(frac=1, random_state=SEED)
    synth_groups = synth_shuf["group_id"].drop_duplicates()
    val_groups = set(synth_groups.iloc[: int(0.15 * len(synth_groups))])
    synth_val = synth_shuf[synth_shuf["group_id"].isin(val_groups)]
    synth_train = synth_shuf[~synth_shuf["group_id"].isin(val_groups)]
    for held in REAL_SOURCES:
        other = [s for s in REAL_SOURCES if s != held][0]
        train = pd.concat([r["train"][r["train"]["source"] == other], synth_train])
        val = pd.concat([r["val"][r["val"]["source"] == other], synth_val])
        test = pd.concat([real[real["source"] == held], r["test"][r["test"]["source"] == other]])
        check_no_leak(f"B_{held}", train, val, test)
        write(f"B_{held}", train, val, test)
        describe(f"Test B — {held} held out (never seen in training)",
                 {"train": train, "val": val, "test": test}, md)

    md += ["Test C: evaluate.py truncates every test set above to its first 50 words.", ""]
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "split_summary.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    print(f"splits -> {SPLITS}")


if __name__ == "__main__":
    main()
