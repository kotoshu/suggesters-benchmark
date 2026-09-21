# suggesters-benchmark

Open, reproducible benchmark for spelling **suggestion quality**: given a
human typo and its human correction, which engine puts the correction in
the top-k? Every claim kotoshu makes about beating Hunspell / SymSpell /
LanguageTool comes from this pipeline — and anyone can re-run it.

## What it measures

Top-1 / top-3 / top-5 exact-match (case-insensitive) of the human
correction, over two error classes:

- **nonword** — "helo" → "hello" (classic misspelling)
- **realword** — "there" → "their" (valid word, wrong word; the class
  context-free engines are bad at)

## Quickstart

```bash
pip install symspellpy
# 1. build eval splits locally (corpus is fetched, never committed here)
python3 extract_pairs.py --corpus typoCorpus.v1.0.0.jsonl --lang en --out data/
# 2. point lanes.yaml datasets at your splits, then
python3 benchmark.py --lanes lanes.yaml --lang en --max 2000
```

## Lanes

`lanes.yaml` is the entire configuration: add an engine lane to
benchmark a new contender, add a dataset lane for a new language.
The harness discovers lanes from the file so runs stay comparable.

Current lanes: **kotoshu** (Ruby ranking pipeline), **hunspell**
(ispell -a over LibreOffice dictionaries), **symspell** (symspellpy TOP
mode over the same frequency table kotoshu indexes), **languagetool**
(public API, bounded subsample).

## Results (2026-09-21)

Environment: macOS arm64, Ruby 3.4, kotoshu 1.0.x (PR #226 ranking),
frequency lists from kotoshu/frequency-list-kelly (en = Kelly core +
wiki tail, 42,585 words; de = Wikimedia unigrams, 21,781 words).
Corpus: GitHub Typo Corpus v1.0.0 (Hagiwara & Mita, LREC 2020),
frozen splits, max 2000 nonword + 2000 realword pairs (en), 79/72 (de).

**English (2000 nonword / 2000 realword pairs)**

| engine | nonword top-1 | top-3 | top-5 | realword top-1 |
|---|---|---|---|---|
| **kotoshu** | **86.4%** | **94.4%** | **95.7%** | **9.4%** |
| SymSpell (TOP) | 85.4% | 85.4% | 85.4% | 4.4% |
| Hunspell | 78.5% | 93.6% | 95.1% | 7.4% |

**German (79 nonword / 72 realword pairs — thin, labelled)**

| engine | nonword top-1 | top-3 | top-5 | realword top-1 |
|---|---|---|---|---|
| SymSpell (TOP) | **73.4%** | 73.4% | 73.4% | 1.4% |
| kotoshu | 70.9% | **91.1%** | **92.4%** | **11.1%** |
| Hunspell | 54.4% | 74.7% | 77.2% | 5.6% |

Reproduce with `--max 2000` and the same frequency lists; numbers will
match to within corpus-build ordering noise.

## License

MIT. The GitHub Typo Corpus has its own terms — fetch it separately
and do not redistribute splits.
