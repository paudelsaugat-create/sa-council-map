import json
import re
import urllib.request
from bs4 import BeautifulSoup

URL = "https://www.localcouncils.sa.gov.au/careers/job-search"
req = urllib.request.Request(
    URL,
    headers={
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    },
)

try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")
except Exception as e:
    print(f"Error fetching URL: {e}")
    html = ""

soup = BeautifulSoup(html, "html.parser")
vacancies = {}

# Match official SA Local Council naming patterns
COUNCIL_REGEX = re.compile(
    r"\b(City of [A-Za-z\s]+|District Council of [A-Za-z\s]+|Town of [A-Za-z\s]+|"
    r"Regional Council of [A-Za-z\s]+|Rural City of [A-Za-z\s]+|[A-Za-z\s]+ City Council|"
    r"[A-Za-z\s]+ Regional Council|[A-Za-z\s]+ District Council|[A-Za-z\s]+ Council)\b",
    re.IGNORECASE,
)

# Look through all links pointing to careers/job details or external ATS portals
for a in soup.find_all("a", href=True):
    href = a["href"].strip()
    raw_title = a.get_text(" ", strip=True)

    # Clean the title text
    title = re.sub(r"-\s*opens in a new tab", "", raw_title, flags=re.IGNORECASE).strip()

    # Skip site header navigation or trivial link anchors
    if len(title) < 4 or any(
        skip in title.lower()
        for skip in [
            "job search",
            "career pathways",
            "graduate programs",
            "apprenticeships",
            "volunteering",
            "benefits",
            "find your council",
        ]
    ):
        continue

    # Identify the job card container
    parent = a.find_parent(["li", "article", "tr", "div"])
    if not parent:
        continue

    parent_text = parent.get_text(" ", strip=True)

    # Extract council name from the enclosing card block
    match = COUNCIL_REGEX.search(parent_text)
    if match:
        council_name = " ".join(match.group(1).split()).strip()

        # Ignore accidental menu item catches
        if council_name.lower() in ["find your council", "careers in council"]:
            continue

        full_url = href if href.startswith("http") else f"https://www.localcouncils.sa.gov.au{href}"

        if council_name not in vacancies:
            vacancies[council_name] = []

        if not any(j["title"] == title for j in vacancies[council_name]):
            vacancies[council_name].append({"title": title, "url": full_url})

# Save output
with open("sa_vacancies.json", "w", encoding="utf-8") as f:
    json.dump(vacancies, f, indent=2, ensure_ascii=False)

total_jobs = sum(len(j) for j in vacancies.values())
print(f"Scraped {total_jobs} active vacancies across {len(vacancies)} councils.")
