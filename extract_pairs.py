#!/usr/bin/env python3
"""Build eval splits from the GitHub Typo Corpus (Hagiwara & Mita, LREC 2020).

The corpus is NOT redistributed here — fetch it, then extract labelled
typo/correction pairs per language:

    python3 extract_pairs.py --corpus typoCorpus.v1.0.0.jsonl.gz \
        --lang en --vocab en_words.txt --out data/

**Provenance note.** The FROZEN split files this benchmark scores were
built by the canonical pipeline in kotoshu/models-fasttext-onnx
(`scripts/fetch_corpus.py` + `scripts/extract_suggest_pairs.py`, which
classify by fastText-vocabulary membership over that repo's model
vocab). This standalone extractor reads the same corpus schema and
classifies by any word-per-line vocabulary you supply, so a fresh
checkout can rebuild *equivalent* splits — but byte-exact reproduction
of the frozen files uses the canonical pipeline (see README,
"Reproducing the frozen splits").

Emits <out>/<lang>.suggest-{nonword,realword}.json with the schema the
scorer consumes:
{"spec": "kotoshu.suggest-benchmark/v1", "language": ..., "klass": ...,
 "n": N, "pairs": [{"typo": ..., "correction": ..., "weight": ...}]}

GTC v1.0.0 row shape: {"edits": [{"src": {"text": ..., "lang": ...},
"tgt": {"text": ...}}, ...]} — one edit per element, packaged as
.jsonl.gz.
"""
import argparse
import gzip
import json
import re
from collections import Counter
from pathlib import Path

LANG_MAP = {
    "eng": "en", "deu": "de", "fra": "fr", "spa": "es",
    "por": "pt", "rus": "ru", "ita": "it", "nld": "nl", "pol": "pl",
}

WORD_RE = re.compile(r"^[A-Za-zÀ-ÿĀ-žĂ-șА-я][A-Za-zÀ-ÿĀ-žĂ-șА-я'’-]*$")


def open_corpus(path):
    return gzip.open(path, "rt", encoding="utf-8") if path.endswith(".gz") \
        else open(path, encoding="utf-8")


def extract(corpus_path, langs, vocab):
    pairs = {lang: {"nonword": Counter(), "realword": Counter()}
             for lang in langs}
    n = 0
    with open_corpus(corpus_path) as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            for edit in row.get("edits", []):
                src = edit.get("src", {})
                tgt = edit.get("tgt", {})
                lang = LANG_MAP.get(src.get("lang", ""))
                if lang is None or lang not in langs:
                    continue
                s_word = (src.get("text") or "").strip()
                d_word = (tgt.get("text") or "").strip()
                if not s_word or not d_word or s_word == d_word:
                    continue
                if not WORD_RE.match(s_word) or not WORD_RE.match(d_word):
                    continue
                klass = "realword" if s_word.lower() in vocab else "nonword"
                pairs[lang][klass][(s_word, d_word)] += 1
            n += 1
            if n % 200_000 == 0:
                print(f"  {n} rows...", flush=True)
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True,
                    help="GitHub Typo Corpus .jsonl or .jsonl.gz")
    ap.add_argument("--lang", action="append", default=[],
                    help="language(s) to keep (default: all mapped)")
    ap.add_argument("--vocab", required=True,
                    help="word-per-line vocabulary for realword classification")
    ap.add_argument("--out", default="data", help="output directory")
    a = ap.parse_args()

    langs = a.lang or list(LANG_MAP.values())
    vocab = set()
    with open(a.vocab, encoding="utf-8") as fh:
        for line in fh:
            w = line.strip().lower()
            if w:
                vocab.add(w)
    print(f"vocab: {len(vocab)} words; langs: {langs}")

    pairs = extract(a.corpus, langs, vocab)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for lang, by_class in pairs.items():
        for klass, counter in by_class.items():
            payload = {
                "spec": "kotoshu.suggest-benchmark/v1",
                "language": lang,
                "klass": klass,
                "n": len(counter),
                "pairs": [{"typo": s, "correction": d, "weight": c}
                          for (s, d), c in counter.most_common()],
            }
            path = out / f"{lang}.suggest-{klass}.json"
            path.write_text(json.dumps(payload, ensure_ascii=False))
            print(f"wrote {path}: {len(counter)} pairs")


if __name__ == "__main__":
    main()
