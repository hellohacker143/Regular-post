import os
import re
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
API_KEY = os.environ["OPENAI_API_KEY"]

CATEGORIES = [
    "Movie Updates",
    "News Updates",
    "Google Updates",
    "Tech News",
    "Trending News",
    "OTT Updates",
    "Box Office Updates",
]

PROMPTS = {
    "Movie Updates": "latest Telugu cinema and Indian movie announcements, trailers, teasers, release updates and official movie news",
    "News Updates": "important current India news and major world news that is useful to general readers",
    "Google Updates": "latest official Google products, Search, Android, YouTube, Gemini, Chrome and other Google announcements",
    "Tech News": "latest technology, AI, smartphones, apps, software and cybersecurity developments",
    "Trending News": "important topics currently trending in India on the web and social platforms, using verified reporting only",
    "OTT Updates": "latest OTT releases, streaming announcements, platform updates and movie/series availability",
    "Box Office Updates": "latest verified Indian movie box-office collections, openings, milestones and official trade/industry updates",
}

def safe_slug(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:90] or "latest-update"

def choose_category():
    # Rotate through all 7 categories based on the current UTC hour.
    hour = datetime.now(timezone.utc).hour
    return CATEGORIES[hour % len(CATEGORIES)]

def call_openai(category, topic):
    prompt = f"""
You are the automated editor for a factual SEO blog.

CATEGORY: {category}
RESEARCH TOPIC: {topic}

Create ONE genuinely current article based on web research performed now.
Rules:
- Use the web search tool before writing.
- Prefer official sources and reputable news organizations.
- Do not invent facts, quotes, dates, prices, collections, release dates or claims.
- Do not present rumors or speculation as facts.
- For political/news subjects, remain neutral and factual; do not persuade readers.
- Avoid topics that have no meaningful current update.
- Do not copy source text. Summarize in original wording.
- Write in simple English.
- Aim for 700-1100 words.
- Include a short FAQ with 3 questions.
- Include a Sources section with the source URLs used.
- Return ONLY the complete Markdown article, beginning with an H1 title.
- Do not include JSON, code fences, or commentary about being an AI.
"""
    payload = {
        "model": MODEL,
        "tools": [{"type": "web_search", "search_context_size": "medium"}],
        "input": prompt,
    }
    r = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=180,
    )
    r.raise_for_status()
    data = r.json()
    text = data.get("output_text", "").strip()
    if not text:
        raise RuntimeError("OpenAI returned no article text.")
    return text

def extract_title(markdown):
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Latest Update"

def main():
    category = choose_category()
    topic = PROMPTS[category]
    article = call_openai(category, topic)
    title = extract_title(article)

    now = datetime.now(timezone.utc)
    filename = f"{now.strftime('%Y-%m-%d-%H%M')}-{safe_slug(title)}.md"
    directory = Path("Daily Blogs") / category
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename

    metadata = (
        f"<!-- Generated: {now.isoformat()} -->\n"
        f"<!-- Category: {category} -->\n\n"
    )
    path.write_text(metadata + article + "\n", encoding="utf-8")

    print(json.dumps({
        "category": category,
        "title": title,
        "file": str(path),
    }))

if __name__ == "__main__":
    main()
