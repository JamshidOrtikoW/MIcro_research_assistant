from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)


def fetch_wikipedia_text(topic):
    search_api = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": topic,
        "format": "json"
    }
    headers = {
        "User-Agent": "MicroResearchAssistant/1.0 (contact: youremail@example.com)"
    }

    try:
        res = requests.get(search_api, params=params, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
    except (requests.RequestException, ValueError) as e:
        print("Error fetching Wikipedia:", e)
        return None

    search_results = data.get("query", {}).get("search")
    if not search_results:
        return None

    page_title = search_results[0]["title"].replace(" ", "_")
    page_url = f"https://en.wikipedia.org/wiki/{page_title}"

    try:
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print("Error fetching Wikipedia page:", e)
        return None

    soup = BeautifulSoup(response.text, "lxml")
    paragraphs = soup.find_all("p")
    text = "".join([p.get_text() for p in paragraphs[:5]])
    return text.strip()

def summarize_text(text, sentences_count=5):
    sentences = re.split(r'(?<=[.!?]) +', text)
    return sentences[:sentences_count] if sentences else [text]
def extract_keywords(text, limit=7):
    words = re.findall(r'\w+', text.lower())
    freq = {}
    for w in words:
        if len(w) > 5:
            freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w[0] for w in ranked[:limit]]

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    topic = request.form.get("topic", "").strip()
    if not topic:
        return render_template("results.html", topic=topic, error=True)

    text = fetch_wikipedia_text(topic)
    if not text:
        return render_template("results.html", topic=topic, error=True)

    summary = summarize_text(text)
    keywords = extract_keywords(text)

    return render_template("results.html",
                           topic=topic,
                           summary=summary,
                           keywords=keywords,
                           error=False)

if __name__ == "__main__":
    app.run(debug=True)
