import json
import re
import sys
from datetime import datetime
from typing import Any

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

CATEGORIES = {
    "copywriting": {
        "label": "文案生成 (Text-to-Text)",
        "query": "best LLM API for Chinese text generation latest model pricing 2026",
        "keywords": ["deepseek", "openai", "gpt", "claude", "qwen", "glm", "ernie", "moonshot"],
    },
    "image_gen": {
        "label": "图片生成 (Text-to-Image)",
        "query": "best text to image API latest model pricing 2026 stable diffusion",
        "keywords": ["stable diffusion", "dall-e", "midjourney", "flux", "sd3", "runway"],
    },
    "video_gen": {
        "label": "视频生成 (Image-to-Video)",
        "query": "best image to video generation API latest model pricing 2026",
        "keywords": ["runway", "luma", "pika", "kling", "sora", "veo", "seedance"],
    },
}


def search_web(query: str, max_results: int = 10) -> list[dict]:
    if DDGS is None:
        print("[!] duckduckgo-search not installed. Run: pip install duckduckgo-search")
        return []
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({"title": r["title"], "url": r["href"], "body": r["body"]})
    except Exception as e:
        print(f"[!] Search error: {e}")
    return results


def extract_model_info(results: list[dict], keywords: list[str]) -> list[dict]:
    models = []
    seen = set()

    for r in results:
        text = (r["title"] + " " + r["body"]).lower()
        matched = [kw for kw in keywords if kw in text]
        if not matched:
            continue

        prices = re.findall(r"\$?(\d+\.?\d*)\s*/\s*(?:1M|million|sec|second|image|video|张|秒)", text)
        versions = re.findall(
            r"(v\d+\.?\d*|GPT-?4[.]?\d*[a-z]*|Claude\s*\d+\.?\d*|"
            r"Gen-?\d+\.?\d*|SD\d+\.?\d*|Ray\d+\.?\d*|Flux\d*\.?\d*)",
            text, re.IGNORECASE,
        )

        model_id = matched[0].upper()
        if model_id in seen:
            continue
        seen.add(model_id)

        models.append({
            "name": model_id,
            "matched_keywords": matched,
            "versions": list(set(versions))[:3],
            "prices_found": prices[:3],
            "source_title": r["title"],
            "source_url": r["url"],
            "snippet": r["body"][:200],
        })

    return models


def scout_category(category: str) -> dict:
    if category not in CATEGORIES:
        return {"error": f"Unknown category: {category}. Available: {list(CATEGORIES.keys())}"}

    cfg = CATEGORIES[category]
    print(f"\n  Searching: {cfg['label']} ...")

    results = search_web(cfg["query"])
    if not results:
        return {"error": "No search results", "category": category}

    models = extract_model_info(results, cfg["keywords"])
    return {
        "category": category,
        "label": cfg["label"],
        "searched_at": datetime.now().isoformat(),
        "results_count": len(results),
        "models_found": models,
    }


def print_report(data: dict):
    if "error" in data:
        print(f"  [!] {data['error']}")
        return

    models = data.get("models_found", [])
    print(f"  Found {len(models)} candidate models:\n")

    if not models:
        print("  (no models matched — try broader keywords)\n")
        return

    for i, m in enumerate(models, 1):
        print(f"  ┌─ [{i}] {m['name']}")
        if m["versions"]:
            print(f"  │    Versions: {', '.join(m['versions'])}")
        if m["prices_found"]:
            print(f"  │    Prices: {', '.join('$'+p for p in m['prices_found'])}")
        print(f"  │    Source: {m['source_url']}")
        print(f"  │    {m['snippet'][:120]}...")
        print(f"  └─")

    print(f"\n  Recommendation based on {data['label']}:\n")
    best = models[0] if models else None
    if best:
        print(f"  >>> Top pick: {best['name']} — see {best['source_url']}")
        if len(models) > 1:
            print(f"  >>> Budget alt: {models[1]['name']} — see {models[1]['source_url']}")
    print()


def scout_all():
    print(f"\n{'='*55}")
    print(f"  API Scout — Real-time API Recommender")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")

    all_data = []
    for cat in CATEGORIES:
        data = scout_category(cat)
        print_report(data)
        all_data.append(data)

    return all_data
