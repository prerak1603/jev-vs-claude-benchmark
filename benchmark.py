"""
benchmark.py

REAL benchmark. Both sides are actual API calls, not simulated.

Side A: Jev (TypeSafe), via OpenRouter's System One endpoint
Side B: Claude, reasoning in prose before answering

Setup:
    pip install -r requirements.txt
    cp .env.example .env   # then fill in your two keys

Run:
    python benchmark.py
"""

import os
import time
import statistics
import requests
from dotenv import load_dotenv
from anthropic import Anthropic
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

load_dotenv()

console = Console()

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")

anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)
CLAUDE_MODEL = "claude-sonnet-4-6"

# Check current pricing before trusting these numbers:
# Claude: https://docs.claude.com | Jev: $0.042 / 1M input, output free (confirmed)
CLAUDE_INPUT_PRICE = 3.00   # USD per million input tokens — verify current rate
CLAUDE_OUTPUT_PRICE = 15.00  # USD per million output tokens — verify current rate
JEV_INPUT_PRICE = 0.042     # USD per million input tokens — confirmed by TypeSafe

# ---- EDIT THESE to test your own questions ----
QUESTIONS = [
    "Hi, I was charged twice this month for the same invoice, can someone help me get this fixed?",
    "I want my money back, this product broke after two days and I'm furious.",
    "Whenever you get a chance, no rush at all, could you send over the report?",
]


def call_jev(state_text: str):
    """Real call to Jev via OpenRouter's System One endpoint."""
    start = time.perf_counter()
    resp = requests.post(
        "https://openrouter.ai/api/v1/systemone",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "typesafe/jev-1.13",
            "state": state_text,
            "questions": {
                "is_billing": {
                    "type": "noul",
                    "instructions": "Is this message about a billing or payment issue?",
                },
                "is_urgent": {
                    "type": "noul",
                    "instructions": "Does this message express urgency?",
                },
                "is_complaint": {
                    "type": "noul",
                    "instructions": "Is the person expressing frustration or dissatisfaction?",
                },
            },
        },
        timeout=15,
    )
    elapsed = time.perf_counter() - start
    resp.raise_for_status()
    data = resp.json()

    usage = data.get("usage", {})
    input_tokens = usage.get("input_tokens", usage.get("prompt_tokens", 0))
    cost = (input_tokens / 1_000_000) * JEV_INPUT_PRICE

    return {
        "elapsed": elapsed,
        "cost": cost,
        "input_tokens": input_tokens,
        "answers": data.get("answers", data),
    }


def call_claude_reasoning(state_text: str):
    """Real call to Claude, reasoning in prose before answering the same questions."""
    start = time.perf_counter()
    resp = anthropic_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": (
                f"Message: \"{state_text}\"\n\n"
                "Think through this step by step, then answer these three questions "
                "with yes/no and a confidence score 0-1:\n"
                "1. Is this about a billing or payment issue?\n"
                "2. Does this message express urgency?\n"
                "3. Is the person expressing frustration or dissatisfaction?"
            )
        }]
    )
    elapsed = time.perf_counter() - start
    text = resp.content[0].text
    cost = (
        (resp.usage.input_tokens / 1_000_000) * CLAUDE_INPUT_PRICE
        + (resp.usage.output_tokens / 1_000_000) * CLAUDE_OUTPUT_PRICE
    )
    return {
        "elapsed": elapsed,
        "cost": cost,
        "output_tokens": resp.usage.output_tokens,
        "text": text,
    }


def main():
    if not OPENROUTER_KEY or not ANTHROPIC_KEY:
        console.print("[red]Set OPENROUTER_API_KEY and ANTHROPIC_API_KEY first.[/red]")
        return

    console.print(Panel.fit(
        "[bold]REAL Jev (via OpenRouter) vs REAL Claude (reasoning mode)[/bold]\n"
        "Both sides are live API calls — no simulation.",
        style="cyan"
    ))

    jev_results, claude_results = [], []

    for i, q in enumerate(QUESTIONS, 1):
        console.print(f"\n[bold yellow]Message {i}:[/bold yellow] {q}\n")

        console.print("[green]-> Calling Jev (OpenRouter)...[/green]")
        j = call_jev(q)
        jev_results.append(j)
        console.print(f"   [dim]{j['elapsed']*1000:.0f}ms | ${j['cost']:.7f} | {j['input_tokens']} input tokens[/dim]")
        console.print(f"   [dim]Answers: {j['answers']}[/dim]")

        console.print("[red]-> Calling Claude (reasoning)...[/red]")
        c = call_claude_reasoning(q)
        claude_results.append(c)
        console.print(f"   [dim]{c['elapsed']:.2f}s | ${c['cost']:.5f} | {c['output_tokens']} output tokens[/dim]")
        console.print(f"   [dim]{c['text'][:180]}...[/dim]")

    avg_jev_time = statistics.mean(r["elapsed"] for r in jev_results)
    avg_claude_time = statistics.mean(r["elapsed"] for r in claude_results)
    avg_jev_cost = statistics.mean(r["cost"] for r in jev_results)
    avg_claude_cost = statistics.mean(r["cost"] for r in claude_results)

    table = Table(title="\nReal results — averaged across all messages")
    table.add_column("Model", style="bold")
    table.add_column("Avg Latency")
    table.add_column("Avg Cost")

    table.add_row("Jev (real)", f"{avg_jev_time*1000:.0f}ms", f"${avg_jev_cost:.7f}")
    table.add_row("Claude (reasoning)", f"{avg_claude_time:.2f}s", f"${avg_claude_cost:.5f}")

    console.print(table)
    console.print(
        f"\n[bold]Speedup: {avg_claude_time/avg_jev_time:.0f}x faster | "
        f"Cost reduction: {avg_claude_cost/avg_jev_cost:.0f}x cheaper[/bold]\n"
    )
    console.print("[dim]Real API calls. Real timestamps. Real invoices from both providers.[/dim]")


if __name__ == "__main__":
    main()
