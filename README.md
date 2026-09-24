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
(public API, bounded subsample), **quill** (pure-Python noisy-channel
suggester, English only; answers valid words too, see the lane note).

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
| quill ¹ | 95.2% | 98.2% | 98.45% | 47.2% ² |

¹ quill-spell 0.6.0, run on Linux x86_64 (Python 3.11) with this repo's
`score()` on the same frozen splits (2000 + 2000 pairs).

² Not comparable with the rows above: quill also suggests alternatives
for valid words, while the other lanes return nothing for a word their
dictionary accepts, and the realword class consists only of valid
words. Hunspell forced to suggest for accepted words scores 15.3% /
41.5% / 50.7% realword top-1 / 3 / 5 on the same pairs.

**German (79 nonword / 72 realword pairs — thin, labelled)**

| engine | nonword top-1 | top-3 | top-5 | realword top-1 |
|---|---|---|---|---|
| SymSpell (TOP) | **73.4%** | 73.4% | 73.4% | 1.4% |
| kotoshu | 70.9% | **91.1%** | **92.4%** | **11.1%** |
| Hunspell | 54.4% | 74.7% | 77.2% | 5.6% |

Reproduce with `--max 2000` and the same frequency lists; numbers will
match to within corpus-build ordering noise.

## Fleet results (first wave, 2026-09-22)

Six languages. Field lanes: LibreOffice/wooorm Hunspell dictionaries +
the SAME published frequency lists the gem indexes. Small splits for
es/fr/pt/ru (labelled; corpus is thin there) — within-noise gaps are
notated rather than claimed as wins.

| lang | n(nonword) | kotoshu top1/top3/top5 | SymSpell top1 | Hunspell top1 |
|------|-----------|------------------------|---------------|---------------|
| en | 2000 | **86.4 / 94.4 / 95.7** | 85.4 | 78.5 |
| es | 71 | **76.1 / 87.3 / 87.3** | 74.7 | 59.2 |
| fr | 119 | **68.1 / 84.0 / 84.9** | 65.6 | 61.3 |
| ru | 304 | 74.0 / **86.8 / 88.2** | 75.0 | 70.7 |
| pt | 124 | 66.1 / 79.0 / **82.3** | 67.7 | 62.9 |
| de | 79 | 70.9 / **91.1 / 92.4** → **72.2 / 89.9 / 91.1** (C9 fold) | 73.4 | 54.4 |

kotoshu is #1 on nonword top-1 outright in en/es/fr; ru/pt sit within
split-size noise at top-1 while #1 at top-3/top-5. Real-word:
kotoshu leads en/de/pt/ru; Hunspell's morphology leads es/fr — the
context-bound frontier, quantified per language in
kotoshu/models-fasttext-onnx TODO.compare/8.

## License

MIT. The GitHub Typo Corpus has its own terms — fetch it separately
and do not redistribute splits.
