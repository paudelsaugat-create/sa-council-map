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

# Match official SA Local Council naming patterns
COUNCIL_REGEX = re.compile(
    r"\b([A-Za-z\s]+(?:City Council|District Council|Regional Council|Rural City Council|Council)|"
    r"City of [A-Za-z\s]+|District Council of [A-Za-z\s]+|Town of [A-Za-z\s]+|Regional Council of [A-Za-z\s]+)\b",
    re.IGNORECASE,
)

# Loop across pagination ranks (1, 11, 21, ..., up to rank 251)
for rank in range(1, 260, 10):
    params = {
        "collection": "all-councils-employment-push",
        "current_page": "1332517",
        "fmo": "true",
        "meta_status": "live",
        "profile": "careers",
        "query": "!showall",
        "start_rank": str(rank),
    }

    req_url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    print(f"Scraping rank {rank}...")

    try:
        req = urllib.request.Request(req_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8")
    except Exception as e:
        print(f"Error loading rank {rank}: {e}")
        break

    soup = BeautifulSoup(html, "html.parser")

    # Find job links with external tab icon or job URLs
    links = soup.find_all("a", href=True)
    found_on_page = 0

    for a in links:
        href = a["href"].strip()
        raw_title = a.get_text(" ", strip=True)

        # Skip headers, footers, pagination controls
        if any(
            skip in raw_title.lower()
            for skip in [
                "next",
                "prev",
                "previous",
                "sort",
                "show",
                "career",
                "contact",
                "privacy",
            ]
        ):
            continue

        # Check if the link looks like a job title link
        if len(raw_title) < 5 or href.startswith("#"):
            continue

        # Look up the DOM tree to find the card boundary
        card = a.find_parent(["li", "article", "div", "section"])
        if not card:
            continue

        card_text = card.get_text("\n", strip=True)
        lines = [line.strip() for line in card_text.splitlines() if line.strip()]

        # The council name is typically the line immediately after the job title
        council_name = None

        # Method A: Exact line matching
        for i, line in enumerate(lines):
            clean_l = re.sub(r"-\s*opens in a new tab", "", line, flags=re.IGNORECASE).strip()
            if clean_l == raw_title and i + 1 < len(lines):
                next_line = lines[i + 1]
                if not any(k in next_line.lower() for k in ["category", "type", "closing date", "full time", "part time"]):
                    council_name = next_line
                    break

        # Method B: Regular expression search inside card text
        if not council_name:
            match = COUNCIL_REGEX.search(card_text)
            if match:
                council_name = match.group(1).strip()

        if council_name:
            # Clean up artifacts
            council_name = " ".join(council_name.split()).strip()
            title = re.sub(r"-\s*opens in a new tab", "", raw_title, flags=re.IGNORECASE).strip()
            job_url = href if href.startswith("http") else f"https://www.localcouncils.sa.gov.au{href}"

            if council_name not in vacancies_by_council:
                vacancies_by_council[council_name] = []

            # Avoid duplicates
            if not any(j["url"] == job_url or j["title"] == title for j in vacancies_by_council[council_name]):
                vacancies_by_council[council_name].append({
                    "title": title,
                    "url": job_url
                })
                found_on_page += 1

    # Stop pagination when a page produces no new listings
    if found_on_page == 0:
        print(f"No additional listings found at rank {rank}. Stopping.")
        break

# Write out collected vacancies
with open("sa_vacancies.json", "w", encoding="utf-8") as f:
    json.dump(vacancies_by_council, f, indent=2, ensure_ascii=False)

total = sum(len(v) for v in vacancies_by_council.values())
print(f"Success: Extracted {total} vacancies across {len(vacancies_by_council)} councils.")
