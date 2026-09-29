import os
import re
from datetime import datetime, timezone
from pathlib import Path
import requests

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
API_KEY = os.environ["OPENAI_API_KEY"]
CATEGORY = "Movie Updates"

def slugify(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:90] or "latest-movie-update"

def main():
    prompt = '''Create ONE fresh, verified Telugu cinema news article based on web research performed now. Focus on today or the last 24 hours. Cover official movie announcements, posters, teasers, trailers, release dates, shooting updates, OTT announcements, actor/director updates, or verified box-office developments. Use official sources and reputable Indian entertainment sources. Do not invent facts, quotes, dates or collections. Do not present rumors as facts. Write original simple English, 700-1100 words, with an H1, useful headings, 3 FAQs, and a Sources section containing the URLs used. Return only the Markdown article.'''
    payload = {"model": MODEL, "tools": [{"type": "web_search", "search_context_size": "medium"}], "input": prompt}
    response = requests.post("https://api.openai.com/v1/responses", headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=180)
    response.raise_for_status()
    article = response.json().get("output_text", "").strip()
    if not article:
        raise RuntimeError("No article returned")
    title = next((x[2:].strip() for x in article.splitlines() if x.startswith("# ")), "Latest Telugu Movie Update")
    now = datetime.now(timezone.utc)
    folder = Path("Daily Blogs") / CATEGORY
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{now:%Y-%m-%d-%H%M}-{slugify(title)}.md"
    path.write_text(f"<!-- Generated: {now.isoformat()} -->\n<!-- Category: {CATEGORY} -->\n\n" + article + "\n", encoding="utf-8")
    print(f"Generated: {path}")

if __name__ == "__main__":
    main()
