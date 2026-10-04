"""
Research-to-Deck Agent — one command, full pipeline.

Usage:
    python run.py "Your topic here"
    python run.py                      (will prompt for a topic)

Runs, in order:
  1. Web research        (research/search.py)   -- needs internet
  2. Content structuring (research/structure.py) -- needs Ollama running locally
  3. Deck generation     (research/deck.py)      -- fully offline

Produces a ready-to-open .pptx in output/.
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "research"))

from search import research_topic, save_results
from structure import structure_content, save_outline
from deck import build_deck


def run_pipeline(topic, max_results_per_query=5):
    print("=" * 70)
    print("RESEARCH-TO-DECK AGENT")
    print(f"Topic: {topic}")
    print("=" * 70)

    # ---- Step 1: research ----
    print("\n[1/3] Researching topic across the web...\n")
    t0 = time.time()
    results = research_topic(topic, max_results_per_query=max_results_per_query)
    if not results:
        print("\n[!] No research results found. Try a broader or differently worded topic.")
        return None
    research_path = save_results(results, topic)
    print(f"[1/3] Done in {time.time() - t0:.1f}s -- {len(results)} sources saved to {research_path}")

    # ---- Step 2: structure ----
    print("\n[2/3] Structuring content with local LLM (this can take a minute or two)...\n")
    t0 = time.time()
    try:
        outline = structure_content(topic, results)
    except Exception as e:
        print(f"\n[!] Content structuring failed: {e}")
        print(f"    Raw research was still saved to {research_path} -- you can retry")
        print(f"    structuring alone with: python research/structure.py {research_path}")
        return None
    outline_path = save_outline(outline, topic)
    print(f"[2/3] Done in {time.time() - t0:.1f}s -- outline saved to {outline_path}")

    # ---- Step 3: deck ----
    print("\n[3/3] Generating PowerPoint deck...\n")
    t0 = time.time()
    out_name = os.path.splitext(os.path.basename(outline_path))[0].replace("outline_", "deck_") + ".pptx"
    out_path = os.path.join("output", out_name)
    build_deck(outline, out_path)
    print(f"[3/3] Done in {time.time() - t0:.1f}s")

    print("\n" + "=" * 70)
    print(f"FINISHED. Open your deck at: {out_path}")
    print("=" * 70)
    return out_path


if __name__ == "__main__":
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input("Enter a research topic: ").strip()

    if not topic:
        print("No topic given, exiting.")
        sys.exit(1)

    run_pipeline(topic)
