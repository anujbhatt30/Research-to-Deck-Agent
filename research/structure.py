"""
Step 2: Content structuring.

Takes the raw, sourced research from Step 1 and asks the local LLM to
organize it into a slide outline: titles, bullet points, and any numbers
worth turning into a chart -- with every claim still tagged to a source
URL, so the final deck can cite where its numbers came from.

Requires Ollama running locally with qwen3.5:9b pulled (same as your
other agent).
"""

import json
import os
import re
import sys
import ollama
from json_repair import repair_json

MODEL = "qwen3.5:9b"
MAX_CONTENT_CHARS = 500   # per source -- kept small so the total prompt fits the model's context window
MAX_SOURCES = 6            # cap how many sources go into one prompt
NUM_CTX = 4096             # total context window (input + output combined)
NUM_PREDICT = 1800         # max new tokens to generate -- enough for 6-8 slides of JSON


def load_research(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["topic"], data["results"]


def condense_sources(results, max_sources=MAX_SOURCES):
    """Trim each source down to a manageable size for the prompt, and cap the count."""
    condensed = []
    for r in results[:max_sources]:
        text = r["content"] or r["snippet"]
        if text and len(text) > MAX_CONTENT_CHARS:
            text = text[:MAX_CONTENT_CHARS] + "..."
        condensed.append({
            "url": r["url"],
            "title": r["title"],
            "text": text,
        })
    return condensed


SCHEMA_EXAMPLE = """{
  "topic": "Generative AI impact on business",
  "slides": [
    {
      "title": "What Is Generative AI?",
      "type": "intro",
      "bullets": ["Short definition point", "Second point"],
      "chart": null,
      "sources": []
    },
    {
      "title": "Economic Value at Stake",
      "type": "chart",
      "bullets": ["One-line takeaway about the chart"],
      "chart": {
        "chart_type": "bar",
        "labels": ["Customer Ops", "Marketing & Sales", "Software Eng", "R&D"],
        "values": [37, 10, 32, 12],
        "unit": "% of function cost",
        "title": "Productivity potential by function"
      },
      "sources": ["https://example.com/source-used"]
    }
  ]
}"""


def build_prompt(topic, condensed_sources):
    sources_block = "\n\n".join(
        f"SOURCE: {s['url']}\nTITLE: {s['title']}\nTEXT: {s['text']}"
        for s in condensed_sources
    )
    return f"""You are structuring research into a business presentation outline.

TOPIC: {topic}

Below are research sources. Use ONLY information found in them -- do not
invent statistics or facts that are not present in the text.

{sources_block}

Produce a slide outline as JSON matching this exact schema (this is an example, use your own real content from the sources above):

{SCHEMA_EXAMPLE}

Rules:
- Output ONLY valid JSON, nothing else -- no explanation, no markdown code fences.
- Create 6-8 slides covering: what it is, adoption/scale, impact across different fields/industries, key advantages, how it's transforming business/workplaces.
- At least 2 slides should have type "chart" with real numeric data found in the sources (for bar or pie charts).
- Every slide's "sources" list must contain the actual URL(s) the content came from.
- Keep each bullet under 20 words.
- Do not fabricate numbers. If you cannot find a real statistic for a chart, use type "bullets" instead of "chart" for that slide.
"""


def clean_json_response(text):
    """Strip markdown fences etc. in case the model adds them despite instructions."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    return text.strip()


def salvage_truncated_json(text):
    """
    If the model's response got cut off mid-JSON, try to recover whatever
    complete slide objects came through, rather than losing the whole run.
    Returns a repaired JSON string, or None if nothing could be salvaged.
    """
    stack = []
    last_safe_idx = None
    in_string = False
    escape = False
    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack:
                stack.pop()
            # back down to exactly [outer object, slides array] means we just
            # closed one complete slide object -- a safe place to cut
            if ch == "}" and stack == ["{", "["]:
                last_safe_idx = i + 1
    if last_safe_idx is None:
        return None
    return text[:last_safe_idx] + "]}"


def _call_model(topic, condensed, num_ctx, num_predict):
    prompt = build_prompt(topic, condensed)
    print(f"Sending {len(condensed)} sources to {MODEL} for structuring...")
    print(f"(prompt is {len(prompt)} characters, roughly {len(prompt)//4} tokens; "
          f"num_ctx={num_ctx}, num_predict={num_predict})")

    try:
        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            think=False,  # qwen3.5 is a "thinking" model -- without this, it can
                          # burn its whole token budget on internal reasoning and
                          # never actually write the JSON answer
            options={"num_ctx": num_ctx, "num_predict": num_predict},
        )
    except TypeError:
        # Installed ollama client is too old to support the think= argument --
        # fall back to calling without it.
        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"num_ctx": num_ctx, "num_predict": num_predict},
        )

    content = response["message"].get("content", "")
    if not content.strip():
        # Diagnostic: if the model still produced nothing, check whether it
        # dumped everything into a separate "thinking" field instead.
        thinking = response["message"].get("thinking", "")
        if thinking.strip():
            print(f"  [diagnostic] content was empty, but found {len(thinking)} "
                  f"chars in a 'thinking' field -- the model is reasoning but not "
                  f"producing a final answer within num_predict={num_predict}.")
    return content


def structure_content(topic, results):
    condensed = condense_sources(results)
    raw = _call_model(topic, condensed, NUM_CTX, NUM_PREDICT)

    if not raw or not raw.strip():
        # Empty response -- most likely a resource/memory issue with the
        # requested context size. Retry once with a much smaller prompt
        # and lower context demand before giving up.
        print("\n[!] Empty response from the model. Retrying with a smaller "
              "prompt and lower context size...\n")
        smaller = condensed[:3]  # cut to 3 sources
        raw = _call_model(topic, smaller, num_ctx=2048, num_predict=1200)

        if not raw or not raw.strip():
            raise RuntimeError(
                "Model returned an empty response twice in a row, even with a "
                "much smaller prompt. This points to a local resource problem "
                "(not enough free RAM/VRAM for this model) rather than the "
                "prompt size. Try closing other applications, or try a smaller "
                "model (e.g. 'ollama pull qwen2.5:3b') and update MODEL in "
                "structure.py."
            )

    cleaned = clean_json_response(raw)

    # Attempt 1: parse as-is
    try:
        outline = json.loads(cleaned)
        if outline.get("slides"):
            return outline
    except json.JSONDecodeError:
        pass

    # Attempt 2: json_repair -- handles missing commas, trailing commas,
    # unquoted keys, and most small-model JSON mistakes automatically
    try:
        repaired = repair_json(cleaned)
        outline = json.loads(repaired)
        if outline.get("slides"):
            n = len(outline["slides"])
            print(f"\n[!] Model's JSON had formatting errors (e.g. missing commas) -- "
                  f"auto-repaired successfully, recovered {n} slide(s).")
            return outline
    except (json.JSONDecodeError, Exception):
        pass

    # Attempt 3: salvage whatever complete slides exist before a truncation point
    salvaged = salvage_truncated_json(cleaned)
    if salvaged:
        try:
            outline = json.loads(salvaged)
            if outline.get("slides"):
                n = len(outline["slides"])
                print(f"\n[!] Response was truncated -- recovered {n} complete slide(s) "
                      f"before the cutoff point.")
                return outline
        except json.JSONDecodeError:
            pass

    print(f"\n[!] Model did not return usable JSON, and nothing could be salvaged. "
          f"Raw output was ({len(raw)} chars):\n")
    print(raw)
    raise ValueError("Could not parse or repair the model's JSON output.")


def save_outline(outline, topic, out_dir="output"):
    os.makedirs(out_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in topic).strip().replace(" ", "_").lower()
    path = os.path.join(out_dir, f"outline_{safe_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(outline, f, indent=2, ensure_ascii=False)
    print(f"\nSaved outline to {path}")
    return path


if __name__ == "__main__":
    # Point this at whatever research JSON Step 1 saved
    research_path = sys.argv[1] if len(sys.argv) > 1 else "output/research_generative_ai_impact_on_business.json"

    topic, results = load_research(research_path)
    outline = structure_content(topic, results)

    print("\n" + "=" * 70)
    print(f"TOPIC: {outline.get('topic')}")
    for i, slide in enumerate(outline.get("slides", []), 1):
        print(f"\n[Slide {i}] {slide['title']} ({slide['type']})")
        for b in slide.get("bullets", []):
            print(f"  - {b}")
        if slide.get("chart"):
            c = slide["chart"]
            print(f"  CHART ({c['chart_type']}): {c['labels']} -> {c['values']} [{c.get('unit','')}]")
        print(f"  Sources: {slide.get('sources')}")

    save_outline(outline, topic)
