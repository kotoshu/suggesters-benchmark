#!/usr/bin/env python3
"""Build eval splits from the GitHub Typo Corpus (Hagiwara & Mita, LREC 2020).

The corpus is NOT redistributed here — fetch it, then extract labelled
typo/correction pairs per language:

    python3 extract_pairs.py --corpus typoCorpus.v1.0.0.jsonl --lang en --out data/

Emits data/<lang>.suggest-{nonword,realword}.json with a stable schema:
{"spec": "kotoshu.suggest-benchmark/v1", "language": ..., "klass": ...,
 "n": N, "pairs": [{"typo": ..., "correction": ..., "weight": ...}]}
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

LANG_MAP = {
    "eng": "en", "deu": "de", "fra": "fr", "spa": "es",
    "por": "pt", "rus": "ru", "ita": "it", "nld": "nl", "pol": "pl",
}


def extract_pairs(corpus_path, langs=None):
    pairs = {lang: {"nonword": Counter(), "realword": Counter()} for lang in LANG_MAP.values()}
    with open(corpus_path, encoding="utf-8") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            src = row.get("src", {})
            dst = row.get("dst", {})
            lang = LANG_MAP.get(src.get("lang", ""))
            if lang is None or (langs and lang not in langs):
                continue
            src_edits = src.get("edits", [])
            dst_edits = dst.get("edits", [])
            for (s_word, d_word, s_ann, _d_ann) in _zip_edits(src_edits, dst_edits):
                if not s_word or not d_word or s_word.lower() == d_word.lower():
                    continue
                klass = "nonword" if _is_nonword(s_ann) else "realword"
                pairs[lang][klass][(s_word, d_word)] += 1
    return pairs


def _zip_edits(src_edits, dst_edits):
    for s_edit, d_edit in zip(src_edits, dst_edits):
        yield (s_edit[0], d_edit[0], s_edit[1], d_edit[1])


def _is_nonword(annotation):
    return bool(re.search(r"(?i)\b(nonword|misspelling|typo)\b", str(annotation)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--lang", action="append", default=None)
    ap.add_argument("--out", default="data")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pairs = extract_pairs(args.corpus, set(args.lang) if args.lang else None)
    for lang, by_klass in pairs.items():
        for klass, counter in by_klass.items():
            if not counter:
                continue
            payload = {
                "spec": "kotoshu.suggest-benchmark/v1",
                "language": lang,
                "klass": klass,
                "n": sum(counter.values()),
                "pairs": [
                    {"typo": t, "correction": c, "weight": w}
                    for (t, c), w in counter.most_common()
                ],
            }
            path = out / f"{lang}.suggest-{klass}.json"
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=1))
            print(f"wrote {path} ({payload['n']} pairs)")


if __name__ == "__main__":
    main()
