import json
import re
import urllib.request
from bs4 import BeautifulSoup

URL = "https://www.localcouncils.sa.gov.au/careers/job-search"
req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})

try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")
except Exception as e:
    print(f"Error fetching URL: {e}")
    html = ""

soup = BeautifulSoup(html, "html.parser")
vacancies = {}

# Locate listing cards
for item in soup.select("article, li, .item, .job-item, tr"):
    title_el = item.select_one("h2 a, h3 a, h4 a, a[href*='job']")
    if not title_el:
        continue

    title = title_el.get_text(strip=True)
    href = title_el.get("href", "")
    link = href if href.startswith("http") else f"https://www.localcouncils.sa.gov.au{href}"

    # Extract council name
    text = item.get_text(" ", strip=True)
    match = re.search(
        r"(City of [A-Za-z\s]+|District Council of [A-Za-z\s]+|Town of [A-Za-z\s]+|Regional Council of [A-Za-z\s]+|[A-Za-z\s]+ City Council|[A-Za-z\s]+ Council)",
        text,
        re.IGNORECASE,
    )
    if match and len(title) > 3:
        council = " ".join(match.group(1).split()).title()
        if council not in vacancies:
            vacancies[council] = []
        if not any(j["url"] == link for j in vacancies[council]):
            vacancies[council].append({"title": title, "url": link})

with open("sa_vacancies.json", "w", encoding="utf-8") as f:
    json.dump(vacancies, f, indent=2)

print(f"Saved vacancies for {len(vacancies)} councils.")
