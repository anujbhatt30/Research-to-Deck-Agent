"""
Step 1: Web research module.

Given a topic, runs several targeted searches (not just one -- a single
query gives a shallow, one-angle view), fetches the full text of each
result, and returns everything WITH its source URL attached -- since the
whole point of this agent is that every slide can cite where its numbers
came from.

No API key needed: uses DuckDuckGo search (free) + trafilatura for
clean article text extraction.
"""

import time
import json
import os
import requests
from ddgs import DDGS
import trafilatura

HEADERS = {"User-Agent": "Mozilla/5.0 (research agent; educational project)"}


AD_URL_PATTERNS = ("bing.com/aclick", "doubleclick.net", "googleadservices.com", "/aclk?")


def is_ad_url(url):
    return any(p in url for p in AD_URL_PATTERNS)


def search_web(query, max_results=5):
    """Run a single search query, return list of {title, url, snippet}."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            url = r.get("href", "")
            if is_ad_url(url):
                continue  # skip sponsored/tracking links, not real content
            results.append({
                "title": r.get("title", ""),
                "url": url,
                "snippet": r.get("body", ""),
            })
    return results


def fetch_full_text(url, timeout=10):
    """Download a page and extract its main article text (no ads/nav junk)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        text = trafilatura.extract(resp.text, include_comments=False, include_tables=True)
        return text
    except Exception as e:
        print(f"  [!] Could not fetch {url}: {e}")
        return None


def research_topic(topic, queries=None, max_results_per_query=5, fetch_full=True):
    """
    Run multiple queries on a topic and return deduplicated, sourced results.

    queries: optional list of search queries. If not given, generates a
    default spread of angles (overview, stats, industry impact, recent news).
    """
    if queries is None:
        queries = [
            f"{topic} overview",
            f"{topic} statistics data",
            f"{topic} industry impact",
            f"{topic} latest news",
        ]

    seen_urls = set()
    all_results = []

    for q in queries:
        print(f"Searching: {q}")
        try:
            hits = search_web(q, max_results=max_results_per_query)
        except Exception as e:
            print(f"  [!] Search failed for '{q}': {e}")
            continue

        for hit in hits:
            url = hit["url"]
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            entry = {
                "query": q,
                "title": hit["title"],
                "url": url,
                "snippet": hit["snippet"],
                "content": None,
            }

            if fetch_full:
                print(f"  Fetching: {url}")
                entry["content"] = fetch_full_text(url)
                time.sleep(0.5)  # be polite to servers

            all_results.append(entry)

    print(f"\nCollected {len(all_results)} unique sources across {len(queries)} queries.")
    return all_results


def save_results(results, topic, out_dir="output"):
    os.makedirs(out_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in topic).strip().replace(" ", "_").lower()
    path = os.path.join(out_dir, f"research_{safe_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"topic": topic, "results": results}, f, indent=2, ensure_ascii=False)
    print(f"\nSaved research to {path}")
    return path


if __name__ == "__main__":
    topic = "Generative AI impact on business"
    results = research_topic(topic, max_results_per_query=3)

    print("\n" + "=" * 70)
    for r in results:
        print(f"\n[{r['query']}]")
        print(f"  {r['title']}")
        print(f"  {r['url']}")
        has_content = "yes" if r["content"] else "no (snippet only)"
        print(f"  Full text extracted: {has_content}")
        print(f"  Snippet: {r['snippet'][:150]}...")

    save_results(results, topic)
