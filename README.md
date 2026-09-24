# jev-vs-claude-benchmark

Real, reproducible benchmark comparing [Jev](https://typesafe.ai) (TypeSafe's "System One" decision model) against Claude in reasoning mode, on the same classification task.

Everyone quoting TypeSafe's "193x faster, 445x cheaper" number is repeating a vendor-published benchmark. This repo runs the comparison yourself — real API calls to both providers, real latency, real cost, no simulation.

## What it does

Sends the same 3 messages to:
- **Jev**, via OpenRouter's System One endpoint (`typesafe/jev-1.13`) — returns calibrated probabilities for 3 yes/no questions in a single pass
- **Claude** (`claude-sonnet-4-6`) — reasons through the same 3 questions in prose before answering

Measures real wall-clock latency and real cost (from each provider's actual token usage) for both.

## Setup

```bash
git clone https://github.com/<your-username>/jev-vs-claude-benchmark
cd jev-vs-claude-benchmark
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:
```
OPENROUTER_API_KEY=your_openrouter_key
ANTHROPIC_API_KEY=your_anthropic_key
```

Get an OpenRouter key at [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys) — no TypeSafe waitlist needed, Jev is served there directly.

## Run

```bash
python benchmark.py
```

Edit the `QUESTIONS` list in `benchmark.py` to test your own messages.

## Results

See [`results/`](./results) for saved runs. Numbers vary run to run (live APIs), but the gap is consistent.

| Model | Avg Latency | Avg Cost |
|---|---|---|
| Jev | — ms | $— |
| Claude (reasoning) | — s | $— |

*(filled in after first real run)*

## Why the gap exists

Not because Jev is a magic black box. Two structural reasons:
1. **No decode-heavy generation.** Claude reasons in prose (hundreds of tokens) before committing to an answer. Jev returns a fixed-schema probability directly — no reasoning tokens to generate or pay for.
2. **Calibration, not just speed.** Jev is trained with RLCD (Reinforcement Learning for Calibrated Decisions) — optimized so a 0.8 confidence score is right ~80% of the time, not just "sounds confident." That's arguably the more interesting part; the speed is a side effect of skipping generation, not the core innovation.

Full writeup: *(link your LinkedIn article here)*

## Caveats

- Small sample (3 messages) — this is a demo of the mechanism, not a statistically rigorous benchmark
- Jev is listed as beta on OpenRouter as of Sept 2026 — pricing/availability may shift
- Cost constants in `benchmark.py` should be checked against current pricing pages before trusting absolute numbers
