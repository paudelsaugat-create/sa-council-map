import json
import re
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup

BASE_URL = "https://www.localcouncils.sa.gov.au/careers/job-search"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

vacancies_by_council = {}

# Match SA council designations
COUNCIL_REGEX = re.compile(
    r"\b(City of [A-Za-z\s]+|District Council of [A-Za-z\s]+|Town of [A-Za-z\s]+|"
    r"Regional Council of [A-Za-z\s]+|Rural City of [A-Za-z\s]+|[A-Za-z\s]+ City Council|"
    r"[A-Za-z\s]+ Regional Council|[A-Za-z\s]+ District Council|[A-Za-z\s]+ Council)\b",
    re.IGNORECASE,
)

# Traverse pages 1 through 10 (ranks 1, 11, 21, ..., 91)
for rank in range(1, 120, 10):
    params = {
        "collection": "all-councils-employment-push",
        "current_page": "1332517",
        "fmo": "true",
        "meta_status": "live",
        "profile": "careers",
        "query": "!showall",
        "start_rank": str(rank),
    }

    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    print(f"Fetching listings at rank {rank}...")

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=25) as resp:
            html = resp.read().decode("utf-8")
    except Exception as e:
        print(f"Failed to fetch rank {rank}: {e}")
        break

    soup = BeautifulSoup(html, "html.parser")
    found_on_page = 0

    # Locate links with the 'opens in a new tab' marker or external career redirects
    for a in soup.find_all("a", href=True):
        raw_text = a.get_text(" ", strip=True)

        if "opens in a new tab" not in raw_text.lower():
            continue

        clean_title = re.sub(
            r"-\s*opens in a new tab.*", "", raw_text, flags=re.IGNORECASE
        ).strip()
        if len(clean_title) < 3:
            continue

        job_url = a["href"].strip()
        if not job_url.startswith("http"):
            job_url = f"https://www.localcouncils.sa.gov.au{job_url}"

        # Locate the parent job card
        card = a.find_parent(["li", "article", "div", "section"])
        if not card:
            continue

        lines = [l.strip() for l in card.get_text("\n", strip=True).splitlines() if l.strip()]
        council_name = None

        # The council name appears on the text line immediately below the title
        for idx, line in enumerate(lines):
            clean_l = re.sub(
                r"-\s*opens in a new tab.*", "", line, flags=re.IGNORECASE
            ).strip()
            if clean_l == clean_title and idx + 1 < len(lines):
                candidate = lines[idx + 1]
                if not any(
                    w in candidate.lower()
                    for w in ["category", "type", "closing date", "full time", "part time"]
                ):
                    council_name = candidate
                    break

        if not council_name:
            match = COUNCIL_REGEX.search(card.get_text(" ", strip=True))
            if match:
                council_name = match.group(1).strip()

        if council_name:
            council_name = " ".join(council_name.split()).strip()

            if council_name not in vacancies_by_council:
                vacancies_by_council[council_name] = []

            if not any(j["title"] == clean_title for j in vacancies_by_council[council_name]):
                vacancies_by_council[council_name].append(
                    {"title": clean_title, "url": job_url}
                )
                found_on_page += 1

    if found_on_page == 0:
        print(f"End of job results reached at rank {rank}.")
        break

# Write out populated JSON
with open("sa_vacancies.json", "w", encoding="utf-8") as f:
    json.dump(vacancies_by_council, f, indent=2, ensure_ascii=False)

total = sum(len(jobs) for jobs in vacancies_by_council.values())
print(f"Extraction complete: Saved {total} vacancies across {len(vacancies_by_council)} councils.")
