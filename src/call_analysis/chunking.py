"""Step 2: simulate a live call by cutting each transcript into ~30-word chunks with timestamps.

- Sentences are kept whole where the transcript has punctuation; long sentences (and unpunctuated
  auto-captions such as the YouTube calls) are cut into ~30-word pieces.
- Speaker labels are kept for display: caller/agent -> "Caller", receiver/recipient/customer -> "You".
  Calls without labels get "Caller" (one-way robocalls) or no speaker (YouTube: both sides mixed).
- Simulated clock: 2.5 words per second.
- The "transcript" every quote is checked against is the raw call text with whitespace collapsed;
  every chunk segment is asserted to be an exact substring of it.

Output: results/call_analysis/calls/<call_id>.json
Usage:  python src/call_analysis/chunking.py [--use-audio]
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from call_analysis import OUT  # noqa: E402
from config import PROCESSED  # noqa: E402

TARGET_WORDS = 30
MAX_WORDS = 38          # a chunk may grow to this to keep a sentence whole
WORDS_PER_SECOND = 2.5
SPEAKER_RE = re.compile(r"(?i)\b(caller|agent|receiver|recipient|customer)\s*:")
SPEAKER_NAME = {"caller": "Caller", "agent": "Caller", "receiver": "You", "recipient": "You", "customer": "You"}
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def normalise(text):
    return " ".join(str(text).split())


def to_turns(text, source):
    """[(speaker or None, text)] in call order."""
    text = normalise(text)
    parts = SPEAKER_RE.split(text)
    if len(parts) > 1:  # labelled dialogue: ['', 'caller', ' hi ...', 'receiver', ' ...']
        turns = [(SPEAKER_NAME[parts[i].lower()], parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]
        return [(s, t) for s, t in turns if t]
    return [("Caller" if source in ("robocall", "kaggle_scam_nonscam") else None, text)]


def to_units(turns):
    """Split turns into sentence-sized units; cut over-long sentences into TARGET_WORDS pieces."""
    units = []
    for turn_no, (speaker, text) in enumerate(turns):
        for sentence in SENTENCE_RE.split(text):
            words = sentence.split()
            step = TARGET_WORDS if len(words) > MAX_WORDS else max(len(words), 1)
            for i in range(0, len(words), step):
                units.append((speaker, turn_no, " ".join(words[i:i + step])))
    return units


def chunk_call(text, source):
    units = to_units(to_turns(text, source))
    chunks, cur, cur_words, words_before = [], [], 0, 0

    def close():
        nonlocal cur, cur_words, words_before
        segments = []
        for speaker, turn_no, t in cur:  # merge consecutive units of the SAME turn into one display line
            if segments and segments[-1]["turn"] == turn_no:
                segments[-1]["text"] += " " + t
            else:
                segments.append({"speaker": speaker, "turn": turn_no, "text": t})
        chunks.append({"index": len(chunks), "start_s": round(words_before / WORDS_PER_SECOND, 1),
                       "end_s": round((words_before + cur_words) / WORDS_PER_SECOND, 1),
                       "n_words": cur_words, "segments": segments})
        words_before += cur_words
        cur, cur_words = [], 0

    for speaker, turn_no, t in units:
        n = len(t.split())
        if cur and (cur_words >= TARGET_WORDS or cur_words + n > MAX_WORDS):
            close()
        cur.append((speaker, turn_no, t))
        cur_words += n
    if cur:
        close()
    return chunks


def verify_segments(call):
    """Every displayed segment must be verbatim text from the transcript (fail loudly otherwise)."""
    for c in call["chunks"]:
        for s in c["segments"]:
            if s["text"] not in call["transcript"]:
                raise AssertionError(f"{call['id']} chunk {c['index']}: segment not found verbatim: {s['text'][:80]!r}")


def build_calls(selected=None):
    selected = selected if selected is not None else pd.read_csv(OUT / "selected_calls.csv")
    raw = pd.read_csv(PROCESSED / "raw_merged.csv").set_index("id")
    (OUT / "calls").mkdir(parents=True, exist_ok=True)
    calls = []
    for row in selected.itertuples():
        text = raw.loc[row.id, "text"]
        chunks = chunk_call(text, row.source)
        call = {"id": row.id, "source": row.source, "true_label": row.true_label, "scam_type": row.scam_type,
                "is_synthetic": bool(row.is_synthetic), "transcript": normalise(text),
                "duration_s": chunks[-1]["end_s"], "chunks": chunks}
        verify_segments(call)
        (OUT / "calls" / f"{row.id}.json").write_text(json.dumps(call, indent=1), encoding="utf-8")
        calls.append(call)
    return calls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--use-audio", action="store_true",
                    help="robocall calls: streaming speech-to-text with faster-whisper (not installed yet)")
    args = ap.parse_args()
    if args.use_audio:
        raise SystemExit("--use-audio needs faster-whisper (small model, ~0.5 GB). Not installed yet - "
                         "ask the user before installing (CLAUDE.md rule 8).")
    calls = build_calls()
    for c in calls:
        print(f"{c['id']:22s} {len(c['chunks']):3d} chunks  {c['duration_s']:6.1f}s simulated  "
              f"speakers={sorted({s['speaker'] or '-' for ch in c['chunks'] for s in ch['segments']})}")
    print(f"\n{len(calls)} calls -> {OUT / 'calls'} (all segments verified verbatim)")


if __name__ == "__main__":
    main()
